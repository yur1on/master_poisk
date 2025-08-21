from django import forms
from .models import Showcase, GalleryImage
from accounts.models import WorkshopProfile
from django.core.validators import FileExtensionValidator
from PIL import Image
import io

# showcase/forms.py
from django import forms
from .models import Showcase, GalleryImage
from accounts.models import WorkshopProfile
from django.core.validators import FileExtensionValidator
from PIL import Image

class ShowcaseForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, required=False, label='Описание')
    phone = forms.CharField(max_length=20, label='Телефон бьюти-студии', required=False)
    working_hours = forms.CharField(max_length=255, required=False, label='Время работы')
    # новые поля соцсетей
    viber = forms.CharField(max_length=255, required=False, label='Viber',
                            widget=forms.TextInput(attrs={'placeholder': 'номер или ссылка (пример: +380501234567 или viber://...)'}))
    telegram = forms.CharField(max_length=255, required=False, label='Telegram',
                               widget=forms.TextInput(attrs={'placeholder': 'username или ссылка (пример: @username или https://t.me/username)'}))
    instagram = forms.CharField(max_length=255, required=False, label='Instagram',
                                widget=forms.TextInput(attrs={'placeholder': 'username без @ или ссылка (пример: username или https://instagram.com/username)'}))

    class Meta:
        model = Showcase
        fields = ['cover_photo', 'description', 'phone', 'working_hours', 'viber', 'telegram', 'instagram']
        labels = {
            'cover_photo': 'Фото главной страницы',
            'description': 'Описание',
            'phone': 'Телефон бьюти-студии',
            'working_hours': 'Время работы',
            'viber': 'Viber',
            'telegram': 'Telegram',
            'instagram': 'Instagram',
        }
        widgets = {
            'cover_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # валидатор расширений для обложки
        self.fields['cover_photo'].validators.append(
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        )

        # при инициализации заполняем description/phone/working_hours из workshop (как раньше)
        if self.instance and getattr(self.instance, 'workshop', None):
            self.fields['description'].initial = self.instance.workshop.description
            self.fields['phone'].initial = self.instance.workshop.phone
            self.fields['working_hours'].initial = self.instance.workshop.working_hours

        # если форма создана для существующего Showcase — Django автоматически подставит initial для viber/telegram/instagram

    def clean_cover_photo(self):
        cover_photo = self.cleaned_data.get('cover_photo')
        if cover_photo:
            if cover_photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')
            try:
                img = Image.open(cover_photo)
                img.verify()
                cover_photo.seek(0)
                img = Image.open(cover_photo)
                if img.format not in ['JPEG', 'PNG', 'GIF']:
                    raise forms.ValidationError('Формат изображения должен быть JPEG, PNG или GIF.')
            except Exception as e:
                raise forms.ValidationError(f'Загруженный файл не является изображением или повреждён: {str(e)}')
        return cover_photo

    def save(self, commit=True):
        # Сохраняем: описание/телефон/время работы в WorkshopProfile (как было)
        instance = super().save(commit=False)
        # Сохраняем соцсети находятся в экземпляре Showcase (instance.viber/telegram/instagram)
        if commit:
            if getattr(instance, 'workshop', None):
                instance.workshop.description = self.cleaned_data.get('description', instance.workshop.description)
                instance.workshop.phone = self.cleaned_data.get('phone', instance.workshop.phone)
                instance.workshop.working_hours = self.cleaned_data.get('working_hours', instance.workshop.working_hours)
                instance.workshop.save()

            # соцсети уже находятся в cleaned_data и принадлежат Showcase
            instance.viber = self.cleaned_data.get('viber', instance.viber)
            instance.telegram = self.cleaned_data.get('telegram', instance.telegram)
            instance.instagram = self.cleaned_data.get('instagram', instance.instagram)

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