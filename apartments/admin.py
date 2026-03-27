from django.contrib import admin

from .models import Apartment, User, Schedule, Price, ApartmentType, Booking, BookingSlot, ApartmentPhoto, ApartmentVideo

class ApartmentPhotoInline(admin.StackedInline):
    model = ApartmentPhoto
    extra = 0

class ApartmentVideoInline(admin.StackedInline):
    model = ApartmentVideo
    extra = 0

class ApartmentScheduleInline(admin.StackedInline):
    model = Schedule
    extra = 0

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'description')
    search_fields = ('name', 'description', 'type')
    list_filter = ('type',)
    inlines = [ApartmentScheduleInline, ApartmentPhotoInline, ApartmentVideoInline]
    list_per_page = 50

@admin.register(ApartmentPhoto)
class ApartmentPhotoAdmin(admin.ModelAdmin):
    list_display = ('apartments_id', 'photo', 'order')

@admin.register(ApartmentVideo)
class ApartmentVideoAdmin(admin.ModelAdmin):
    pass

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('date', 'apartment', 'price', 'status')
    search_fields = ('date', 'apartment__name', 'price__label', 'status')
    list_filter = ('status', 'price', 'apartment')
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
