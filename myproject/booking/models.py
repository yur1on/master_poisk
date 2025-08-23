# booking/models.py
from django.db import models
from showcase.models import Specialist, Showcase
from accounts.models import ClientProfile, ServicePrice
from django.utils import timezone
from datetime import timedelta

class Availability(models.Model):
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Начало')
    end_time = models.TimeField(verbose_name='Конец')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Доступное время'
        verbose_name_plural = 'Доступные времена'
        unique_together = ['specialist', 'date', 'start_time']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.specialist} - {self.date} {self.start_time}-{self.end_time}"

    def duration(self):
        start = timezone.datetime.combine(self.date, self.start_time)
        end = timezone.datetime.combine(self.date, self.end_time)
        return end - start

class Appointment(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='appointments')
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='appointments')
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(ServicePrice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Услуга')
    notes = models.TextField(blank=True, verbose_name='Заметки')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ], default='pending')

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['availability__date', 'availability__start_time']

    def __str__(self):
        return f"{self.client} у {self.specialist} - {self.availability.date} {self.availability.start_time}"

    def is_available(self):
        return not Appointment.objects.filter(availability=self.availability, status__in=['pending', 'confirmed']).exists()