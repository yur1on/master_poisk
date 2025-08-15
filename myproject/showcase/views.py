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

# Настройка логирования
logger = logging.getLogger(__name__)


@login_required
def edit_showcase(request):
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        logger.error(f"WorkshopProfile не найден для пользователя {request.user.username}")
        return redirect('accounts:profile')

    showcase, created = Showcase.objects.get_or_create(workshop=workshop)
    if request.method == 'POST':
        form = ShowcaseForm(request.POST, request.FILES, instance=showcase)
        if form.is_valid():
            logger.info(f"Форма валидна для пользователя {request.user.username}")
            form.save()
            logger.info(f"Витрина успешно сохранена для пользователя {request.user.username}")
            return redirect('showcase:view_showcase', username=request.user.username)
        else:
            logger.error(f"Ошибки формы: {form.errors}")
    else:
        form = ShowcaseForm(instance=showcase)

    return render(request, 'showcase/edit_showcase.html', {'form': form})


def view_showcase(request, username):
    user = get_object_or_404(User, username=username)
    is_owner = request.user.is_authenticated and request.user == user
    try:
        workshop = user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        logger.error(f"WorkshopProfile не найден для пользователя {username}")
        return render(request, 'showcase/not_found.html', {'username': username})

    try:
        showcase = workshop.showcase
    except Showcase.DoesNotExist:
        if is_owner:
            logger.warning(f"Витрина не найдена для пользователя {username}, перенаправление на редактирование")
            return redirect('showcase:edit_showcase')
        logger.error(f"Витрина не найдена для пользователя {username}")
        return render(request, 'showcase/not_found.html', {'username': username})

    gallery = showcase.gallery_images.all()
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

    if request.method == 'POST':
        upload_form = GalleryImageForm(request.POST, request.FILES)
        if upload_form.is_valid():
            gallery_image = upload_form.save(commit=False)
            gallery_image.showcase = showcase
            gallery_image.save()
            logger.info(f"Изображение галереи успешно загружено для пользователя {username}")
            return redirect('showcase:view_showcase', username=username)
        else:
            logger.error(f"Ошибки формы загрузки изображения: {upload_form.errors}")
    else:
        upload_form = GalleryImageForm()

    return render(request, 'showcase/view_showcase.html', {
        'workshop': workshop,
        'showcase': showcase,
        'gallery': gallery,
        'is_owner': is_owner,
        'grouped_prices': grouped_prices,
        'upload_form': upload_form
    })


@login_required
@require_POST
def delete_image(request, image_id):
    try:
        image = get_object_or_404(GalleryImage, id=image_id)
        if image.showcase.workshop.user == request.user:
            image.delete()
            logger.info(f"Изображение {image_id} удалено пользователем {request.user.username}")
            return JsonResponse({'success': True})
        logger.warning(f"Попытка удаления изображения {image_id} неавторизованным пользователем {request.user.username}")
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    except Exception as e:
        logger.error(f"Ошибка при удалении изображения {image_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)