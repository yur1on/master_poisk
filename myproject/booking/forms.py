from django import forms
from django.core.exceptions import ValidationError
from .models import Availability, Appointment
from accounts.models import ServicePrice
from datetime import date as _date
from django.forms import modelformset_factory


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['date', 'start_time', 'end_time', 'service']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Можно передать workshop или specialist, чтобы отфильтровать услуги
        workshop = kwargs.pop('workshop', None)
        specialist = kwargs.pop('specialist', None)
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = ServicePrice.objects.none()
        if workshop:
            self.fields['service'].queryset = ServicePrice.objects.filter(workshop=workshop)
        elif specialist:
            try:
                self.fields['service'].queryset = ServicePrice.objects.filter(workshop=specialist.showcase.workshop)
            except Exception:
                self.fields['service'].queryset = ServicePrice.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date_field = cleaned_data.get('date')

        if date_field and date_field < _date.today():
            raise ValidationError('Дата не может быть в прошлом.')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Время начала должно быть раньше времени окончания.')

        return cleaned_data


AvailabilityFormSet = modelformset_factory(
    Availability,
    form=AvailabilityForm,
    extra=1,
    can_delete=True
)


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        # убираем service — услуга берётся из Availability (чтобы не было рассинхрона)
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # если нужно, можно принимать specialist или availability для валидаций
        super().__init__(*args, **kwargs)
