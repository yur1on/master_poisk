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

class WorkshopRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    workshop_name = forms.CharField(label='Название мастерской')
    workshop_address = forms.CharField(label='Адрес')
    phone = forms.CharField(label='Телефон мастерской')

    class Meta:
        model = User
        fields = ['username', 'email', 'workshop_name', 'workshop_address', 'phone', 'password1', 'password2']

class ClientProfileForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = ClientProfile
        fields = ['phone']

class WorkshopProfileForm(forms.ModelForm):
    email = forms.EmailField()
    workshop_name = forms.CharField()
    workshop_address = forms.CharField()

    class Meta:
        model = WorkshopProfile
        fields = ['workshop_name', 'workshop_address', 'phone']
