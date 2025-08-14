# accounts/models.py
from django.db import models
from django.contrib.auth.models import User

class ActivityArea(models.Model):
    CATEGORY_CHOICES = [
        ('hair', 'Уход за волосами'),
        ('nails', 'Ногтевой сервис'),
        ('cosmetology', 'Косметология'),
        ('makeup', 'Макияж'),
        ('brows_lashes', 'Уход за бровями и ресницами'),
        ('epilation', 'Эпиляция и депиляция'),
        ('body', 'Массаж и уход за телом'),
        ('tattoo_piercing', 'Тату и пирсинг'),
        ('styling', 'Стилистика и имидж'),
        ('kids', 'Детская бьюти-сфера'),
        ('alternative', 'Альтернативные направления'),
        ('education', 'Обучение и менторство'),
    ]
    name = models.CharField(max_length=100, verbose_name='Название')
    code = models.CharField(max_length=30, unique=True, verbose_name='Код')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name='Категория')

    class Meta:
        verbose_name = 'Сфера деятельности'
        verbose_name_plural = 'Сферы деятельности'

    def __str__(self):
        return self.name

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, verbose_name='Имя')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')

    class Meta:
        verbose_name = 'Профиль клиента'
        verbose_name_plural = 'Профили клиентов'

    def __str__(self):
        return f"Клиент {self.user.username}"

class WorkshopProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    workshop_name = models.CharField(max_length=100, verbose_name='Название бьюти-студии')
    workshop_address = models.CharField(max_length=255, verbose_name='Адрес')
    phone = models.CharField(max_length=20, verbose_name='Телефон бьюти-студии')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    activity_area = models.ManyToManyField(ActivityArea, verbose_name='Сферы деятельности')
    description = models.TextField(blank=True, verbose_name='Описание')
    working_hours = models.CharField(max_length=255, blank=True, verbose_name='Время работы')

    class Meta:
        verbose_name = 'Профиль бьюти-студии'
        verbose_name_plural = 'Профили бьюти-студий'

    def __str__(self):
        return self.workshop_name

class ServicePrice(models.Model):
    workshop = models.ForeignKey(WorkshopProfile, on_delete=models.CASCADE, related_name='service_prices')
    activity_area = models.ForeignKey(ActivityArea, on_delete=models.CASCADE, verbose_name='Сфера деятельности')
    service_name = models.CharField(max_length=100, verbose_name='Название услуги')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    duration = models.CharField(max_length=50, blank=True, verbose_name='Длительность')

    class Meta:
        verbose_name = 'Цена услуги'
        verbose_name_plural = 'Цены услуг'

    def __str__(self):
        return f"{self.service_name} ({self.workshop.workshop_name}) - {self.price} руб."