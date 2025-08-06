from django.db import models
from django.contrib.auth.models import User

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField("Имя", max_length=100, blank=True)
    phone = models.CharField("Телефон", max_length=20)
    city = models.CharField("Город", max_length=100, blank=True)

    def __str__(self):
        return f"Клиент: {self.name or self.user.username}"

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

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
    code = models.CharField("Код", max_length=30, unique=True)
    name = models.CharField("Название", max_length=100)
    category = models.CharField("Категория", max_length=30, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.get_category_display()} → {self.name}"

    class Meta:
        verbose_name = "Сфера деятельности"
        verbose_name_plural = "Сферы деятельности"

class WorkshopProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    workshop_name = models.CharField("Название бьюти-студии", max_length=100)
    workshop_address = models.CharField("Адрес", max_length=255)
    phone = models.CharField("Телефон бьюти-студии", max_length=20)
    city = models.CharField("Город", max_length=100, blank=True)
    activity_area = models.ManyToManyField(
        ActivityArea,
        verbose_name='Сферы деятельности'
    )

    def __str__(self):
        return f"Бьюти-студия: {self.workshop_name}"

    class Meta:
        verbose_name = "Профиль бьюти-студии"
        verbose_name_plural = "Профили бьюти-студий"