from django.db import models
from accounts.models import WorkshopProfile

class Showcase(models.Model):
    workshop = models.OneToOneField(WorkshopProfile, on_delete=models.CASCADE, related_name='showcase')
    cover_photo = models.ImageField(upload_to='showcase/covers/', blank=True, null=True, verbose_name='Фото главной страницы')
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
    description = models.CharField(max_length=255, blank=True, verbose_name='Описание')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Изображение галереи'
        verbose_name_plural = 'Изображения галереи'

    def __str__(self):
        return f"Изображение для {self.showcase.workshop.workshop_name}"