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
