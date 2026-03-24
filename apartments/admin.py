from django.contrib import admin

from .models import Apartment, User, Schedule, Price, ApartmentType, Booking, BookingSlot

# Register your models here.
admin.site.register(Apartment)
admin.site.register(User)
admin.site.register(Schedule)
admin.site.register(Price)
admin.site.register(ApartmentType)
admin.site.register(Booking)
admin.site.register(BookingSlot)

