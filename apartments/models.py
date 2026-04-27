from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from phonenumber_field.modelfields import PhoneNumberField

from geopy.geocoders import Nominatim

import logging

logger = logging.getLogger("apartments")


class User(AbstractUser):
    """
    Кастомная модель юзера, все поля из стандратного User +
    phone - поле основано на библиотеке django-phonenumber-field, для удобного хранения и валидации телефонных номеров.
    Уникальное поле, так как по нему, в том числе будет происходить авторизация.
    """

    phone = PhoneNumberField(unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)

    class Meta:
        verbose_name_plural = "Users"


class Schedule(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        BOOKED = "booked", "Booked"
        MAINTENANCE = "maintenance", "Maintenance"

    date = models.DateField()
    apartment = models.ForeignKey(
        "apartments.Apartment", on_delete=models.CASCADE, related_name="schedule"
    )
    price = models.ForeignKey(
        "apartments.Price",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="schedule",
    )
    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.AVAILABLE
    )

    class Meta:
        unique_together = ("date", "apartment")
        ordering = ("date",)

    def __str__(self):
        return f"{self.apartment} - {self.date} - {self.status}"

    def clean(self):
        if self.status != self.Status.MAINTENANCE and self.price is None:
            raise ValidationError("Price must be set for non-maintenance schedules.")


class Apartment(models.Model):
    """
    Модель для хранения квартир.
    type - ссылка на тип квартиры, для удобства фильтрации и отображения. Например: Эконом, Стандарт, Премиум.
    """

    name = models.CharField(max_length=100)
    type = models.ForeignKey("apartments.ApartmentType", on_delete=models.CASCADE)
    description = models.TextField()
    max_guests = models.PositiveIntegerField(default=0)

    tags = models.ManyToManyField(
        "apartments.Tag",
        related_name="apartments",
        blank=True,
    )

    address = models.CharField(max_length=255, null=True, blank=True)

    # Coordinates
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    class Meta:
        unique_together = ("name", "type")
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        should_geocode = False

        if self.address:
            if not self.pk:
                should_geocode = True
            else:
                try:
                    old = Apartment.objects.get(pk=self.pk)
                    if old.address != self.address:
                        should_geocode = True
                        logger.debug(
                            f"Address changed from '{old.address}' to '{self.address}', re-geocoding"
                        )
                except Apartment.DoesNotExist:
                    should_geocode = True

        if should_geocode:
            geolocator = Nominatim(user_agent="apartments")
            try:
                location = geolocator.geocode(self.address)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
                    logger.debug(
                        f"Geocoded '{self.address}' -> {self.latitude}, {self.longitude}"
                    )
                else:
                    logger.warning(
                        f"Geocoder returned no results for address: '{self.address}'"
                    )
            except Exception as e:
                logger.error(f"Error with geocoding address '{self.address}': {e}")

        super().save(*args, **kwargs)


class ApartmentPhoto(models.Model):
    """
    Модель для хранения нескольких фото на одну квартиру. Сортировка по полю order.
    """

    apartments = models.ForeignKey(
        "apartments.Apartment", on_delete=models.CASCADE, related_name="photos"
    )
    photo = models.ImageField(upload_to="apartments/photos/")
    # order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        unique_together = ("apartments", "photo")


class ApartmentVideo(models.Model):
    """
    Модель для хранения нескольких видео на одну квартиру. Сортировка по полю order.
    """

    apartments = models.ForeignKey(
        "apartments.Apartment", on_delete=models.CASCADE, related_name="videos"
    )
    video = models.FileField(upload_to="apartments/videos/")
    # order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        unique_together = ("apartments", "video")


class Tag(models.Model):
    """
    Модель для хранения тегов на квартиру. Например: "У моря", "Рядом с метро". "WiFi" и т.д.
    many-to-many связь. Сортировка по полю order.
    """

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class ApartmentType(models.Model):
    """
    Для типа квартиры. Например: Эконом, Стандарт, Премиум.
    В моделе Квартиры её тип ссылать на эту таблицу.
    """

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Price(models.Model):
    """
    Для переиспользования цены, и адаптации под разные дни: выходные, будни, праздники и т.д. И для разных типов апартаментов
    """

    price = models.DecimalField(max_digits=10, decimal_places=2)
    label = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.label} - {self.price}"


class Booking(models.Model):
    """
    Бронирование пользователя.
    Всегда сохраняется в историю, не зависимо от статуса Успех, Отмены итд.
    """

    class Status(models.TextChoices):
        """
        Заготовленные варианты окончания бронирования.
        """

        PENDING = "pending", "Pending"  # Ожидание Оплаты
        CONFIRMED = "confirmed", "Confirmed"  # Подтвержденно
        CANCELED = "canceled", "Canceled"  # Отмененно
        EXPIRED = "expired", "Expired"  # Срок оплаты/бронированния истек

    user = models.ForeignKey(
        "apartments.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    email = models.EmailField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.PENDING
    )
    reserved_until = models.DateTimeField(null=True, blank=True)  #'Deadline' оплаты
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Booking {self.pk} by {self.email} - {self.status}"


class BookingSlot(models.Model):
    """
    price_snapshot — цена дня на момент бронирования.
    Один слот на один день в Букинге.
    """

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.PROTECT)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Booking id - {self.booking.pk}, schedule - {self.schedule}, price - {self.price_snapshot}"

    class Meta:
        unique_together = (
            "booking",
            "schedule",
        )  # один слот не может войти в бронь дважды
