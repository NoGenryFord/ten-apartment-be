from datetime import timedelta

from django.contrib import admin, messages
from django.db import transaction

# custom admin
from .admin_custom.admin_inline import (
    ApartmentScheduleInline,
    ApartmentPhotoInline,
    ApartmentVideoInline,
)
from .admin_custom.calendar_windget import schedule_calendar

from django.utils import timezone


from .models import (
    Apartment,
    User,
    Schedule,
    Price,
    ApartmentType,
    Booking,
    BookingSlot,
    ApartmentPhoto,
    ApartmentVideo,
)

from .forms.ApartmentActionForm import ApartmentActionForm, StartDateForm
from .services import apply_booking_status_transition

import logging

logger = logging.getLogger("django")


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    readonly_fields = ("schedule_calendar",)
    fields = (
        "name",
        "type",
        "description",
        "schedule_calendar",
        "address",
        "max_guests",
    )
    list_display = ("id", "name", "type", "description")
    search_fields = ("name", "description", "type")
    list_filter = ("type",)
    inlines = [ApartmentScheduleInline, ApartmentPhotoInline, ApartmentVideoInline]
    list_per_page = 50

    actions = ("create_schedule_for_next_30_days",)
    action_form = ApartmentActionForm

    class Media:
        js = ("js/apartment_action_toggle.js",)

    @admin.display(description="Schedule Calendar")
    def schedule_calendar(self, obj):
        if not obj.pk:
            return "Schedule not available"
        return schedule_calendar(obj)

    @admin.action(description="Create Schedule for next 30 days")
    def create_schedule_for_next_30_days(self, request, queryset):
        date_form = StartDateForm({"start_date": request.POST.get("start_date")})
        if not date_form.is_valid():
            self.message_user(request, "Invalid start date.", level=messages.ERROR)
            return

        default_price = Price.objects.order_by("id").first()
        if default_price is None:
            self.message_user(
                request,
                "Create at least one Price before generating schedule.",
                level=messages.ERROR,
            )
            return

        start_date = date_form.cleaned_data.get("start_date") or timezone.localdate()
        end_date = start_date + timedelta(days=29)
        total_create = 0

        for apartment in queryset:
            existing_dates = set(
                Schedule.objects.filter(
                    apartment=apartment, date__range=(start_date, end_date)
                ).values_list("date", flat=True)
            )

            slots_to_create = []
            for offset in range(30):
                slot_date = start_date + timedelta(days=offset)
                if slot_date in existing_dates:
                    continue

                slots_to_create.append(
                    Schedule(
                        apartment=apartment,
                        date=slot_date,
                        price=default_price,
                        status=Schedule.Status.AVAILABLE,
                    )
                )

            Schedule.objects.bulk_create(slots_to_create, ignore_conflicts=True)
            total_create += len(slots_to_create)

            self.message_user(
                request,
                f"Create {total_create} schedule slots.",
                level=messages.SUCCESS,
            )


@admin.register(ApartmentPhoto)
class ApartmentPhotoAdmin(admin.ModelAdmin):
    list_display = ("apartments_id", "photo")


@admin.register(ApartmentVideo)
class ApartmentVideoAdmin(admin.ModelAdmin):
    pass


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "apartment", "price", "status")
    search_fields = ("date", "apartment__name", "price__label", "status")
    list_filter = ("status", "price", "apartment")
    date_hierarchy = "date"
    list_per_page = 50


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ("price", "label")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "phone",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    search_fields = ("username", "first_name", "last_name", "email", "phone")
    list_filter = ("is_staff", "is_superuser", "is_active")


@admin.register(ApartmentType)
class ApartmentTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    search_fields = ("name",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "email",
        "status",
        "total_price",
        "created_at",
        "reserved_until",
        "paid",
    )

    def save_model(self, request, obj, form, change):
        """
        EN:
        Keep booking/schedule consistency when status is changed from admin UI.

        RU:
        Сохраняет консистентность брони/слотов при смене статуса в админке.
        """
        if not change:
            return super().save_model(request, obj, form, change)

        previous_status = Booking.objects.only("status").get(pk=obj.pk).status
        new_status = obj.status

        with transaction.atomic():
            super().save_model(request, obj, form, change)

            if previous_status != new_status and new_status in {
                Booking.Status.CONFIRMED,
                Booking.Status.CANCELED,
                Booking.Status.EXPIRED,
            }:
                apply_booking_status_transition(booking=obj, target_status=new_status)


@admin.register(BookingSlot)
class BookingSlotAdmin(admin.ModelAdmin): ...
