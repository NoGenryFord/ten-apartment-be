from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apartments.models import Booking, BookingSlot, Schedule


def apply_booking_status_transition(booking: Booking, target_status: str) -> Booking:
    """
    EN:
    Apply booking status transition and synchronize related schedule slots.

    Rules:
    - confirmed: booking.paid=True, RESERVED slots -> BOOKED
    - canceled/expired: booking.paid=False, RESERVED/BOOKED slots -> AVAILABLE

    RU:
    Применяет переход статуса бронирования и синхронизирует связанные слоты.

    Правила:
    - confirmed: booking.paid=True, RESERVED слоты -> BOOKED
    - canceled/expired: booking.paid=False, RESERVED/BOOKED слоты -> AVAILABLE
    """
    booking.status = target_status

    slot_schedule_ids = list(
        BookingSlot.objects.filter(booking=booking).values_list(
            "schedule_id", flat=True
        )
    )

    if target_status == Booking.Status.CONFIRMED:
        booking.paid = True
        booking.save(update_fields=["status", "paid"])

        Schedule.objects.filter(
            id__in=slot_schedule_ids,
            status=Schedule.Status.RESERVED,
        ).update(status=Schedule.Status.BOOKED)
        return booking

    if target_status in {Booking.Status.CANCELED, Booking.Status.EXPIRED}:
        booking.paid = False
        booking.save(update_fields=["status", "paid"])

        Schedule.objects.filter(
            id__in=slot_schedule_ids,
            status__in=[Schedule.Status.RESERVED, Schedule.Status.BOOKED],
        ).update(status=Schedule.Status.AVAILABLE)
        return booking

    booking.save(update_fields=["status"])
    return booking


def reconcile_reserved_schedules() -> dict[str, int]:
    """
    EN:
    Reconcile reservation consistency between Booking/BookingSlot and Schedule.

    Actions:
    - Mark overdue pending bookings as EXPIRED and release their slots.
    - For RESERVED schedules linked to CONFIRMED bookings, set status to BOOKED.
    - For RESERVED schedules that have no active pending booking, set to AVAILABLE.

    RU:
    Синхронизирует консистентность между Booking/BookingSlot и Schedule.

    Действия:
    - Переводит просроченные pending-букинги в EXPIRED и освобождает их слоты.
    - Для RESERVED слотов, связанных с CONFIRMED букингом, проставляет BOOKED.
    - Для RESERVED слотов без активного pending-букинга проставляет AVAILABLE.
    """
    now = timezone.now()

    with transaction.atomic():
        expired_bookings = Booking.objects.filter(
            status=Booking.Status.PENDING,
            reserved_until__lt=now,
        )

        expired_count = expired_bookings.count()
        if expired_count:
            for booking in expired_bookings.select_for_update():
                apply_booking_status_transition(
                    booking=booking,
                    target_status=Booking.Status.EXPIRED,
                )

        confirmed_schedule_ids = BookingSlot.objects.filter(
            booking__status=Booking.Status.CONFIRMED,
            schedule__status=Schedule.Status.RESERVED,
        ).values_list("schedule_id", flat=True)

        reserved_to_booked = Schedule.objects.filter(
            id__in=confirmed_schedule_ids,
            status=Schedule.Status.RESERVED,
        ).update(status=Schedule.Status.BOOKED)

        reserved_without_active_pending = (
            Schedule.objects.filter(status=Schedule.Status.RESERVED)
            .annotate(
                active_pending_bookings=Count(
                    "bookingslot",
                    filter=Q(
                        bookingslot__booking__status=Booking.Status.PENDING,
                        bookingslot__booking__reserved_until__gte=now,
                    ),
                    distinct=True,
                )
            )
            .filter(active_pending_bookings=0)
        )

        reserved_to_available = reserved_without_active_pending.update(
            status=Schedule.Status.AVAILABLE
        )

    return {
        "expired_bookings": expired_count,
        "reserved_to_booked": reserved_to_booked,
        "reserved_to_available": reserved_to_available,
    }
