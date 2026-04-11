from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response


from apartments.models import Booking, BookingSlot, Schedule, User
from apartments.api.serializers import BookingSerializer

from apartments.api.serializers import CreateBookingSerializer, StartPaymentSerializer, PaymentResultSerializer

import logging

logger = logging.getLogger("apartments")



class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        POST /api/v1/booking/
        """
        try:
            logger.info(f"BookingViewSet.create - quest reservation")
            serializer = CreateBookingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            apt_id = data['apartment_id']
            start_date = data['start_date']
            end_date = data['end_date']
            actual_end_date = data['end_date'] - timedelta(days=1) # -1 день для дня выезда
            nights_needed = (data['end_date'] - data['start_date']).days

            #Транзакция и блокировка
            with transaction.atomic():
                schedule = Schedule.objects.select_for_update().filter(
                    apartment_id=apt_id,
                    date__range=[start_date, actual_end_date],
                    status = Schedule.Status.AVAILABLE,
                )

                if schedule.count() != nights_needed:
                    logger.warning(f"Not enough available nights for apartment {apt_id} in the given date range.")
                    return Response({"error": "Not enough available nights for the selected apartment in the given date range."},
                                    status=status.HTTP_400_BAD_REQUEST)

                total_price = schedule.aggregate(
                    total=Sum('price__price'))['total'] or 0

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
                            price_snapshot = day.price.price
                        )
                    )

                BookingSlot.objects.bulk_create(slots_to_create)
                logger.info(f"Booking created successfully with ID {booking.id} for apartment {apt_id} from {start_date} to {data['end_date']} with total price {total_price}.")


                return Response({
                    "message": "Booking created successfully",
                    "booking_id": booking.id,
                    "total_price": total_price,
                    "reserved_until": reserved_until.isoformat(),
                    "status": "pending",
                }
                    ,status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Unexpected error in BookingViewSet.create")
            raise


    @action(detail=True, methods=["post"])
    def start_payment(self, request, pk=None):
        """
        POST /api/v1/booking/{booking_id}/start_payment/

        Скрытая регистрация: получение емейла и создание учетки.

        так-же тут вызывается платежка (на период разработки заглушка)

        """
        booking = self.get_object()

        with transaction.atomic():
            if booking.status != Booking.Status.PENDING:
                return Response({"error": "Booking is not in pending status"},
                                status=status.HTTP_400_BAD_REQUEST)

            if booking.status == Booking.Status.EXPIRED:
                return Response({"error": "Booking has already expired"},
                                status=status.HTTP_400_BAD_REQUEST)

            payload = StartPaymentSerializer(data=request.data)
            payload.is_valid(raise_exception=True)
            data = payload.validated_data

            # Авто-регистрация
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={'username': data["email"],
                          'first_name': data.get("first_name", ""),
                          'last_name': data.get("last_name", ""),
                          },
            )
            if created:
                user.set_unusable_password()
                user.save()
                logger.info(f"Created user with email {user.email}")

            booking.user = user
            booking.email = data["email"]
            booking.save(update_fields=["user", "email"])

            #Заглушка платежки
            payment_url = f"/api/v1/booking/{booking.id}/payment"

        return Response({
            "message": "Payment has been started",
            "payment_url": payment_url,
            "booking_id": booking.id,
            "status": booking.status,
            "reserved_until": booking.reserved_until.isoformat() if booking.reserved_until else None,
        },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def payment_result(self, request, pk=None):
        """
        Заглушка webhook от платежки.
        body: {"result": "success"} | {"result": "failed"}
        """

        booking = self.get_object()
        payload = PaymentResultSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        result = payload.validated_data["result"]

        with transaction.atomic():
            if booking.status != Booking.Status.PENDING:
                return Response({"error": "Booking is not in pending status"},
                                status=status.HTTP_400_BAD_REQUEST)

            if booking.status == Booking.Status.EXPIRED:
                return Response({"error": "Booking has already expired"},
                                status=status.HTTP_400_BAD_REQUEST)
            if result == "success":
                booking.status = Booking.Status.CONFIRMED
                booking.paid = True
                booking.save(update_fields=["status", "paid"])

                slots = BookingSlot.objects.select_related("schedule").filter(booking=booking)
                for slot in slots:
                    slot.schedule.status = Schedule.Status.BOOKED
                    slot.schedule.save(update_fields=["status"])

                return Response({
                    "message": "Payment successful",
                    "booking_id": booking.id,
                    "status": booking.status,
                },
                    status=status.HTTP_200_OK)

            booking.status = Booking.Status.CANCELED #(или оставить PENDING?)
            booking.paid = False
            booking.save(update_fields=["status", "paid"])

            slots = BookingSlot.objects.select_related("schedule").filter(booking=booking)
            for slot in slots:
                slot.schedule.status = Schedule.Status.AVAILABLE
                slot.schedule.save(update_fields=["status"])

            return Response({
                "message": "Payment failed",
                "booking_id": booking.id,
                "status": booking.status,
            },
                status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel_payment(self, request, pk=None):
        """
        POST /api/v1/booking/{booking_id}/cancel_payment/

        Отмена брони пользователем (до оплаты)
        """
        booking = self.get_object()

        with transaction.atomic():
            if booking.status != Booking.Status.PENDING:
                return Response({"error": "Booking is not in pending status"},
                                status=status.HTTP_400_BAD_REQUEST)

            if booking.status == Booking.Status.EXPIRED:
                return Response({"error": "Booking has already expired"},
                                status=status.HTTP_400_BAD_REQUEST)

            booking.status = Booking.Status.CANCELED
            booking.paid = False
            booking.save(update_fields=["status", "paid"])

            slots = BookingSlot.objects.select_related("schedule").filter(booking=booking)
            for slot in slots:
                slot.schedule.status = Schedule.Status.AVAILABLE
                slot.schedule.save(update_fields=["status"])

            return Response({
                "message": "Booking has been canceled",
                "booking_id": booking.id,
                "status": booking.status,
            },
                status=status.HTTP_200_OK)