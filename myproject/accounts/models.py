from django.contrib.auth.models import User
from django.db import models

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"Клиент: {self.user.username}"

# models.py
class WorkshopProfile(models.Model):
    ACTIVITY_CHOICES = [
        ('phones', 'Ремонт телефонов'),
        ('computers', 'Ремонт компьютеров'),
        ('appliances', 'Ремонт бытовой техники'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    workshop_name = models.CharField(max_length=100)
    workshop_address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    activity_area = models.ManyToManyField(
        'ActivityArea',
        verbose_name='Сферы деятельности'
    )

    def __str__(self):
        return f"Мастерская: {self.workshop_name}"


class ActivityArea(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
