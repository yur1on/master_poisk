from django.db import models
from django.utils import timezone
from accounts.models import WorkshopProfile, ServicePrice


class Showcase(models.Model):
    workshop = models.OneToOneField(WorkshopProfile, on_delete=models.CASCADE, related_name='showcase')
    cover_photo = models.ImageField(upload_to='showcase/covers/', blank=True, null=True, verbose_name='Фото главной страницы')
    viber = models.CharField(max_length=255, blank=True, verbose_name='Viber (номер или ссылка)')
    telegram = models.CharField(max_length=255, blank=True, verbose_name='Telegram (username или ссылка)')
    instagram = models.CharField(max_length=255, blank=True, verbose_name='Instagram (username или ссылка)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Витрина'
        verbose_name_plural = 'Витрины'

    def __str__(self):
        return f"Витрина для {self.workshop.workshop_name}"


class GalleryImage(models.Model):
    showcase = models.ForeignKey(Showcase, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='showcase/gallery/', verbose_name='Изображение работы')
    description = models.TextField(blank=True, verbose_name='Описание')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Изображение галереи'
        verbose_name_plural = 'Изображения галереи'

    def __str__(self):
        return f"Изображение для {self.showcase.workshop.workshop_name}"


class Specialist(models.Model):
    showcase = models.ForeignKey(Showcase, on_delete=models.CASCADE, related_name='specialists')
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    position = models.CharField("Должность", max_length=150, blank=True)
    photo = models.ImageField("Фото", upload_to='showcase/specialists/', blank=True, null=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    bio = models.TextField("О специалисте", blank=True)
    is_active = models.BooleanField("Показывать на витрине", default=True)
    order = models.PositiveIntegerField("Порядок (меньше — выше)", default=100)

    # --- связи на услуги (можно выбрать несколько)
    services = models.ManyToManyField(ServicePrice, blank=True, related_name='specialists', verbose_name='Услуги')

    created_at = models.DateTimeField("Создан", default=timezone.now)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Специалист"
        verbose_name_plural = "Специалисты"
        ordering = ['order', 'last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()
