from django.contrib import admin

from .models import Apartment, User, Schedule, Price, ApartmentType, Booking, BookingSlot, ApartmentPhoto, ApartmentVideo

class ApartmentPhotoInline(admin.StackedInline):
    model = ApartmentPhoto
    extra = 0

class ApartmentVideoInline(admin.StackedInline):
    model = ApartmentVideo
    extra = 0

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'description')
    search_fields = ('name', 'description', 'type')
    list_filter = ('type',)
    inlines = [ApartmentPhotoInline, ApartmentVideoInline]

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
