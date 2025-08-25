# booking/views.py
from datetime import date, timedelta
import calendar
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.contrib import messages

from .models import Availability, Appointment
from .forms import AvailabilityFormSet, AppointmentForm
from accounts.models import WorkshopProfile, ClientProfile, ServicePrice
from showcase.models import Specialist, Showcase

logger = logging.getLogger(__name__)

# -------------------------
# Owner (управление расписанием и записями)
# -------------------------
@login_required
def owner_specialists_list(request):
    try:
        workshop = request.user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        messages.error(request, "Профиль студии или витрина не найдены.")
        return redirect('accounts:profile')

    specialists = showcase.specialists.filter(is_active=True)
    return render(request, 'booking/owner_specialists_list.html', {
        'specialists': specialists,
        'workshop': workshop,
    })


# booking/views.py (обновлённая owner_schedule_manage)
from datetime import date, timedelta
import calendar
from django.utils.dateparse import parse_date

# booking/views.py (обновлённый owner_schedule_manage с проверкой пересечений)
from datetime import date, timedelta
import calendar
import logging



logger = logging.getLogger(__name__)

# helper
# booking/views.py (замените существующую owner_schedule_manage этим кодом)

from datetime import date, timedelta
import calendar
import logging



logger = logging.getLogger(__name__)

from datetime import date, timedelta
import calendar
import logging


from .forms import AvailabilityFormSet, AppointmentForm
from accounts.models import ClientProfile, ServicePrice, WorkshopProfile
from showcase.models import Specialist

logger = logging.getLogger(__name__)

from datetime import date, timedelta
import calendar
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Availability, Appointment
from .forms import AvailabilityFormSet, AppointmentForm
from accounts.models import ClientProfile, ServicePrice
from showcase.models import Specialist

logger = logging.getLogger(__name__)

def times_overlap(start1, end1, start2, end2):
    return (start1 < end2) and (start2 < end1)

@login_required
def owner_schedule_manage(request, pk):
    specialist = get_object_or_404(Specialist, pk=pk)

    # определяем владельца студии
    is_owner = False
    try:
        is_owner = (specialist.showcase.workshop.user == request.user)
    except Exception:
        is_owner = False

    # месяц в формате YYYY-MM (если нет — текущий)
    month_q = request.GET.get('month')
    if month_q:
        try:
            year, month = map(int, month_q.split('-'))
        except Exception:
            year, month = date.today().year, date.today().month
    else:
        year, month = date.today().year, date.today().month

    # выбранная дата ?date=YYYY-MM-DD
    date_str = request.GET.get('date')
    selected_date = parse_date(date_str) if date_str else None

    # границы месяца
    first_day = date(year, month, 1)
    last_day = first_day + timedelta(days=calendar.monthrange(year, month)[1] - 1)

    # все Availabilities за месяц
    avail_month_qs = (
        Availability.objects
        .filter(specialist=specialist, date__range=(first_day, last_day))
        .order_by("date", "start_time")
    )

    # все Appointments за месяц (берём select_related для эффективности)
    appts_month_qs = (
        Appointment.objects
        .filter(specialist=specialist, availability__date__range=(first_day, last_day))
        .select_related("client__user", "availability", "service")
        .order_by("availability__date", "availability__start_time")
    )

    # календарная матрица
    cal = calendar.Calendar(firstweekday=0)
    month_days_matrix = list(cal.monthdayscalendar(year, month))
    month_name = calendar.month_name[month]

    # строим словари:
    # - free_slots_by_day: свободные слоты (availability без pending/confirmed)
    # - appts_by_day: записи pending/confirmed
    free_slots_by_day = {}
    for a in avail_month_qs:
        if not Appointment.objects.filter(
            availability=a,
            status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
        ).exists():
            free_slots_by_day.setdefault(a.date.day, []).append(a)

    appts_by_day = {}
    for ap in appts_month_qs:
        if ap.status in [Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]:
            d = ap.availability.date.day
            appts_by_day.setdefault(d, []).append(ap)

    # строим day_counts на основе свободных слотов и записей
    month_days_count = calendar.monthrange(year, month)[1]
    day_counts = {
        d: {
            "slots": len(free_slots_by_day.get(d, [])),
            "appts": len(appts_by_day.get(d, []))
        }
        for d in range(1, month_days_count + 1)
    }

    # Слоты и записи на выбранную дату:
    if selected_date:
        # свободные availabilities (без pending/confirmed)
        availabilities_day = avail_month_qs.filter(date=selected_date).exclude(
            appointments__status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
        ).order_by("start_time")

        # только активные записи (pending/confirmed)
        appointments_day = appts_month_qs.filter(
            availability__date=selected_date,
            status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
        )
    else:
        availabilities_day = []
        appointments_day = []

    # --- далее код обработки POST (назначение клиента, редактирование formset и запись клиента) ---
    if request.method == "POST":
        # владелец назначает клиента на слот
        if is_owner and request.POST.get("owner_assign_submit"):
            availability_id = request.POST.get("availability_id")
            client_name = request.POST.get("client_name", "").strip()
            client_phone = request.POST.get("client_phone", "").strip()
            client_city = request.POST.get("client_city", "").strip()
            notes = request.POST.get("notes", "").strip()

            if not availability_id or not client_name or not client_phone:
                messages.error(request, "Пожалуйста, заполните имя и телефон клиента.")
            else:
                try:
                    # ищем клиента по телефону, либо создаём
                    client = ClientProfile.objects.filter(phone=client_phone).first()
                    if not client:
                        # создаём User с username=телефон (уникальный)
                        base_username = client_phone
                        username = base_username
                        counter = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}_{counter}"
                            counter += 1
                        user = User.objects.create_user(username=username, password=None)
                        client = ClientProfile.objects.create(
                            user=user,
                            name=client_name,
                            phone=client_phone,
                            city=client_city
                        )

                    # проверяем, что слот свободен
                    availability = get_object_or_404(Availability, pk=availability_id, specialist=specialist)
                    if Appointment.objects.filter(
                        availability=availability,
                        status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
                    ).exists():
                        messages.error(request, "Этот слот уже занят.")
                    else:
                        Appointment.objects.create(
                            client=client,
                            specialist=specialist,
                            availability=availability,
                            service=availability.service,
                            notes=notes,
                            status=Appointment.STATUS_CONFIRMED
                        )
                        messages.success(request, "Запись добавлена.")
                except Exception as e:
                    logger.error(f"Ошибка при назначении клиента: {e}")
                    messages.error(request, "Произошла ошибка при добавлении записи.")

            # перенаправляем на текущий месяц и дату
            date_param = selected_date.isoformat() if selected_date else ""
            return redirect(f"{request.path}?month={year:04d}-{month:02d}&date={date_param}")

        # владелец редактирует formset
        elif is_owner and "formset_submit" in request.POST:
            formset = AvailabilityFormSet(request.POST, queryset=avail_month_qs)
            # фильтруем услуги по студии
            workshop = specialist.showcase.workshop
            for f in formset.forms:
                try:
                    f.fields["service"].queryset = ServicePrice.objects.filter(workshop=workshop)
                except Exception:
                    pass

            if formset.is_valid():
                # проверка пересечений
                deleted_forms = getattr(formset, "deleted_forms", [])
                deleted_pks = [f.instance.pk for f in deleted_forms if getattr(f.instance, "pk", None)]

                dates_in_forms = set()
                for f in formset.forms:
                    cd = getattr(f, "cleaned_data", None)
                    if not cd or cd.get("DELETE"):
                        continue
                    d = cd.get("date")
                    if d:
                        dates_in_forms.add(d)

                # существующие интервалы в БД, исключая удалённые
                db_intervals_by_date = {}
                if dates_in_forms:
                    q = Q(specialist=specialist, date__in=list(dates_in_forms))
                    if deleted_pks:
                        q &= ~Q(pk__in=deleted_pks)
                    existing = Availability.objects.filter(q).order_by("date", "start_time")
                    for a in existing:
                        db_intervals_by_date.setdefault(a.date, []).append((a.start_time, a.end_time, a.pk))

                new_intervals_by_date = {}
                has_errors = False

                for idx, form in enumerate(formset.forms):
                    cd = getattr(form, "cleaned_data", None)
                    if not cd or cd.get("DELETE"):
                        continue
                    d = cd.get("date")
                    st = cd.get("start_time")
                    et = cd.get("end_time")
                    if not d or not st or not et:
                        form.add_error(None, "Дата, время начала и конца обязательны.")
                        has_errors = True
                        continue
                    if not (st < et):
                        form.add_error("start_time", "Время начала должно быть раньше времени окончания.")
                        form.add_error("end_time", "Время окончания должно быть позже времени начала.")
                        has_errors = True
                        continue

                    # пересечение с уже существующими слотами в БД
                    for db_st, db_et, db_pk in db_intervals_by_date.get(d, []):
                        inst_pk = getattr(form.instance, "pk", None)
                        if inst_pk and db_pk == inst_pk:
                            continue
                        if times_overlap(st, et, db_st, db_et):
                            form.add_error("start_time", f"Пересекается со слотами {db_st.strftime('%H:%M')}–{db_et.strftime('%H:%M')}.")
                            form.add_error("end_time", f"Пересекается со слотами {db_st.strftime('%H:%M')}–{db_et.strftime('%H:%M')}.")
                            has_errors = True
                            break
                    if has_errors:
                        continue

                    # пересечение между формами в formset
                    li = new_intervals_by_date.setdefault(d, [])
                    for other_st, other_et, other_idx in li:
                        if times_overlap(st, et, other_st, other_et):
                            form.add_error("start_time", "Пересекается с другим слотом в форме.")
                            form.add_error("end_time", "Пересекается с другим слотом в форме.")
                            other_form = formset.forms[other_idx]
                            other_form.add_error("start_time", "Пересекается с другим слотом в форме.")
                            other_form.add_error("end_time", "Пересекается с другим слотом в форме.")
                            has_errors = True
                            break
                    li.append((st, et, idx))

                if has_errors:
                    messages.error(request, "Найдены пересечения. Исправьте, пожалуйста.")
                else:
                    instances = formset.save(commit=False)
                    for instance in instances:
                        instance.specialist = specialist
                        instance.save()
                    for inst in formset.deleted_objects:
                        inst.delete()
                    messages.success(request, "Расписание сохранено.")
                    return redirect(f"{request.path}?month={year:04d}-{month:02d}")

            else:
                messages.error(request, "Есть ошибки в формах. Исправьте их.")

        # клиент записывается
        elif not is_owner and "book_submit" in request.POST:
            try:
                client = request.user.clientprofile
            except ClientProfile.DoesNotExist:
                messages.error(request, "Клиентский профиль не найден. Пожалуйста, заполните профиль.")
                return redirect('accounts:profile')

            availability_id = request.POST.get("availability")
            if not availability_id:
                messages.error(request, "Выберите слот.")
            else:
                availability = get_object_or_404(Availability, pk=availability_id, specialist=specialist)
                if Appointment.objects.filter(availability=availability, status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]).exists():
                    messages.error(request, "Это время уже занято.")
                else:
                    form_appt = AppointmentForm(request.POST)
                    if form_appt.is_valid():
                        appt = form_appt.save(commit=False)
                        appt.client = client
                        appt.specialist = specialist
                        appt.availability = availability
                        appt.service = availability.service
                        appt.save()
                        messages.success(request, "Вы успешно записаны. Ожидайте подтверждения.")
                        return redirect('booking:client_my_appointments')
                    else:
                        messages.error(request, "Ошибка при сохранении записи.")
            date_param = selected_date.isoformat() if selected_date else ""
            return redirect(f"{request.path}?month={year:04d}-{month:02d}&date={date_param}")

    # формируем formset для владельца
    formset = None
    if is_owner:
        formset = AvailabilityFormSet(queryset=avail_month_qs)
        workshop = specialist.showcase.workshop
        for f in formset.forms:
            try:
                f.fields["service"].queryset = ServicePrice.objects.filter(workshop=workshop)
            except Exception:
                pass

    # форма для клиента
    appt_form = None
    if not is_owner:
        appt_form = AppointmentForm()

    context = {
        "specialist": specialist,
        "is_owner": is_owner,
        "formset": formset,
        "month": f"{year:04d}-{month:02d}",
        "month_days_matrix": month_days_matrix,
        "day_counts": day_counts,
        "month_name": month_name,
        "year": year,
        "month_num": month,
        "selected_date": selected_date,
        "availabilities_day": availabilities_day,
        "appointments_day": appointments_day,
        "availabilities": avail_month_qs,
        "appts_month_qs": appts_month_qs,
        "weekdays": ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"],
        "appt_form": appt_form
    }
    return render(request, "booking/owner_schedule_manage.html", context)

# booking/views.py (только функция owner_appointments_list)
from django.db.models import Prefetch

@login_required
def owner_appointments_list(request, pk):
    """
    Показывает записи для специалиста (владелец).
    Используем select_related/prefetch, чтобы уменьшить число запросов.
    """
    specialist = get_object_or_404(Specialist, pk=pk)
    if specialist.showcase.workshop.user != request.user:
        messages.error(request, "Нет доступа.")
        return redirect('booking:owner_specialists_list')

    # Подгружаем availability и client (ClientProfile) сразу, чтобы в шаблоне не делать N дополнительных запросов
    appointments = (
        specialist.appointments
        .select_related('availability', 'service', 'client__user')  # client__user позволяет читать client.user.get_full_name
        .order_by('availability__date', 'availability__start_time')
    )

    return render(request, 'booking/owner_appointments_list.html', {
        'specialist': specialist,
        'appointments': appointments,
    })


@login_required
def owner_confirm_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.specialist.showcase.workshop.user != request.user:
        messages.error(request, "Нет доступа.")
        return redirect('accounts:profile')
    appointment.status = 'confirmed'
    appointment.save()
    messages.success(request, "Запись подтверждена.")
    return redirect('booking:owner_appointments_list', pk=appointment.specialist.pk)


@login_required
def owner_cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.specialist.showcase.workshop.user != request.user:
        messages.error(request, "Нет доступа.")
        return redirect('accounts:profile')
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, "Запись отменена.")
    return redirect('booking:owner_appointments_list', pk=appointment.specialist.pk)

# booking/views.py
from django.contrib.auth.models import User
from django.contrib import messages

@login_required
def owner_delete_appointment(request, pk):
    """
    Позволяет владельцу полностью удалить запись (после отмены).
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.specialist.showcase.workshop.user != request.user:
        messages.error(request, "Нет доступа.")
        return redirect('accounts:profile')
    appointment.delete()
    messages.success(request, "Запись удалена.")
    return redirect('booking:owner_appointments_list', pk=appointment.specialist.pk)

# -------------------------
# Client (календарь + запись + список своих записей)
# -------------------------
# booking/views.py (фрагмент)

from datetime import date
import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.contrib import messages

from .models import Availability, Appointment
from .forms import AppointmentForm
from accounts.models import ClientProfile
from showcase.models import Specialist

MONTHS_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

@login_required
def client_book_appointment(request, pk):
    """Просмотр календаря свободных слотов и запись клиента к специалисту."""
    specialist = get_object_or_404(Specialist, pk=pk)

    # Проверяем, что у пользователя есть клиентский профиль
    try:
        client = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        messages.error(request, "Клиентский профиль не найден. Пожалуйста, заполните профиль.")
        return redirect('accounts:profile')

    # Определяем выбранную дату (сегодня, если не передана)
    date_str = request.GET.get('date')
    selected_date = parse_date(date_str) if date_str else date.today()

    # Месяц и год для календаря (по умолчанию текущий месяц)
    month_q = request.GET.get('month')
    if month_q:
        try:
            year_m, month_m = map(int, month_q.split('-'))
        except Exception:
            year_m, month_m = selected_date.year, selected_date.month
    else:
        year_m, month_m = selected_date.year, selected_date.month

    # Матрица дней месяца
    cal = calendar.Calendar(firstweekday=0)
    month_days_matrix = list(cal.monthdayscalendar(year_m, month_m))
    month_name = MONTHS_RU[month_m] if 1 <= month_m <= 12 else calendar.month_name[month_m]

    # Свободные слоты за месяц (исключаем слоты с pending/confirmed записями)
    avail_month_qs = Availability.objects.filter(
        specialist=specialist,
        date__year=year_m,
        date__month=month_m
    ).exclude(
        appointments__status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
    ).order_by('date', 'start_time')

    # Подсчёт свободных слотов по дням
    slots_by_day = {}
    for a in avail_month_qs:
        d = a.date.day
        slots_by_day.setdefault(d, []).append(a)

    month_days_count = calendar.monthrange(year_m, month_m)[1]
    day_counts = {day: len(slots_by_day.get(day, [])) for day in range(1, month_days_count + 1)}

    # Свободные слоты на выбранную дату
    availabilities = Availability.objects.filter(
        specialist=specialist,
        date=selected_date
    ).exclude(
        appointments__status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
    ).order_by('start_time')

    # Обработка записи (POST)
    error = None
    if request.method == 'POST' and 'book_submit' in request.POST:
        availability_id = request.POST.get('availability')
        if not availability_id:
            messages.error(request, "Выберите слот.")
            return redirect(f'{request.path}?month={year_m}-{month_m:02d}&date={selected_date.isoformat()}')

        availability = get_object_or_404(Availability, pk=availability_id, specialist=specialist)
        # Повторно проверяем, что слот ещё свободен
        if Appointment.objects.filter(
            availability=availability,
            status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
        ).exists():
            error = "Это время уже занято."
        else:
            form = AppointmentForm(request.POST)
            if form.is_valid():
                appt = form.save(commit=False)
                appt.client = client
                appt.specialist = specialist
                appt.availability = availability
                appt.service = availability.service
                appt.save()
                messages.success(request, "Вы успешно записаны. Ожидайте подтверждения.")
                return redirect('booking:client_my_appointments')
            else:
                error = "Ошибка при заполнении формы записи."
    else:
        form = AppointmentForm()

    context = {
        'specialist': specialist,
        'month_days_matrix': month_days_matrix,
        'month_name': month_name,
        'year': year_m,
        'month': month_m,
        'day_counts': day_counts,
        'selected_date': selected_date,
        'availabilities': availabilities,
        'form': form,
        'today': date.today().isoformat(),
        'weekdays': ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        'error': error
    }
    return render(request, 'booking/client_book_appointment.html', context)


@login_required
def client_my_appointments(request):
    try:
        client = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        messages.error(request, "Клиентский профиль не найден.")
        return redirect('accounts:profile')

    appointments = client.appointments.all().order_by('availability__date', 'availability__start_time')
    return render(request, 'booking/client_my_appointments.html', {
        'appointments': appointments,
        'today': date.today().isoformat(),
    })


@login_required
def client_cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    try:
        client = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        messages.error(request, "Клиентский профиль не найден.")
        return redirect('accounts:profile')
    if appointment.client != client:
        messages.error(request, "Нет доступа.")
        return redirect('booking:client_my_appointments')
    if appointment.availability.date >= date.today():
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, "Запись отменена.")
    else:
        messages.error(request, "Нельзя отменить прошедшую запись.")
    return redirect('booking:client_my_appointments')
