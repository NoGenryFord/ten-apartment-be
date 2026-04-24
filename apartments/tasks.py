import logging

from celery import shared_task

from apartments.services import reconcile_reserved_schedules

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
