from django import forms
from django.forms import modelformset_factory
from .models import Showcase, GalleryImage

class ShowcaseForm(forms.ModelForm):
    class Meta:
        model = Showcase
        fields = ['cover_photo']
        labels = {'cover_photo': 'Фото главной страницы'}
        widgets = {'cover_photo': forms.FileInput(attrs={'class': 'form-control'})}



GalleryFormSet = modelformset_factory(
    GalleryImage,
    fields=('image', 'description'),
    extra=5,  # Default blank forms for new images
    max_num=20,  # Max total forms to prevent abuse
    can_delete=True,
    labels={'image': 'Изображение работы', 'description': 'Описание'},
    widgets={
        'image': forms.FileInput(attrs={'class': 'form-control'}),
        'description': forms.TextInput(attrs={'class': 'form-control'}),
    }
)

class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['image', 'description']
        labels = {'image': 'Новое изображение', 'description': 'Описание'}
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }