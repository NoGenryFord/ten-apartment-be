import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ten_apartment_be.settings")

app = Celery("ten_apartment_be")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "reconcile-reserved-schedules-every-minute": {
        "task": "apartments.tasks.reconcile_reserved_schedules_task",
        "schedule": crontab(minute="*/10"),
    },
}
