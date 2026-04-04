from django.contrib import admin

# custom admin
from .admin_custom.admin_inline import ApartmentScheduleInline, ApartmentPhotoInline, ApartmentVideoInline
from .admin_custom.calendar_windget import schedule_calendar


from .models import Apartment, User, Schedule, Price, ApartmentType, Booking, BookingSlot, ApartmentPhoto, ApartmentVideo

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    readonly_fields = ('schedule_calendar',)
    fields = ('name', 'type', 'description', 'schedule_calendar')
    list_display = ('name', 'type', 'description')
    search_fields = ('name', 'description', 'type')
    list_filter = ('type',)
    inlines = [ApartmentScheduleInline, ApartmentPhotoInline, ApartmentVideoInline]
    list_per_page = 50

    @admin.display(description='Schedule Calendar')
    def schedule_calendar(self, obj):
        if not obj.pk:
            return "Schedule not available"
        return schedule_calendar(obj)

@admin.register(ApartmentPhoto)
class ApartmentPhotoAdmin(admin.ModelAdmin):
    list_display = ('apartments_id', 'photo')

@admin.register(ApartmentVideo)
class ApartmentVideoAdmin(admin.ModelAdmin):
    pass

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('date', 'apartment', 'price', 'status')
    search_fields = ('date', 'apartment__name', 'price__label', 'status')
    list_filter = ('status', 'price', 'apartment')
    date_hierarchy = 'date'
    list_per_page = 50

    @admin.action(description='Create Schedule for next 30 days')
    def create_schedule_for_next_30_days(self, request, queryset):
        pass

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('price', 'label')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

@admin.register(ApartmentType)
class ApartmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


