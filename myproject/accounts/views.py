from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import ClientRegisterForm, WorkshopRegisterForm, ClientProfileForm, WorkshopProfileForm, ServicePriceFormSet
from .models import ClientProfile, WorkshopProfile, ServicePrice
from showcase.models import Showcase, GalleryImage
from showcase.forms import ShowcaseForm, GalleryImageForm
from collections import OrderedDict
from django.db import IntegrityError
from django.contrib.staticfiles import finders
import json
import logging

logger = logging.getLogger(__name__)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main:home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            try:
                user.workshopprofile
                return redirect('showcase:view_showcase', username=user.username)
            except WorkshopProfile.DoesNotExist:
                try:
                    user.clientprofile
                    return redirect('accounts:profile')
                except ClientProfile.DoesNotExist:
                    pass
            return redirect('main:home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('main:home')

def select_user_type(request):
    return render(request, 'accounts/select_user_type.html')

def register_client(request):
    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                if not ClientProfile.objects.filter(user=user).exists():
                    ClientProfile.objects.create(
                        user=user,
                        name=form.cleaned_data['name'],
                        phone=form.cleaned_data['phone'],
                        city=form.cleaned_data['city']
                    )
                login(request, user)
                return redirect('accounts:profile')
            except IntegrityError:
                form.add_error(None, "Пользователь с таким именем уже существует.")
    else:
        form = ClientRegisterForm()
    return render(request, 'accounts/register_client.html', {'form': form})

def register_workshop(request):
    if request.method == 'POST':
        form = WorkshopRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('showcase:view_showcase', username=user.username)
    else:
        form = WorkshopRegisterForm()
    return render(request, 'accounts/register_workshop.html', {'form': form})

@login_required
def profile_view(request):
    client_profile = None
    workshop_profile = None
    is_client = False
    is_workshop = False
    grouped_activities = {}
    client_form = None
    workshop_form = None
    formset = None
    showcase_form = None
    upload_form = None
    showcase = None
    gallery = None
    grouped_prices = OrderedDict()

    try:
        client_profile = request.user.clientprofile
        is_client = True
        client_form = ClientProfileForm(instance=client_profile, initial={'email': request.user.email})
    except ClientProfile.DoesNotExist:
        try:
            workshop_profile = request.user.workshopprofile
            is_workshop = True
            workshop_form = WorkshopProfileForm(instance=workshop_profile, initial={'email': request.user.email})
            json_path = finders.find('services.json')
            if not json_path:
                logger.error("Файл services.json не найден")
                return JsonResponse({'success': False, 'errors': 'Service list not found.'}, status=500) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('accounts:profile')
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    services_data = json.load(f)
                service_map = {item['code']: item['works'] for item in services_data}
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования services.json: {str(e)}")
                return JsonResponse({'success': False, 'errors': 'Invalid services.json format.'}, status=500) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('accounts:profile')
            activity_codes = {str(area.id): area.code for area in workshop_profile.activity_area.all()}
            formset = ServicePriceFormSet(
                queryset=ServicePrice.objects.filter(workshop=workshop_profile),
                form_kwargs={'workshop': workshop_profile}
            )
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
            grouped_activities = OrderedDict()
            for activity in workshop_profile.activity_area.all():
                cat = CATEGORY_TRANSLATIONS.get(activity.category, activity.get_category_display())
                grouped_activities.setdefault(cat, []).append(activity)
            prices = ServicePrice.objects.filter(workshop=workshop_profile)
            for price in prices:
                cat = CATEGORY_TRANSLATIONS.get(price.activity_area.category, price.activity_area.get_category_display())
                grouped_prices.setdefault(cat, []).append(price)
            showcase, created = Showcase.objects.get_or_create(workshop=workshop_profile)
            showcase_form = ShowcaseForm(instance=showcase)
            upload_form = GalleryImageForm()
            gallery = showcase.gallery_images.all()
        except WorkshopProfile.DoesNotExist:
            pass

    return render(request, 'accounts/profile.html', {
        'client_profile': client_profile,
        'workshop_profile': workshop_profile,
        'is_client': is_client,
        'is_workshop': is_workshop,
        'grouped_activities': grouped_activities,
        'user': request.user,
        'client_form': client_form,
        'workshop_form': workshop_form,
        'formset': formset,
        'service_map': service_map if is_workshop else {},
        'activity_codes': activity_codes if is_workshop else {},
        'showcase_form': showcase_form,
        'upload_form': upload_form,
        'showcase': showcase,
        'gallery': gallery,
        'grouped_prices': grouped_prices
    })

@login_required
def edit_profile(request):
    user = request.user
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST':
        try:
            client_profile = user.clientprofile
            form = ClientProfileForm(request.POST, instance=client_profile)
            if form.is_valid():
                client_profile = form.save()
                user.email = form.cleaned_data['email']
                user.save()
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'name': client_profile.name,
                        'email': user.email,
                        'phone': client_profile.phone,
                        'city': client_profile.city or ''
                    })
                return redirect('accounts:profile')
            else:
                logger.error(f"Ошибки формы в edit_profile (client): {form.errors}")
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
                return render(request, 'accounts/profile.html', {
                    'client_form': form,
                    'is_client': True,
                    'user': user
                })
        except ClientProfile.DoesNotExist:
            try:
                workshop_profile = user.workshopprofile
                form = WorkshopProfileForm(request.POST, instance=workshop_profile)
                if form.is_valid():
                    workshop_profile = form.save(commit=False)
                    user.email = form.cleaned_data['email']
                    user.save()
                    workshop_profile.save()
                    form.save_m2m()
                    if is_ajax:
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
                        grouped_activities = OrderedDict()
                        for activity in workshop_profile.activity_area.all():
                            cat = CATEGORY_TRANSLATIONS.get(activity.category, activity.get_category_display())
                            grouped_activities.setdefault(cat, []).append(activity)
                        activities_html = ''
                        for category, activities in grouped_activities.items():
                            activities_html += f'<h5>{category}</h5><ul class="activity-list">'
                            for activity in activities:
                                activities_html += f'<li>{activity.name}</li>'
                            activities_html += '</ul>'
                        return JsonResponse({
                            'success': True,
                            'workshop_name': workshop_profile.workshop_name,
                            'workshop_address': workshop_profile.workshop_address,
                            'city': workshop_profile.city or '',
                            'email': user.email,
                            'phone': workshop_profile.phone,
                            'description': workshop_profile.description or '',
                            'working_hours': workshop_profile.working_hours or '',
                            'activities_html': activities_html
                        })
                    return redirect('accounts:profile')
                else:
                    logger.error(f"Ошибки формы в edit_profile (workshop): {form.errors}")
                    if is_ajax:
                        return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
                    return render(request, 'accounts/profile.html', {
                        'workshop_form': form,
                        'is_workshop': True,
                        'user': user,
                        'grouped_activities': grouped_activities
                    })
            except WorkshopProfile.DoesNotExist:
                logger.error(f"Профиль не найден для пользователя {user.username}")
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': 'Profile not found.'}, status=400)
                return redirect('main:home')
        except Exception as e:
            logger.error(f"Неожиданная ошибка в edit_profile: {str(e)}")
            if is_ajax:
                return JsonResponse({'success': False, 'errors': str(e)}, status=500)
            return redirect('main:home')
    else:
        return redirect('accounts:profile')

@login_required
def edit_prices(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        logger.error(f"WorkshopProfile не найден для пользователя {request.user.username}")
        if is_ajax:
            return JsonResponse({'success': False, 'errors': 'Workshop profile not found.'}, status=400)
        return redirect('accounts:profile')

    try:
        json_path = finders.find('services.json')
        if not json_path:
            logger.error("Файл services.json не найден")
            if is_ajax:
                return JsonResponse({'success': False, 'errors': 'Service list not found.'}, status=500)
            return redirect('accounts:profile')
        with open(json_path, 'r', encoding='utf-8') as f:
            services_data = json.load(f)
        service_map = {item['code']: item['works'] for item in services_data}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования services.json: {str(e)}")
        if is_ajax:
            return JsonResponse({'success': False, 'errors': 'Invalid services.json format.'}, status=500)
        return redirect('accounts:profile')

    activity_codes = {str(area.id): area.code for area in workshop.activity_area.all()}

    if request.method == 'POST':
        formset = ServicePriceFormSet(
            request.POST,
            queryset=ServicePrice.objects.filter(workshop=workshop),
            form_kwargs={'workshop': workshop}
        )
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.workshop = workshop
                instance.save()
            for instance in formset.deleted_objects:
                instance.delete()
            if is_ajax:
                prices = ServicePrice.objects.filter(workshop=workshop)
                grouped_prices = OrderedDict()
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
                for price in prices:
                    cat = CATEGORY_TRANSLATIONS.get(price.activity_area.category, price.activity_area.get_category_display())
                    grouped_prices.setdefault(cat, []).append(price)
                prices_html = ''
                for category, prices in grouped_prices.items():
                    prices_html += f'<h5>{category}</h5><table class="price-table"><thead><tr><th>Услуга</th><th>Цена (руб.)</th><th>Длительность</th></tr></thead><tbody>'
                    for price in prices:
                        prices_html += f'<tr><td>{price.service_name}</td><td>{price.price}</td><td>{price.duration or "Не указано"}</td></tr>'
                    prices_html += '</tbody></table>'
                return JsonResponse({
                    'success': True,
                    'prices_html': prices_html
                })
            return redirect('accounts:profile')
        else:
            logger.error(f"Ошибки формсета в edit_prices: {formset.errors}, {formset.non_form_errors}")
            if is_ajax:
                return JsonResponse({'success': False, 'errors': formset.errors.as_json()}, status=400)
            return render(request, 'accounts/profile.html', {
                'formset': formset,
                'service_map': service_map,
                'activity_codes': activity_codes,
                'workshop_profile': workshop,
                'is_workshop': True,
                'user': request.user
            })
    else:
        return redirect('accounts:profile')