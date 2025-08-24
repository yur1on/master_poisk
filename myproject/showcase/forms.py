from django import forms
from django.core.validators import FileExtensionValidator
from PIL import Image
from .models import Showcase, GalleryImage, Specialist
from accounts.models import WorkshopProfile, ServicePrice


class ShowcaseForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, required=False, label='Описание')
    phone = forms.CharField(max_length=20, label='Телефон бьюти-студии', required=False)
    working_hours = forms.CharField(max_length=255, required=False, label='Время работы')
    viber = forms.CharField(max_length=255, required=False, label='Viber',
                            widget=forms.TextInput(attrs={'placeholder': 'номер или ссылка (пример: +380501234567 или viber://...)'}))
    telegram = forms.CharField(max_length=255, required=False, label='Telegram',
                               widget=forms.TextInput(attrs={'placeholder': '@username или https://t.me/username'}))
    instagram = forms.CharField(max_length=255, required=False, label='Instagram',
                                widget=forms.TextInput(attrs={'placeholder': 'username или https://instagram.com/username'}))

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
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
        )

    def clean_cover_photo(self):
        cover_photo = self.cleaned_data.get('cover_photo')
        if cover_photo:
            if cover_photo.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')
            try:
                img = Image.open(cover_photo)
                img.verify()
                cover_photo.seek(0)
                img = Image.open(cover_photo)
                if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                    raise forms.ValidationError('Формат изображения должен быть JPEG, PNG, GIF или WEBP.')
            except Exception as e:
                raise forms.ValidationError(f'Загруженный файл не является изображением или повреждён: {str(e)}')
        return cover_photo

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit and getattr(instance, 'workshop', None):
            # опционально синхронизируем данные в WorkshopProfile, если вам нужно
            wp = instance.workshop
            wp.description = self.cleaned_data.get('description', wp.description)
            wp.phone = self.cleaned_data.get('phone', wp.phone)
            wp.working_hours = self.cleaned_data.get('working_hours', getattr(wp, 'working_hours', ''))
            wp.save()
        # соцсети уже в instance
        if commit:
            instance.save()
        return instance


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['image', 'description']
        labels = {'image': 'Изображение работы', 'description': 'Описание'}
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].validators.append(
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
        )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')
            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)
                img = Image.open(image)
                if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                    raise forms.ValidationError('Формат изображения должен быть JPEG, PNG, GIF или WEBP.')
            except Exception as e:
                raise forms.ValidationError(f'Загруженный файл не является изображением или повреждён: {str(e)}')
        return image


class SpecialistForm(forms.ModelForm):
    class Meta:
        model = Specialist
        fields = ['first_name', 'last_name', 'position', 'photo', 'phone', 'bio', 'is_active', 'order', 'services']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'services': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        # можно передать workshop=workshop, чтобы отфильтровать услуги по студии
        workshop = kwargs.pop('workshop', None)
        super().__init__(*args, **kwargs)
        self.fields['photo'].validators.append(FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']))

        # по умолчанию пустой queryset — чтобы не показывать услуги чужих студий
        self.fields['services'].queryset = ServicePrice.objects.none()
        if workshop:
            self.fields['services'].queryset = ServicePrice.objects.filter(workshop=workshop)

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')
            try:
                img = Image.open(photo)
                img.verify()
            except Exception:
                raise forms.ValidationError('Загруженный файл не является корректным изображением.')
            photo.seek(0)
        return photo
