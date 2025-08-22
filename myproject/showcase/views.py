from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import WorkshopProfile, ServicePrice
from .models import Showcase, GalleryImage
from .forms import ShowcaseForm, GalleryImageForm
from collections import OrderedDict
import logging
import os
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Showcase, GalleryImage, Specialist
from .forms import ShowcaseForm, GalleryImageForm, SpecialistForm
from accounts.models import WorkshopProfile, ServicePrice
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

import os
from django.conf import settings

logger = logging.getLogger(__name__)

@login_required
def edit_showcase(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        logger.error(f"WorkshopProfile не найден для пользователя {request.user.username}")
        if is_ajax:
            return JsonResponse({'success': False, 'errors': 'Workshop profile not found.'}, status=400)
        return redirect('accounts:profile')

    showcase, created = Showcase.objects.get_or_create(workshop=workshop)
    if request.method == 'POST':
        form = ShowcaseForm(request.POST, request.FILES, instance=showcase)
        if form.is_valid():
            logger.info(f"Форма валидна для пользователя {request.user.username}")
            form.save()
            logger.info(f"Витрина успешно сохранена для пользователя {request.user.username}")
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'description': form.cleaned_data['description'] or '',
                    'phone': form.cleaned_data['phone'] or '',
                    'working_hours': form.cleaned_data['working_hours'] or ''
                })
            return redirect('showcase:view_showcase', username=request.user.username)
        else:
            logger.error(f"Ошибки формы в edit_showcase: {form.errors}")
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            return render(request, 'accounts/profile.html', {
                'showcase_form': form,
                'workshop_profile': workshop,
                'is_workshop': True,
                'user': request.user
            })
    else:
        return redirect('accounts:profile')

@login_required
def upload_gallery_image(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        workshop = request.user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        logger.error(f"Workshop или showcase не найден для пользователя {request.user.username}")
        if is_ajax:
            return JsonResponse({'success': False, 'errors': 'Workshop or showcase not found.'}, status=400)
        return redirect('accounts:profile')

    if request.method == 'POST':
        upload_form = GalleryImageForm(request.POST, request.FILES)
        if upload_form.is_valid():
            gallery_image = upload_form.save(commit=False)
            gallery_image.showcase = showcase
            gallery_image.save()
            logger.info(f"Изображение галереи успешно загружено для пользователя {request.user.username}")
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'image_url': gallery_image.image.url,
                    'description': gallery_image.description or '',
                    'image_id': gallery_image.id
                })
            return redirect('showcase:view_showcase', username=request.user.username)
        else:
            logger.error(f"Ошибки формы загрузки изображения: {upload_form.errors}")
            if is_ajax:
                return JsonResponse({'success': False, 'errors': upload_form.errors.as_json()}, status=400)
            # Рендерим view_showcase.html с ошибками формы
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
            return render(request, 'showcase/view_showcase.html', {
                'workshop': workshop,
                'showcase': showcase,
                'gallery': showcase.gallery_images.all(),
                'is_owner': True,
                'grouped_prices': grouped_prices,
                'upload_form': upload_form
            })
    else:
        return redirect('showcase:view_showcase', username=request.user.username)


def view_showcase(request, username):
    user = get_object_or_404(User, username=username)
    is_owner = request.user.is_authenticated and request.user == user

    # Получаем WorkshopProfile
    try:
        workshop = user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        logger.error(f"WorkshopProfile не найден для пользователя {username}")
        return render(request, 'showcase/not_found.html', {'username': username})

    # Получаем Showcase или перенаправляем владельца на создание/редактирование
    try:
        showcase = workshop.showcase
    except Showcase.DoesNotExist:
        if is_owner:
            logger.warning(f"Витрина не найдена для пользователя {username}, перенаправление на редактирование")
            return redirect('showcase:edit_showcase')
        logger.error(f"Витрина не найдена для пользователя {username}")
        return render(request, 'showcase/not_found.html', {'username': username})

    # Галерея
    gallery = showcase.gallery_images.all()

    # Специалисты — фильтруем только активных и сортируем по полю order (и далее по фамилии/имени)
    specialists = showcase.specialists.filter(is_active=True).order_by('order', 'last_name', 'first_name')

    # Цены и группировка (как было)
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

    upload_form = GalleryImageForm()

    return render(request, 'showcase/view_showcase.html', {
        'workshop': workshop,
        'showcase': showcase,
        'gallery': gallery,
        'specialists': specialists,         # <-- добавлено
        'is_owner': is_owner,
        'grouped_prices': grouped_prices,
        'upload_form': upload_form
    })

@login_required
@require_POST
def delete_image(request, image_id):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        image = get_object_or_404(GalleryImage, id=image_id)
        if image.showcase.workshop.user != request.user:
            logger.warning(f"Попытка удаления изображения {image_id} неавторизованным пользователем {request.user.username}")
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Вы не авторизованы для удаления этого изображения'}, status=403)
            return redirect('showcase:view_showcase', username=image.showcase.workshop.user.username)

        # Удаляем изображение и связанный файл
        image_file = image.image.path
        image.delete()
        import os
        if os.path.exists(image_file):
            os.remove(image_file)
            logger.info(f"Файл изображения {image_file} удалён с диска")
        logger.info(f"Изображение {image_id} успешно удалено пользователем {request.user.username}")

        if is_ajax:
            return JsonResponse({'success': True})
        return redirect('showcase:view_showcase', username=request.user.username)
    except Exception as e:
        logger.error(f"Ошибка при удалении изображения {image_id}: {str(e)}")
        if is_ajax:
            return JsonResponse({'success': False, 'error': f'Ошибка сервера: {str(e)}'}, status=500)
        return redirect('accounts:profile')


# --- Public list/detail (публичные страницы для посетителей) ---
def specialists_list(request, username):
    """Публичная страница: список специалистов витрины пользователя"""
    user = get_object_or_404(User, username=username)
    try:
        workshop = user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        return render(request, 'showcase/not_found.html', {'username': username})

    specialists = showcase.specialists.filter(is_active=True).order_by('order', 'last_name', 'first_name')

    # пагинация (опционально)
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(specialists, 9)
    page = request.GET.get('page', 1)
    try:
        specialists_page = paginator.page(page)
    except PageNotAnInteger:
        specialists_page = paginator.page(1)
    except EmptyPage:
        specialists_page = paginator.page(paginator.num_pages)

    return render(request, 'showcase/specialists_list.html', {
        'workshop': workshop,
        'showcase': showcase,
        'specialists': specialists_page,
        'paginator': paginator,
        'page_obj': specialists_page,
        'is_owner': request.user.is_authenticated and request.user == user
    })


def specialist_detail(request, username, pk):
    """Публичная страница: подробная карточка специалиста"""
    user = get_object_or_404(User, username=username)
    try:
        workshop = user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        return render(request, 'showcase/not_found.html', {'username': username})

    specialist = get_object_or_404(Specialist, pk=pk, showcase=showcase)

    return render(request, 'showcase/specialist_detail.html', {
        'workshop': workshop,
        'showcase': showcase,
        'specialist': specialist,
        'is_owner': request.user.is_authenticated and request.user == user
    })


# --- Management (только владелец) ---
@login_required
def specialists_manage(request):
    """
    Страница управления специалистами (отдельная страница,
    доступна только владельцу WorkshopProfile).
    """
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        return redirect('accounts:profile')

    showcase, _ = Showcase.objects.get_or_create(workshop=workshop)
    specialists = showcase.specialists.all().order_by('order', 'last_name', 'first_name')
    form = SpecialistForm()
    return render(request, 'showcase/specialists_manage.html', {
        'workshop': workshop,
        'showcase': showcase,
        'specialists': specialists,
        'form': form,
        'is_owner': True
    })


@login_required
@require_POST
def specialist_create(request):
    """Создать специалиста (POST). Возвращает JSON при AJAX, иначе редирект."""
    try:
        workshop = request.user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Workshop not found'}, status=400)
        return redirect('accounts:profile')

    form = SpecialistForm(request.POST, request.FILES)
    if form.is_valid():
        spec = form.save(commit=False)
        spec.showcase = showcase
        spec.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'id': spec.id,
                'first_name': spec.first_name,
                'last_name': spec.last_name,
                'position': spec.position,
                'photo_url': spec.photo.url if spec.photo else '',
                'phone': spec.phone,
                'bio': spec.bio,
                'is_active': spec.is_active,
                'order': spec.order
            })
        return redirect('showcase:specialists_manage')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        # при обычном POST — отобразим форму со ошибками
        specialists = showcase.specialists.all().order_by('order')
        return render(request, 'showcase/specialists_manage.html', {
            'workshop': workshop,
            'showcase': showcase,
            'specialists': specialists,
            'form': form,
            'is_owner': True
        })


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseForbidden
from .models import Specialist
from .forms import SpecialistForm


@login_required
def specialist_edit(request, pk):
    """
    Редактирование специалиста.
    - GET → отрисовывает форму редактирования
    - POST → сохраняет изменения
    - Если запрос AJAX → возвращает JSON
    """
    spec = get_object_or_404(Specialist, pk=pk)

    # проверка прав
    if spec.showcase.workshop.user != request.user:
        return HttpResponseForbidden('Нет доступа')

    form = SpecialistForm(request.POST or None, request.FILES or None, instance=spec)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': spec.pk})
            return redirect('showcase:specialists_manage')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # GET или невалидная форма (обычный рендер)
    return render(request, 'showcase/specialist_edit.html', {
        'form': form,
        'specialist': spec,
        'is_owner': True,
    })

from django.contrib import messages

@login_required
@require_POST
def specialist_delete(request, pk):
    """Удаление специалиста через POST, с редиректом."""
    spec = get_object_or_404(Specialist, pk=pk)
    if spec.showcase.workshop.user != request.user:
        messages.error(request, "Нет доступа")
        return redirect('showcase:view_showcase', username=spec.showcase.workshop.user.username)

    try:
        photo_path = spec.photo.path if spec.photo else None
        spec.delete()
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
        messages.success(request, "Специалист успешно удалён")
        return redirect('showcase:view_showcase', username=request.user.username)
    except Exception as e:
        logger.error(f"Ошибка при удалении специалиста {pk}: {e}")
        messages.error(request, "Ошибка сервера")
        return redirect('showcase:view_showcase', username=request.user.username)
