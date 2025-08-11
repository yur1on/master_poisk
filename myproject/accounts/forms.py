from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ClientProfile, WorkshopProfile, ActivityArea
from collections import OrderedDict

class ClientRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=True)
    name = forms.CharField(label='Имя', max_length=100, required=False)
    phone = forms.CharField(label='Телефон', max_length=20)
    city = forms.CharField(label='Город', max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'phone', 'city', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            ClientProfile.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                phone=self.cleaned_data['phone'],
                city=self.cleaned_data['city']
            )
        return user

class WorkshopRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=True)
    workshop_name = forms.CharField(label='Название бьюти-студии', max_length=100)
    workshop_address = forms.CharField(label='Адрес', max_length=255)
    phone = forms.CharField(label='Телефон бьюти-студии', max_length=20)
    city = forms.CharField(label='Город', max_length=100, required=False)
    activity_area = forms.ModelMultipleChoiceField(
        label='Сферы деятельности',
        queryset=ActivityArea.objects.none(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = [
            'username', 'email',
            'workshop_name', 'workshop_address',
            'phone', 'city', 'activity_area',
            'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ActivityArea.objects.order_by('category', 'name')
        self.fields['activity_area'].queryset = qs

        # Словарь перевода категорий
        CATEGORY_TRANSLATIONS = {
            'hair': 'Уход за волосами',
            'nails': 'Ногтевой сервис',
            'cosmetology': 'Косметология',
            'makeup': 'Макияж',
            'brows_lashes': 'Уход за бровями и ресницами',
            'epilation': 'Эпиляция и депиляция',
            'body': 'Массаж и уход за телом',
            'tattoo_piercing': 'Тату и пирсинг',
            'styling': 'Стилистика и имидж',
            'kids': 'Детская бьюти-сфера',
            'alternative': 'Альтернативные направления',
            'education': 'Обучение и менторство'
        }

        # Группируем для шаблона с переводом
        grouped = OrderedDict()
        for area in qs:
            cat = CATEGORY_TRANSLATIONS.get(area.category, area.get_category_display())
            grouped.setdefault(cat, []).append(area)
        self.grouped_activity = grouped

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = WorkshopProfile.objects.create(
                user=user,
                workshop_name=self.cleaned_data['workshop_name'],
                workshop_address=self.cleaned_data['workshop_address'],
                phone=self.cleaned_data['phone'],
                city=self.cleaned_data['city']
            )
            profile.activity_area.set(self.cleaned_data['activity_area'])
        return user

class ClientProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Email', required=True)
    name = forms.CharField(label='Имя', max_length=100, required=False)
    phone = forms.CharField(label='Телефон', max_length=20)
    city = forms.CharField(label='Город', max_length=100, required=False)

    class Meta:
        model = ClientProfile
        fields = ['name', 'phone', 'city']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['name', 'phone', 'city']:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class WorkshopProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Email', required=True)
    workshop_name = forms.CharField(label='Название бьюти-студии', max_length=100)
    workshop_address = forms.CharField(label='Адрес', max_length=255)
    phone = forms.CharField(label='Телефон бьюти-студии', max_length=20)
    city = forms.CharField(label='Город', max_length=100, required=False)
    activity_area = forms.ModelMultipleChoiceField(
        queryset=ActivityArea.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Сферы деятельности'
    )

    class Meta:
        model = WorkshopProfile
        fields = ['workshop_name', 'workshop_address', 'phone', 'city', 'activity_area']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['workshop_name', 'workshop_address', 'phone', 'city']:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        # Словарь перевода категорий
        CATEGORY_TRANSLATIONS = {
            'hair': 'Уход за волосами',
            'nails': 'Ногтевой сервис',
            'cosmetology': 'Косметология',
            'makeup': 'Макияж',
            'brows_lashes': 'Уход за бровями и ресницами',
            'epilation': 'Эпиляция и депиляция',
            'body': 'Массаж и уход за телом',
            'tattoo_piercing': 'Тату и пирсинг',
            'styling': 'Стилистика и имидж',
            'kids': 'Детская бьюти-сфера',
            'alternative': 'Альтернативные направления',
            'education': 'Обучение и менторство'
        }

        # Группируем для шаблона с переводом
        qs = ActivityArea.objects.order_by('category', 'name')
        grouped = OrderedDict()
        for area in qs:
            cat = CATEGORY_TRANSLATIONS.get(area.category, area.get_category_display())
            grouped.setdefault(cat, []).append(area)
        self.grouped_activity = grouped

    description = forms.CharField(widget=forms.Textarea, required=False, label='Описание')
    working_hours = forms.CharField(max_length=255, required=False, label='Время работы')

    class Meta:
        model = WorkshopProfile
        fields = ['workshop_name', 'workshop_address', 'phone', 'city', 'activity_area', 'description', 'working_hours']