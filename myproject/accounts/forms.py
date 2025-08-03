from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ClientProfile, WorkshopProfile

class ClientRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(label='Телефон')

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

# forms.py
from .models import ActivityArea

class WorkshopRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    workshop_name = forms.CharField(label='Название мастерской')
    workshop_address = forms.CharField(label='Адрес')
    phone = forms.CharField(label='Телефон мастерской')
    activity_area = forms.ModelMultipleChoiceField(
        label='Сферы деятельности',
        queryset=ActivityArea.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'workshop_name', 'workshop_address', 'phone', 'activity_area', 'password1', 'password2']

class ClientProfileForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = ClientProfile
        fields = ['phone']

from .models import WorkshopProfile, ActivityArea

# user_profile/forms.py

from django import forms
from .models import WorkshopProfile, ActivityArea
from django.contrib.auth.models import User

class WorkshopProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    activity_area = forms.ModelMultipleChoiceField(
        queryset=ActivityArea.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Сферы деятельности'
    )

    class Meta:
        model = WorkshopProfile
        fields = ['workshop_name', 'workshop_address', 'phone', 'activity_area']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # задаём класс form-control всем текстовым полям
        for field_name in ['workshop_name', 'workshop_address', 'phone']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
