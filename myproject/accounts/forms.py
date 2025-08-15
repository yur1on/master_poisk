from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ClientProfile, WorkshopProfile, ActivityArea, ServicePrice
from django import forms
from django.forms import modelformset_factory
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
            'city', 'activity_area',
            'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ActivityArea.objects.order_by('category', 'name')
        self.fields['activity_area'].queryset = qs
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
    city = forms.CharField(label='Город', max_length=100, required=False)
    activity_area = forms.ModelMultipleChoiceField(
        queryset=ActivityArea.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Сферы деятельности'
    )

    class Meta:
        model = WorkshopProfile
        fields = ['workshop_name', 'workshop_address', 'city', 'activity_area']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['workshop_name', 'workshop_address', 'city']:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        qs = ActivityArea.objects.order_by('category', 'name')
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
        grouped = OrderedDict()
        for area in qs:
            cat = CATEGORY_TRANSLATIONS.get(area.category, area.get_category_display())
            grouped.setdefault(cat, []).append(area)
        self.grouped_activity = grouped

class ServicePriceForm(forms.ModelForm):
    class Meta:
        model = ServicePrice
        fields = ['activity_area', 'service_name', 'price', 'duration']
        labels = {
            'activity_area': 'Сфера деятельности',
            'service_name': 'Услуга',
            'price': 'Цена (руб.)',
            'duration': 'Длительность'
        }
        widgets = {
            'activity_area': forms.Select(attrs={'class': 'form-control'}),
            'service_name': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, workshop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if workshop:
            self.fields['activity_area'].queryset = workshop.activity_area.all()
        self.fields['service_name'].choices = [('', '---------')]

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('activity_area'):
            raise forms.ValidationError({'activity_area': 'Выберите сферу деятельности.'})
        if not cleaned_data.get('service_name'):
            raise forms.ValidationError({'service_name': 'Выберите услугу.'})
        if not cleaned_data.get('price'):
            raise forms.ValidationError({'price': 'Укажите цену.'})
        return cleaned_data

ServicePriceFormSet = modelformset_factory(
    ServicePrice,
    form=ServicePriceForm,
    extra=1,
    can_delete=True,
    max_num=100
)