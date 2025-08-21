# showcase/admin.py
from django.contrib import admin
from .models import Showcase, GalleryImage

@admin.register(Showcase)
class ShowcaseAdmin(admin.ModelAdmin):
    list_display = ('workshop', 'phone_display', 'viber', 'telegram', 'instagram', 'updated_at')
    search_fields = ('workshop__workshop_name', 'viber', 'telegram', 'instagram')

    def phone_display(self, obj):
        return obj.workshop.phone if getattr(obj, 'workshop', None) else ''
    phone_display.short_description = 'Телефон студии'

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('showcase', 'uploaded_at')
