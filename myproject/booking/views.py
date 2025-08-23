# booking/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Specialist, Availability, Appointment
from .forms import AvailabilityFormSet, AppointmentForm
from accounts.models import WorkshopProfile, ClientProfile
from showcase.models import Showcase
from datetime import date, timedelta
from django.utils.dateparse import parse_date
import logging
import calendar

logger = logging.getLogger(__name__)

@login_required
def owner_specialists_list(request):
    try:
        workshop = request.user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        return redirect('accounts:profile')

    specialists = showcase.specialists.filter(is_active=True)
    return render(request, 'booking/owner_specialists_list.html', {
        'specialists': specialists,
        'workshop': workshop,
    })

@login_required
def owner_schedule_manage(request, pk):
    specialist = get_object_or_404(Specialist, pk=pk)
    if specialist.showcase.workshop.user != request.user:
        return redirect('booking:owner_specialists_list')

    month = request.GET.get('month', date.today().strftime('%Y-%m'))
    year, month = map(int, month.split('-'))
    first_day = date(year, month, 1)
    last_day = first_day + timedelta(days=calendar.monthrange(year, month)[1] - 1)

    availabilities = Availability.objects.filter(
        specialist=specialist,
        date__range=(first_day, last_day)
    ).order_by('date', 'start_time')

    if request.method == 'POST':
        formset = AvailabilityFormSet(request.POST, queryset=availabilities)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.specialist = specialist
                instance.save()
            for instance in formset.deleted_objects:
                instance.delete()
            return redirect('booking:owner_schedule_manage', pk=pk)
    else:
        formset = AvailabilityFormSet(queryset=availabilities)

    return render(request, 'booking/owner_schedule_manage.html', {
        'specialist': specialist,
        'formset': formset,
        'month': f'{year}-{month:02d}',
        'availabilities': availabilities,
    })

@login_required
def owner_appointments_list(request, pk):
    specialist = get_object_or_404(Specialist, pk=pk)
    if specialist.showcase.workshop.user != request.user:
        return redirect('booking:owner_specialists_list')

    appointments = specialist.appointments.all().order_by('availability__date', 'availability__start_time')
    return render(request, 'booking/owner_appointments_list.html', {
        'specialist': specialist,
        'appointments': appointments,
    })

@login_required
def owner_confirm_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.specialist.showcase.workshop.user != request.user:
        return redirect('accounts:profile')
    appointment.status = 'confirmed'
    appointment.save()
    return redirect('booking:owner_appointments_list', pk=appointment.specialist.pk)

@login_required
def owner_cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.specialist.showcase.workshop.user != request.user:
        return redirect('accounts:profile')
    appointment.status = 'cancelled'
    appointment.save()
    return redirect('booking:owner_appointments_list', pk=appointment.specialist.pk)

@login_required
def client_book_appointment(request, pk):
    specialist = get_object_or_404(Specialist, pk=pk)
    try:
        client = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        return redirect('accounts:profile')

    date_str = request.GET.get('date')
    selected_date = parse_date(date_str) if date_str else date.today()

    availabilities = Availability.objects.filter(
        specialist=specialist,
        date=selected_date,
        appointments__isnull=True
    ).order_by('start_time')

    if request.method == 'POST':
        availability_id = request.POST.get('availability')
        availability = get_object_or_404(Availability, pk=availability_id, specialist=specialist)
        if Appointment.objects.filter(availability=availability).exists():
            return render(request, 'booking/client_book_appointment.html', {
                'specialist': specialist,
                'availabilities': availabilities,
                'selected_date': selected_date,
                'error': 'Это время уже занято.'
            })
        form = AppointmentForm(request.POST, specialist=specialist)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = client
            appointment.specialist = specialist
            appointment.availability = availability
            appointment.save()
            return redirect('booking:client_my_appointments')
    else:
        form = AppointmentForm(specialist=specialist)

    return render(request, 'booking/client_book_appointment.html', {
        'specialist': specialist,
        'availabilities': availabilities,
        'selected_date': selected_date,
        'form': form,
    })

@login_required
def client_my_appointments(request):
    try:
        client = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        return redirect('accounts:profile')

    appointments = client.appointments.all().order_by('availability__date', 'availability__start_time')
    return render(request, 'booking/client_my_appointments.html', {
        'appointments': appointments,
    })

@login_required
def client_cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    try:
        client = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        return redirect('accounts:profile')
    if appointment.client != client:
        return redirect('booking:client_my_appointments')
    if appointment.availability.date >= date.today():
        appointment.status = 'cancelled'
        appointment.save()
    return redirect('booking:client_my_appointments')