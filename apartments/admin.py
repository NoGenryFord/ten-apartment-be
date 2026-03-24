from django.contrib import admin

from .models import Apartment, User, Schedule, Price, ApartmentType, Booking, BookingSlot

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'description')
    search_fields = ('name', 'description', 'type')
    list_filter = ('type',)
    # ordering = ('name', 'type')


# Register your models here.
admin.site.register(User)
admin.site.register(Schedule)
admin.site.register(Price)
admin.site.register(ApartmentType)
admin.site.register(Booking)
admin.site.register(BookingSlot)
