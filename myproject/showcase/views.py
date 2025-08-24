# showcase/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from collections import OrderedDict
import logging
import os

from .models import Showcase, GalleryImage, Specialist
from .forms import ShowcaseForm, GalleryImageForm, SpecialistForm
from accounts.models import WorkshopProfile, ServicePrice
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@login_required
def edit_showcase(request):
    """Редактирование/создание витрины владельцем студии."""
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        messages.error(request, "Профиль студии не найден.")
        return redirect('accounts:profile')

    showcase, created = Showcase.objects.get_or_create(workshop=workshop)

    if request.method == 'POST':
        form = ShowcaseForm(request.POST, request.FILES, instance=showcase)
        if form.is_valid():
            form.save()
            messages.success(request, "Витрина сохранена.")
            return redirect('showcase:view_showcase', username=request.user.username)
        else:
            messages.error(request, "Ошибка в форме. Исправьте и попробуйте снова.")
    else:
        form = ShowcaseForm(instance=showcase)

    return render(request, 'showcase/edit_showcase.html', {
        'form': form,
        'workshop': workshop,
        'showcase': showcase,
        'is_owner': True
    })


@login_required
@require_POST
def upload_gallery_image(request):
    """Загрузка изображения в галерею витрины."""
    try:
        workshop = request.user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        messages.error(request, "Витрина не найдена.")
        return redirect('accounts:profile')

    form = GalleryImageForm(request.POST, request.FILES)
    if form.is_valid():
        gi = form.save(commit=False)
        gi.showcase = showcase
        gi.save()
        messages.success(request, "Изображение добавлено.")
    else:
        messages.error(request, "Ошибка загрузки изображения.")
    return redirect('showcase:view_showcase', username=request.user.username)


def view_showcase(request, username):
    """Публичная витрина — для посетителей."""
    user = get_object_or_404(User, username=username)
    try:
        workshop = user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        return render(request, 'showcase/not_found.html', {'username': username})

    gallery = showcase.gallery_images.all()
    specialists = showcase.specialists.filter(is_active=True).order_by('order', 'last_name', 'first_name')

    # собираем цены по категориям
    prices = ServicePrice.objects.filter(workshop=workshop)
    grouped_prices = OrderedDict()
    for p in prices:
        cat = p.activity_area.get_category_display() if hasattr(p, 'activity_area') else 'Услуги'
        grouped_prices.setdefault(cat, []).append(p)

    return render(request, 'showcase/view_showcase.html', {
        'workshop': workshop,
        'showcase': showcase,
        'gallery': gallery,
        'specialists': specialists,
        'grouped_prices': grouped_prices,
        'is_owner': request.user.is_authenticated and request.user == user
    })


def specialists_list(request, username):
    """Публичный список специалистов витрины."""
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
        'page_obj': specialists_page,
        'is_owner': request.user.is_authenticated and request.user == user
    })


def specialist_detail(request, username, pk):
    """Публичная карточка специалиста."""
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


# --- Управление (владелец студии) ---
@login_required
def specialists_manage(request):
    """Страница управления специалистами (создание через форму, список)."""
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        messages.error(request, "Профиль студии не найден.")
        return redirect('accounts:profile')

    showcase, _ = Showcase.objects.get_or_create(workshop=workshop)
    specialists = showcase.specialists.all().order_by('order', 'last_name', 'first_name')
    form = SpecialistForm(workshop=workshop)
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
    """Создать специалиста."""
    try:
        workshop = request.user.workshopprofile
        showcase = workshop.showcase
    except (WorkshopProfile.DoesNotExist, Showcase.DoesNotExist):
        messages.error(request, "Витрина/профиль не найдены.")
        return redirect('accounts:profile')

    form = SpecialistForm(request.POST, request.FILES, workshop=workshop)
    if form.is_valid():
        spec = form.save(commit=False)
        spec.showcase = showcase
        spec.save()
        form.save_m2m()
        messages.success(request, "Специалист добавлен.")
        return redirect('showcase:specialists_manage')
    else:
        specialists = showcase.specialists.all().order_by('order', 'last_name', 'first_name')
        return render(request, 'showcase/specialists_manage.html', {
            'workshop': workshop,
            'showcase': showcase,
            'specialists': specialists,
            'form': form,
            'is_owner': True
        })


@login_required
def specialist_edit(request, pk):
    """Редактирование специалиста."""
    spec = get_object_or_404(Specialist, pk=pk)
    if spec.showcase.workshop.user != request.user:
        return HttpResponseForbidden('Нет доступа')

    workshop = spec.showcase.workshop
    if request.method == 'POST':
        form = SpecialistForm(request.POST, request.FILES, instance=spec, workshop=workshop)
        if form.is_valid():
            form.save()
            form.save_m2m()
            messages.success(request, "Изменения сохранены.")
            return redirect('showcase:specialists_manage')
    else:
        form = SpecialistForm(instance=spec, workshop=workshop)

    return render(request, 'showcase/specialist_edit.html', {
        'form': form,
        'specialist': spec,
        'is_owner': True,
    })


@login_required
@require_POST
def specialist_delete(request, pk):
    spec = get_object_or_404(Specialist, pk=pk)
    if spec.showcase.workshop.user != request.user:
        messages.error(request, "Нет доступа")
        return redirect('showcase:view_showcase', username=spec.showcase.workshop.user.username)

    try:
        photo_path = spec.photo.path if spec.photo else None
        spec.delete()
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
        messages.success(request, "Специалист удалён.")
    except Exception as e:
        logger.error(f"Ошибка при удалении специалиста: {e}")
        messages.error(request, "Ошибка при удалении специалиста.")
    return redirect('showcase:specialists_manage')


@login_required
@require_POST
def delete_image(request, image_id):
    try:
        image = get_object_or_404(GalleryImage, id=image_id)
        if image.showcase.workshop.user != request.user:
            return JsonResponse({'success': False, 'error': 'Нет доступа'}, status=403)
        image_file = image.image.path
        image.delete()
        if os.path.exists(image_file):
            os.remove(image_file)
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Ошибка удаления изображения {image_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
