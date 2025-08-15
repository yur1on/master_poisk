from django import forms
from .models import Showcase, GalleryImage
from accounts.models import WorkshopProfile
from django.core.validators import FileExtensionValidator
from PIL import Image
import io

class ShowcaseForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, required=False, label='Описание')
    phone = forms.CharField(max_length=20, label='Телефон бьюти-студии')
    working_hours = forms.CharField(max_length=255, required=False, label='Время работы')

    class Meta:
        model = Showcase
        fields = ['cover_photo', 'description', 'phone', 'working_hours']
        labels = {
            'cover_photo': 'Фото главной страницы',
            'description': 'Описание',
            'phone': 'Телефон бьюти-студии',
            'working_hours': 'Время работы'
        }
        widgets = {
            'cover_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_photo'].validators.append(
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        )
        if self.instance and self.instance.workshop:
            self.fields['description'].initial = self.instance.workshop.description
            self.fields['phone'].initial = self.instance.workshop.phone
            self.fields['working_hours'].initial = self.instance.workshop.working_hours

    def clean_cover_photo(self):
        cover_photo = self.cleaned_data.get('cover_photo')
        if cover_photo:
            if cover_photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')
            try:
                img = Image.open(cover_photo)
                img.verify()  # Проверка целостности
                cover_photo.seek(0)  # Сброс курсора
                img = Image.open(cover_photo)  # Повторное открытие
                if img.format not in ['JPEG', 'PNG', 'GIF']:
                    raise forms.ValidationError('Формат изображения должен быть JPEG, PNG или GIF.')
            except Exception as e:
                raise forms.ValidationError(f'Загруженный файл не является изображением или повреждён: {str(e)}')
        return cover_photo

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.workshop.description = self.cleaned_data['description']
            instance.workshop.phone = self.cleaned_data['phone']
            instance.workshop.working_hours = self.cleaned_data['working_hours']
            instance.workshop.save()
            instance.save()
        return instance

class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['image', 'description']
        labels = {'image': 'Изображение работы', 'description': 'Описание'}
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите описание изображения'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].validators.append(
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')
            try:
                img = Image.open(image)
                img.verify()  # Проверка целостности
                image.seek(0)  # Сброс курсора
                img = Image.open(image)  # Повторное открытие
                if img.format not in ['JPEG', 'PNG', 'GIF']:
                    raise forms.ValidationError('Формат изображения должен быть JPEG, PNG или GIF.')
            except Exception as e:
                raise forms.ValidationError(f'Загруженный файл не является изображением или повреждён: {str(e)}')
        return image