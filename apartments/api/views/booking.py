from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


from apartments.models import Booking, BookingSlot, Schedule, User
from apartments.api.serializers import BookingSerializer
from apartments.services import apply_booking_status_transition

from apartments.api.serializers import (
    CreateBookingSerializer,
    StartPaymentSerializer,
    PaymentResultSerializer,
)

import logging

logger = logging.getLogger("apartments")


class BookingViewSet(viewsets.GenericViewSet):
    """
    EN:
    Booking API focused on reservation and payment lifecycle actions.

    Allowed flow:
    - POST /bookings/ -> create provisional booking
    - POST /bookings/{id}/start_payment/
    - POST /bookings/{id}/payment_result/
    - POST /bookings/{id}/cancel_payment/

    RU:
    API бронирований, ориентированный на сценарий резерва и оплаты.

    Разрешенный поток:
    - POST /bookings/ -> создать предварительную бронь
    - POST /bookings/{id}/start_payment/
    - POST /bookings/{id}/payment_result/
    - POST /bookings/{id}/cancel_payment/
    """

    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.AllowAny]
    # Keep only POST-based business actions; block default GET/PUT/PATCH/DELETE CRUD.
    http_method_names = ["post", "head", "options"]

    def create(self, request, *args, **kwargs):
        """
        EN:
        Create a provisional booking by locking all requested available schedule
        slots inside a single DB transaction.

        Endpoint:
        POST /api/v1/bookings/

        RU:
        Создает предварительную бронь, блокируя все доступные слоты расписания
        на запрошенный период в рамках одной транзакции БД.

        Эндпоинт:
        POST /api/v1/bookings/
        """
        try:
            logger.info(f"BookingViewSet.create - quest reservation")
            serializer = CreateBookingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            apt_id = data["apartment_id"]
            start_date = data["start_date"]
            end_date = data["end_date"]
            nights_needed = (end_date - start_date).days

            # Транзакция и блокировка
            with transaction.atomic():
                schedule = Schedule.objects.select_for_update().filter(
                    apartment_id=apt_id,
                    # Checkout day is excluded, so same-day turnover is allowed.
                    date__gte=start_date,
                    date__lt=end_date,
                    status=Schedule.Status.AVAILABLE,
                )

                if schedule.count() != nights_needed:
                    logger.warning(
                        f"Not enough available nights for apartment {apt_id} in the given date range."
                    )
                    return Response(
                        {
                            "error": "Not enough available nights for the selected apartment in the given date range."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                total_price = (
                    schedule.aggregate(total=Sum("price__price"))["total"] or 0
                )

                reserved_until = timezone.now() + timedelta(minutes=15)

                booking = Booking.objects.create(
                    user=None,
                    email=None,
                    total_price=total_price,
                    reserved_until=reserved_until,
                    status=Booking.Status.PENDING,
                    paid=False,
                )

                slots_to_create = []
                for day in schedule:
                    day.status = Schedule.Status.RESERVED
                    day.save()
                    slots_to_create.append(
                        BookingSlot(
                            booking=booking,
                            schedule=day,
                            price_snapshot=day.price.price,
                        )
                    )

                BookingSlot.objects.bulk_create(slots_to_create)
                logger.info(
                    f"Booking created successfully with ID {booking.id} for apartment {apt_id} from {start_date} to {data['end_date']} with total price {total_price}."
                )

                return Response(
                    {
                        "message": "Booking created successfully",
                        "booking_id": booking.id,
                        "total_price": total_price,
                        "reserved_until": reserved_until.isoformat(),
                        "status": "pending",
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            logger.exception("Unexpected error in BookingViewSet.create")
            raise

    @action(detail=True, methods=["post"])
    def start_payment(self, request, pk=None):
        """
        EN:
        Start payment flow for an existing pending booking.
        Also performs lightweight user binding by email (guest to user mapping).

        Endpoint:
        POST /api/v1/bookings/{booking_id}/start_payment/

        RU:
        Запускает оплату для существующей брони в статусе pending.
        Дополнительно выполняет привязку пользователя по email
        (гостевой сценарий -> пользователь).

        Эндпоинт:
        POST /api/v1/bookings/{booking_id}/start_payment/

        """
        booking = self.get_object()

        with transaction.atomic():
            if booking.status != Booking.Status.PENDING:
                return Response(
                    {"error": "Booking is not in pending status"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking.status == Booking.Status.EXPIRED:
                return Response(
                    {"error": "Booking has already expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payload = StartPaymentSerializer(
                data=request.data, context={"request": request}
            )
            payload.is_valid(raise_exception=True)
            data = payload.validated_data

            if request.user.is_authenticated:
                user = request.user
            else:
                user = User.objects.filter(email=data["email"]).first()

                if user:
                    if user.has_usable_password() and not user.check_password(
                        data["password"]
                    ):
                        return Response(
                            {"error": "Invalid email or password"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if not user.has_usable_password():
                        user.set_password(data["password"])
                else:
                    user = User(
                        email=data["email"],
                        username=data["email"],
                    )
                    user.set_password(data["password"])
                    logger.info(f"Created user with email {user.email}")

                user.first_name = data.get("first_name", user.first_name)
                user.last_name = data.get("last_name", user.last_name)
                user.save()

            booking.user = user
            booking.email = user.email
            booking.save(update_fields=["user", "email"])

            refresh = RefreshToken.for_user(user)

            # Stub payment entrypoint for manual success/failure confirmation.
            payment_url = f"/api/v1/bookings/{booking.id}/payment_result/"

        return Response(
            {
                "message": "Payment has been started",
                "payment_url": payment_url,
                "booking_id": booking.id,
                "status": booking.status,
                "reserved_until": (
                    booking.reserved_until.isoformat()
                    if booking.reserved_until
                    else None
                ),
                "auth": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def payment_result(self, request, pk=None):
        """
        EN:
        Stub endpoint for payment gateway webhook callback.
        Body: {"result": "success"} | {"result": "failed"}

        On success, booking becomes CONFIRMED and schedule slots become BOOKED.
        On failure, booking is CANCELED and schedule slots are released to AVAILABLE.

        RU:
        Заглушка callback/webhook от платежного провайдера.
        Тело: {"result": "success"} | {"result": "failed"}

        При успехе бронь переходит в CONFIRMED, слоты становятся BOOKED.
        При неуспехе бронь переходит в CANCELED, слоты освобождаются в AVAILABLE.
        """

        booking = self.get_object()
        payload = PaymentResultSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        result = payload.validated_data["result"]

        with transaction.atomic():
            if booking.status != Booking.Status.PENDING:
                return Response(
                    {"error": "Booking is not in pending status"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking.status == Booking.Status.EXPIRED:
                return Response(
                    {"error": "Booking has already expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if result == "success":
                apply_booking_status_transition(
                    booking=booking,
                    target_status=Booking.Status.CONFIRMED,
                )

                return Response(
                    {
                        "message": "Payment successful",
                        "booking_id": booking.id,
                        "status": booking.status,
                    },
                    status=status.HTTP_200_OK,
                )

            apply_booking_status_transition(
                booking=booking,
                target_status=Booking.Status.CANCELED,
            )

            return Response(
                {
                    "message": "Payment failed",
                    "booking_id": booking.id,
                    "status": booking.status,
                },
                status=status.HTTP_200_OK,
            )

    @action(detail=True, methods=["post"])
    def cancel_payment(self, request, pk=None):
        """
        EN:
        Cancel pending booking before payment confirmation and release reserved slots.

        Endpoint:
        POST /api/v1/bookings/{booking_id}/cancel_payment/

        RU:
        Отменяет pending-бронь до подтверждения оплаты и освобождает
        зарезервированные слоты.

        Эндпоинт:
        POST /api/v1/bookings/{booking_id}/cancel_payment/
        """
        booking = self.get_object()

        with transaction.atomic():
            if booking.status != Booking.Status.PENDING:
                return Response(
                    {"error": "Booking is not in pending status"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking.status == Booking.Status.EXPIRED:
                return Response(
                    {"error": "Booking has already expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            apply_booking_status_transition(
                booking=booking,
                target_status=Booking.Status.CANCELED,
            )

            return Response(
                {
                    "message": "Booking has been canceled",
                    "booking_id": booking.id,
                    "status": booking.status,
                },
                status=status.HTTP_200_OK,
            )
