from django.contrib import admin

from .models import Apartment, User, Schedule, Price, ApartmentType, Booking, BookingSlot, ApartmentPhoto, ApartmentVideo

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'description')
    search_fields = ('name', 'description', 'type')
    list_filter = ('type',)
    # ordering = ('name', 'type')

@admin.register(ApartmentPhoto)
class ApartmentPhotoAdmin(admin.ModelAdmin):
    list_display = ('apartments_id', 'photo', 'order')

@admin.register(ApartmentVideo)
class ApartmentVideoAdmin(admin.ModelAdmin):
    pass