from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import WorkshopProfile, ServicePrice
from .models import Showcase, GalleryImage
from .forms import ShowcaseForm, GalleryImageFormSet, GalleryImageForm
from collections import OrderedDict
from django.core.exceptions import ValidationError
from PIL import Image
import os


@login_required
def edit_showcase(request):
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        return redirect('accounts:profile')
    showcase, created = Showcase.objects.get_or_create(workshop=workshop)
    if request.method == 'POST':
        form = ShowcaseForm(request.POST, request.FILES, instance=showcase)
        formset = GalleryImageFormSet(request.POST, request.FILES, queryset=showcase.gallery_images.all())

        # Проверка размера и формата изображений
        for f in request.FILES.getlist('form-0-image') + [request.FILES.get('cover_photo')]:
            if f:
                if f.size > 5 * 1024 * 1024:  # 5MB
                    form.add_error(None, 'Размер изображения не должен превышать 5 МБ.')
                    continue
                try:
                    img = Image.open(f)
                    if img.format not in ['JPEG', 'PNG', 'GIF']:
                        form.add_error(None, 'Формат изображения должен быть JPEG, PNG или GIF.')
                except Exception:
                    form.add_error(None, 'Недопустимый формат изображения.')

        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            for instance in instances:
                if instance.image:
                    instance.showcase = showcase
                    instance.save()
            for instance in formset.deleted_objects:
                instance.delete()
            return redirect('showcase:view_showcase', username=request.user.username)
    else:
        form = ShowcaseForm(instance=showcase)
        formset = GalleryImageFormSet(queryset=showcase.gallery_images.all())
    return render(request, 'showcase/edit_showcase.html', {'form': form, 'formset': formset})


def view_showcase(request, username):
    user = get_object_or_404(User, username=username)
    is_owner = request.user.is_authenticated and request.user == user
    try:
        workshop = user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        return render(request, 'showcase/not_found.html', {'username': username})
    try:
        showcase = workshop.showcase
    except Showcase.DoesNotExist:
        if is_owner:
            return redirect('showcase:edit_showcase')
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
            image = upload_form.cleaned_data['image']
            if image.size > 5 * 1024 * 1024:  # 5MB
                upload_form.add_error(None, 'Размер изображения не должен превышать 5 МБ.')
            else:
                try:
                    img = Image.open(image)
                    if img.format not in ['JPEG', 'PNG', 'GIF']:
                        upload_form.add_error(None, 'Формат изображения должен быть JPEG, PNG или GIF.')
                    else:
                        gallery_image = upload_form.save(commit=False)
                        gallery_image.showcase = showcase
                        gallery_image.save()
                        return redirect('showcase:view_showcase', username=username)
                except Exception:
                    upload_form.add_error(None, 'Недопустимый формат изображения.')
        # Если форма невалидна, она передаётся в шаблон для отображения ошибок
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
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)