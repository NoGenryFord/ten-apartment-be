from django.contrib import admin
from apartments.models import Schedule, ApartmentPhoto, ApartmentVideo

class ApartmentPhotoInline(admin.StackedInline):
    model = ApartmentPhoto
    extra = 0
    classes = ['collapse']

class ApartmentVideoInline(admin.StackedInline):
    model = ApartmentVideo
    extra = 0
    classes = ['collapse']


class ApartmentScheduleInline(admin.StackedInline):
    model = Schedule
    extra = 0
    classes = ['collapse']