from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class Schedule(models.Model):
    date = models.DateField()
    apartment = models.ForeignKey('apartments.Apartment', on_delete=models.CASCADE)
    Price = models.ForeignKey('Price', on_delete=models.CASCADE)
    is_booking = models.BooleanField()

class Apartment(models.Model):
    name = models.CharField(max_length=100)
    type = models.ForeignKey('apartments.ApartmentType', on_delete=models.CASCADE)
    description = models.TextField()
    photo = models.ImageField(upload_to='apartments/')
    video = models.FileField(upload_to='apartments/')

class ApartmentType(models.Model):
    name = models.CharField(max_length=100)

class Price(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Booking(models.Model):
    apartments = models.ForeignKey('apartments.Apartment', on_delete=models.CASCADE)
    price = models.ForeignKey('Price', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)


