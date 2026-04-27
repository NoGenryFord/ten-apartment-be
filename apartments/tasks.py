import logging

from celery import shared_task

from apartments.models import Booking
from apartments.services import (
    reconcile_reserved_schedules,
    send_booking_confirmation_email,
)

logger = logging.getLogger("apartments")


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def reconcile_reserved_schedules_task(self):
    """
    Periodic consistency task for booking/schedule statuses.
    """
    stats = reconcile_reserved_schedules()
    logger.info(
        "Reservation reconciliation finished: expired_bookings=%s, reserved_to_booked=%s, reserved_to_available=%s",
        stats["expired_bookings"],
        stats["reserved_to_booked"],
        stats["reserved_to_available"],
    )
    return stats


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    dont_autoretry_for=(ValueError,),
    retry_backoff=True,
    max_retries=3,
)
def send_booking_confirmation_email_task(self, booking_id: int):
    booking = Booking.objects.select_related("user").get(pk=booking_id)

    if booking.status != Booking.Status.CONFIRMED:
        logger.info(
            "Skip booking confirmation email for booking=%s because status=%s",
            booking.id,
            booking.status,
        )
        return {"booking_id": booking.id, "sent": False, "reason": "not_confirmed"}

    status_code = send_booking_confirmation_email(booking)
    logger.info(
        "Booking confirmation email sent for booking=%s to=%s sendgrid_status=%s",
        booking.id,
        booking.email,
        status_code,
    )
    return {"booking_id": booking.id, "sent": True, "status_code": status_code}
