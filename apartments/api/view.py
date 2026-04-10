from datetime import datetime, timedelta

from django.db.models import Count, Sum, Q
from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, views, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apartments.api.serializers import ApartmentSerializer, ScheduleSerializer, CreateBookingSerializer, \
    BookingSerializer, StartPaymentSerializer, PaymentResultSerializer
from apartments.models import Apartment, Schedule, Booking, BookingSlot, User

# logger
import logging

logger = logging.getLogger("apartments")

class APIRootView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'apartments': '/api/apartments/',
            'schedules': '/api/schedules/',
            'auth_token': '/api/token/',
        }, status = status.HTTP_200_OK)

class ApartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Эндпоинт: /api/apartments/search/?start_date=2026-01-01&end_date=2026-01-20
        """
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        logger.debug("Apartment search requested: start_date=%s end_date=%s", start_date, end_date)

        try:
            if not start_date:
                logger.warning("Validation error: start_date is missing")
                return Response({"error": "start_date are required."},
                                status=status.HTTP_400_BAD_REQUEST)
            if not end_date:
                logger.debug("end_date is missing, using start_date as end_date")
                end_date = start_date
            try:
                logger.debug("Start date is %s", start_date)
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                logger.debug("End date is %s", end_date)
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            except:
                logger.warning("Validation error: invalid date format start=%s end=%s", start_date, end_date)
                return Response({"error": "start_date and end_date are not valid. Use YYYY-MM-DD format"},
                                status=status.HTTP_400_BAD_REQUEST)

            if end_date == start_date:
                end_date += timedelta(days=1)
                logger.debug("end_date is the same as start_date, adjusted end_date to %s", end_date)

            night_needed = (end_date - start_date).days
            actual_end_date = end_date - timedelta(days=1)
            logger.debug("Actual end date is %s", actual_end_date)

            if night_needed < 0:
                logger.warning("Validation error: night_needed is negative")
                return Response({"error": "night_needed must be greater than 0"},
                                status=status.HTTP_400_BAD_REQUEST)


            """
            Поиск в БД по фильтру: Квартира должна иметь статус AVAILABLE на все ночи в запрошенном диапазоне дат.
            """
            available_apartments = Apartment.objects.filter(
                schedule__date__range=[start_date, actual_end_date],
                schedule__status=Schedule.Status.AVAILABLE
            ).annotate(
                available_nights=Count('schedule', filter=Q(
                    schedule__status=Schedule.Status.AVAILABLE,
                    schedule__date__range=[start_date, actual_end_date]
                )),
                total_price=Sum('schedule__price__price', filter=Q(
                    schedule__status=Schedule.Status.AVAILABLE,
                    schedule__date__range=[start_date, actual_end_date]
                ))
            ).filter(
                available_nights=night_needed
            )
            serializer = self.get_serializer(available_apartments, many=True)

            logger.info(f"Found {len(available_apartments)} available apartments for the given date range.")
            return Response(serializer.data)
        except Exception as e:
            logger.exception("Unexpected error in ApartmentViewSet.search")
            raise


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Календарь для конкретной квартиры
        /api/schedules/?apartments_id=1
        """
        queryset = super().get_queryset()
        apartment_id = self.request.query_params.get('apartment_id')
        if apartment_id:
            queryset = queryset.filter(apartment_id=apartment_id)
        return queryset


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


