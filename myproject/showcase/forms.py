



# showcase/forms.py
from django import forms
from django.forms import modelformset_factory
from .models import Showcase, GalleryImage

class ShowcaseForm(forms.ModelForm):
    class Meta:
        model = Showcase
        fields = ['cover_photo']
        labels = {'cover_photo': 'Фото главной страницы'}
        widgets = {'cover_photo': forms.FileInput(attrs={'class': 'form-control'})}

GalleryImageFormSet = modelformset_factory(
    GalleryImage,
    fields=('image', 'description'),
    extra=5,
    max_num=20,
    can_delete=True,
    labels={'image': 'Изображение работы', 'description': 'Описание'},
    widgets={
        'image': forms.FileInput(attrs={'class': 'form-control'}),
        'description': forms.TextInput(attrs={'class': 'form-control'}),
    }
)