# showcase/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import WorkshopProfile, ServicePrice
from .models import Showcase, GalleryImage
from .forms import ShowcaseForm, GalleryImageFormSet
from collections import OrderedDict
from django.contrib.staticfiles import finders
import json

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
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            for instance in instances:
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
    return render(request, 'showcase/view_showcase.html', {
        'workshop': workshop,
        'showcase': showcase,
        'gallery': gallery,
        'is_owner': is_owner,
        'grouped_prices': grouped_prices
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