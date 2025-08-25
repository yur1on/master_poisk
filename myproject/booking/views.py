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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.db.models import Q

from .models import Availability, Appointment
from .forms import AvailabilityFormSet
from accounts.models import WorkshopProfile, ServicePrice
from showcase.models import Specialist

logger = logging.getLogger(__name__)

# helper
def times_overlap(start1, end1, start2, end2):
    """
    True если интервалы (start1,end1) и (start2,end2) пересекаются.
    Ожидаем объекты datetime.time (или совместимые для сравнения).
    Пересечение определяем как: start1 < end2 and start2 < end1
    """
    return (start1 < end2) and (start2 < end1)


@login_required
def owner_schedule_manage(request, pk):
    """
    Управление расписанием: formset + календарь + проверка перекрытий.
    """
    specialist = get_object_or_404(Specialist, pk=pk)
    if specialist.showcase.workshop.user != request.user:
        messages.error(request, "Нет доступа.")
        return redirect('booking:owner_specialists_list')

    workshop = specialist.showcase.workshop

    # месяц в формате YYYY-MM (если нет — текущий)
    month_q = request.GET.get('month')
    if month_q:
        try:
            year, month = map(int, month_q.split('-'))
        except Exception:
            year, month = date.today().year, date.today().month
    else:
        year, month = date.today().year, date.today().month

    # selected_date (опционально)
    date_str = request.GET.get('date')
    selected_date = parse_date(date_str) if date_str else None

    # границы месяца
    first_day = date(year, month, 1)
    last_day = first_day + timedelta(days=calendar.monthrange(year, month)[1] - 1)

    # Availabilities за месяц (владелец видит все)
    avail_month_qs = Availability.objects.filter(
        specialist=specialist,
        date__range=(first_day, last_day)
    ).order_by('date', 'start_time')

    # calendar matrix
    cal = calendar.Calendar(firstweekday=0)
    month_days_matrix = list(cal.monthdayscalendar(year, month))
    month_name = calendar.month_name[month]

    # slots_by_day/counts
    slots_by_day = {}
    for a in avail_month_qs:
        slots_by_day.setdefault(a.date.day, []).append(a)
    month_days_count = calendar.monthrange(year, month)[1]
    day_counts = {d: len(slots_by_day.get(d, [])) for d in range(1, month_days_count + 1)}

    # availabilities for selected date (to show under calendar)
    if selected_date:
        availabilities_day = avail_month_qs.filter(date=selected_date).order_by('start_time')
    else:
        availabilities_day = []

    # FORMSET handling
    if request.method == 'POST':
        formset = AvailabilityFormSet(request.POST, queryset=avail_month_qs)
        # ограничим сервисы этой студии
        for f in formset.forms:
            try:
                f.fields['service'].queryset = ServicePrice.objects.filter(workshop=workshop)
            except Exception:
                pass

        if formset.is_valid():
            # получаем формы, помеченные на удаление — их pk нужно исключить при проверке перекрытий
            deleted_forms = getattr(formset, 'deleted_forms', [])
            deleted_pks = [f.instance.pk for f in deleted_forms if getattr(f.instance, 'pk', None)]

            # подготовим быстрый доступ к существующим интервалам в БД по дате
            # dict: date -> list of (start_time, end_time, pk)
            db_intervals_by_date = {}
            # берем авалы за те даты, которые упоминаются в formset, чтобы не делать много запросов
            dates_in_forms = set()
            for f in formset.forms:
                cd = f.cleaned_data if hasattr(f, 'cleaned_data') else {}
                if not cd:
                    continue
                if cd.get('DELETE'):
                    continue
                d = cd.get('date')
                if d:
                    dates_in_forms.add(d)

            if dates_in_forms:
                q = Q(specialist=specialist, date__in=list(dates_in_forms))
                # исключаем те, которые помечены для удаления
                if deleted_pks:
                    q &= ~Q(pk__in=deleted_pks)
                existing = Availability.objects.filter(q).order_by('date', 'start_time')
                for a in existing:
                    db_intervals_by_date.setdefault(a.date, []).append((a.start_time, a.end_time, a.pk))

            # соберём новые интервалы из formset (для проверки пересечений между формами)
            new_intervals_by_date = {}  # date -> list of (start, end, form_index)
            has_errors = False

            # Проверяем каждую форму
            for idx, form in enumerate(formset.forms):
                cd = form.cleaned_data if hasattr(form, 'cleaned_data') else {}
                # игнорируем формы помеченные на удаление
                if not cd or cd.get('DELETE'):
                    continue

                d = cd.get('date')
                st = cd.get('start_time')
                et = cd.get('end_time')

                # базовые проверки
                if not d or not st or not et:
                    # если каких-то полей нет — добавляем ошибку
                    form.add_error(None, "Дата, время начала и конца обязательны.")
                    has_errors = True
                    continue

                if not (st < et):
                    form.add_error('start_time', "Время начала должно быть раньше времени окончания.")
                    form.add_error('end_time', "Время окончания должно быть позже времени начала.")
                    has_errors = True
                    continue

                # 1) проверка с существующими интервальными в БД на ту же дату
                db_intervals = db_intervals_by_date.get(d, [])
                for db_st, db_et, db_pk in db_intervals:
                    # если форма редактирует ту же запись (instance.pk), то пропускаем сравнение с самим собой
                    inst_pk = getattr(form.instance, 'pk', None)
                    if inst_pk and db_pk == inst_pk:
                        continue
                    if times_overlap(st, et, db_st, db_et):
                        form.add_error('start_time', f"Пересекается с существующим слотом {db_st.strftime('%H:%M')}–{db_et.strftime('%H:%M')}.")
                        form.add_error('end_time', f"Пересекается с существующим слотом {db_st.strftime('%H:%M')}–{db_et.strftime('%H:%M')}.")
                        has_errors = True
                        break
                if has_errors:
                    # не продолжаем дополнительные проверки для этой формы
                    continue

                # 2) проверка между формами в этом formset (чтобы не добавить два пересекающихся новых/изменённых слота)
                li = new_intervals_by_date.setdefault(d, [])
                # сравниваем со всеми уже добавленными в li
                for other_st, other_et, other_idx in li:
                    if times_overlap(st, et, other_st, other_et):
                        # добавляем ошибку и обеим формам (если хотим — только текущей)
                        form.add_error('start_time', "Пересекается с другим слотом, указанным в этой форме.")
                        form.add_error('end_time', "Пересекается с другим слотом, указанным в этой форме.")
                        # пометим ошибку и у формы-источника (other_idx)
                        other_form = formset.forms[other_idx]
                        other_form.add_error('start_time', "Пересекается с другим слотом, указанным в этой форме.")
                        other_form.add_error('end_time', "Пересекается с другим слотом, указанным в этой форме.")
                        has_errors = True
                        break

                # если ошибок нет — добавляем текущую форму в список новых
                li.append((st, et, idx))

            if has_errors:
                # есть ошибки — рендерим страницу с formset (ошибки уже добавлены)
                messages.error(request, "Найдены пересечения слотов — исправьте, пожалуйста.")
                context = {
                    'specialist': specialist,
                    'formset': formset,
                    'month': f'{year}-{month:02d}',
                    'availabilities': avail_month_qs,
                    'month_days_matrix': month_days_matrix,
                    'day_counts': day_counts,
                    'month_name': month_name,
                    'year': year,
                    'month_num': month,
                    'selected_date': selected_date,
                    'availabilities_day': availabilities_day,
                    'weekdays': ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
                }
                return render(request, 'booking/owner_schedule_manage.html', context)

            # если ошибок не найдено — сохраняем (как раньше)
            instances = formset.save(commit=False)
            for instance in instances:
                instance.specialist = specialist
                instance.save()
            # удаляем отмеченные
            for instance in formset.deleted_objects:
                instance.delete()
            messages.success(request, "Расписание сохранено.")
            return redirect('booking:owner_schedule_manage', pk=pk)
        else:
            # formset невалиден — покажем ошибки
            messages.error(request, "Есть ошибки в заполненных формах. Исправьте их.")
    else:
        formset = AvailabilityFormSet(queryset=avail_month_qs)
        for f in formset.forms:
            try:
                f.fields['service'].queryset = ServicePrice.objects.filter(workshop=workshop)
            except Exception:
                pass

    context = {
        'specialist': specialist,
        'formset': formset,
        'month': f'{year}-{month:02d}',
        'availabilities': avail_month_qs,
        'month_days_matrix': month_days_matrix,
        'day_counts': day_counts,
        'month_name': month_name,
        'year': year,
        'month_num': month,
        'selected_date': selected_date,
        'availabilities_day': availabilities_day,
        'weekdays': ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    }
    return render(request, 'booking/owner_schedule_manage.html', context)

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


# -------------------------
# Client (календарь + запись + список своих записей)
# -------------------------
MONTHS_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

@login_required
def client_book_appointment(request, pk):
    specialist = get_object_or_404(Specialist, pk=pk)

    # Проверка клиентского профиля
    try:
        client = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        messages.error(request, "Клиентский профиль не найден. Пожалуйста, заполните профиль.")
        return redirect('accounts:profile')

    # получаем выбранную дату
    date_str = request.GET.get('date')
    selected_date = parse_date(date_str) if date_str else date.today()

    # месяц для календаря
    month_q = request.GET.get('month')
    if month_q:
        try:
            year_m, month_m = map(int, month_q.split('-'))
        except Exception:
            year_m, month_m = selected_date.year, selected_date.month
    else:
        year_m, month_m = selected_date.year, selected_date.month

    # матрица дней месяца
    cal = calendar.Calendar(firstweekday=0)
    month_days_matrix = list(cal.monthdayscalendar(year_m, month_m))
    month_name = MONTHS_RU[month_m] if 1 <= month_m <= 12 else calendar.month_name[month_m]

    # все доступные слоты за месяц (исключая pending/confirmed)
    avail_month_qs = Availability.objects.filter(
        specialist=specialist,
        date__year=year_m,
        date__month=month_m
    ).exclude(appointments__status__in=['pending', 'confirmed']).order_by('date', 'start_time')

    slots_by_day = {}
    for a in avail_month_qs:
        d = a.date.day
        slots_by_day.setdefault(d, []).append(a)

    month_days_count = calendar.monthrange(year_m, month_m)[1]
    day_counts = {day: len(slots_by_day.get(day, [])) for day in range(1, month_days_count + 1)}

    availabilities = Availability.objects.filter(
        specialist=specialist,
        date=selected_date
    ).exclude(appointments__status__in=['pending', 'confirmed']).order_by('start_time')

    # POST - запись
    if request.method == 'POST':
        availability_id = request.POST.get('availability')
        availability = get_object_or_404(Availability, pk=availability_id, specialist=specialist)

        if Appointment.objects.filter(availability=availability, status__in=['pending', 'confirmed']).exists():
            form = AppointmentForm()
            context = {
                'specialist': specialist,
                'month_days_matrix': month_days_matrix,
                'month_name': month_name,
                'year': year_m,
                'month': month_m,
                'slots_by_day': slots_by_day,
                'day_counts': day_counts,
                'selected_date': selected_date,
                'availabilities': availabilities,
                'form': form,
                'error': 'Это время уже занято.',
                'today': date.today().isoformat(),
                'weekdays': ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
            }
            return render(request, 'booking/client_book_appointment.html', context)

        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = client
            appointment.specialist = specialist
            appointment.availability = availability
            appointment.service = availability.service
            appointment.save()
            messages.success(request, "Вы успешно записаны. Ожидайте подтверждения.")
            return redirect('booking:client_my_appointments')
    else:
        form = AppointmentForm()

    context = {
        'specialist': specialist,
        'month_days_matrix': month_days_matrix,
        'month_name': month_name,
        'year': year_m,
        'month': month_m,
        'slots_by_day': slots_by_day,
        'day_counts': day_counts,
        'selected_date': selected_date,
        'availabilities': availabilities,
        'form': form,
        'today': date.today().isoformat(),
        'weekdays': ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
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
