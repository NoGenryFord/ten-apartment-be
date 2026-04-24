from django.core.management.base import BaseCommand

from apartments.services import reconcile_reserved_schedules

# Для Дебага
class Command(BaseCommand):
    help = "Reconcile reserved schedules with booking state"

    def handle(self, *args, **options):
        stats = reconcile_reserved_schedules()
        self.stdout.write(
            self.style.SUCCESS(
                "Reconciliation done: expired_bookings={expired_bookings}, reserved_to_booked={reserved_to_booked}, reserved_to_available={reserved_to_available}".format(
                    **stats
                )
            )
        )
