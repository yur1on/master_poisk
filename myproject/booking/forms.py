# booking/forms.py
from django import forms
from .models import Availability, Appointment
from accounts.models import ServicePrice
from datetime import date, timedelta
from django.core.exceptions import ValidationError
import calendar

class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')

        if date and date < date.today():
            raise ValidationError('Дата не может быть в прошлом.')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Время начала должно быть раньше времени окончания.')

        return cleaned_data

AvailabilityFormSet = forms.modelformset_factory(
    Availability,
    form=AvailabilityForm,
    extra=1,
    can_delete=True
)

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['service', 'notes']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        specialist = kwargs.pop('specialist', None)
        super().__init__(*args, **kwargs)
        if specialist:
            workshop = specialist.showcase.workshop
            self.fields['service'].queryset = ServicePrice.objects.filter(workshop=workshop)