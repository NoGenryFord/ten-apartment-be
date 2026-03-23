from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser):
    """
    Кастомная модель юзера, все поля из стандратного User +
    phone - поле основано на библиотеке django-phonenumber-field, для удобного хранения и валидации телефонных номеров.
    Уникальное поле, так как по нему, в том числе будет происходить авторизация.
    """
    phone = PhoneNumberField(unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Users'

class Schedule(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        BOOKED = 'booked', 'Booked'
        MAINTENANCE = 'maintenance', 'Maintenance'

    date = models.DateField()
    apartment = models.ForeignKey('apartments.Apartments', on_delete=models.CASCADE, related_name='schedule')
    price = models.ForeignKey('apartments.Prices', on_delete=models.PROTECT)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.AVAILABLE)

    class Meta:
        unique_together = ('date', 'apartment')
        ordering = ('date',)

    def __str__(self):
        return f'{self.apartment} - {self.date} - {self.status}'

class Apartments(models.Model):
    """
    Модель для хранения квартир.
    type - ссылка на тип квартиры, для удобства фильтрации и отображения. Например: Эконом, Стандарт, Премиум.
    """
    name = models.CharField(max_length=100)
    type = models.ForeignKey('apartments.ApartmentTypes', on_delete=models.CASCADE)
    description = models.TextField()
    photo = models.ImageField(upload_to='apartments/', null=True, blank=True)
    video = models.FileField(upload_to='apartments/', null=True, blank=True)

class ApartmentTypes(models.Model):
    """
    Для типа квартиры. Например: Эконом, Стандарт, Премиум.
    В моделе Квартиры её тип ссылать на эту таблицу.
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Prices(models.Model):
    """
    Для переиспользования цены, и адаптации под разные дни: выходные, будни, праздники и т.д. И для разных типов апартаментов
    """
    price = models.DecimalField(max_digits=10, decimal_places=2)
    label = models.CharField(max_length=100)

class Booking(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending' #Ожидание Оплаты
        CONFIRMED = 'confirmed', 'Confirmed' #Подтвержденно
        CANCELED = 'canceled', 'Canceled' #Отмененно
        EXPIRED = 'expired', 'Expired' #Срок оплаты/бронированния истек

    user = models.ForeignKey('apartments.User', on_delete=models.CASCADE, related_name='booking')
    apartments = models.ForeignKey('apartments.Apartments', on_delete=models.CASCADE)
    slots = models.ManyToManyField(Schedule, through='BookingSlots')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING)
    reserved_until = models.DateTimeField(null=True, blank=True) #'Deadline' оплаты
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f'Booking {self.pk} by {self.user} - {self.apartments} - {self.status}'

class BookingSlots(models.Model):
    """
        price_snapshot — цена дня на момент бронирования.
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.PROTECT)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('booking', 'schedule')  # один слот не может войти в бронь дважды


