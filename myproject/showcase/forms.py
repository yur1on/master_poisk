from django import forms
from django.forms import modelformset_factory
from .models import Showcase, GalleryImage

class ShowcaseForm(forms.ModelForm):
    class Meta:
        model = Showcase
        fields = ['cover_photo']
        labels = {'cover_photo': 'Фото главной страницы'}
        widgets = {'cover_photo': forms.FileInput(attrs={'class': 'form-control'})}

class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['image', 'description']
        labels = {'image': 'Изображение работы', 'description': 'Описание'}
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите описание изображения'}),
        }

GalleryImageFormSet = modelformset_factory(
    GalleryImage,
    fields=('image', 'description'),
    extra=3,
    max_num=20,
    can_delete=True,
    labels={'image': 'Изображение работы', 'description': 'Описание'},
    widgets={
        'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите описание изображения'}),
    }
)