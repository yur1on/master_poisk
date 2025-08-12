from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import WorkshopProfile
from .models import Showcase
from .forms import ShowcaseForm, GalleryFormSet, GalleryImageForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import WorkshopProfile
from .models import Showcase
from .forms import ShowcaseForm, GalleryFormSet, GalleryImageForm

@login_required
def edit_showcase(request):
    try:
        workshop = request.user.workshopprofile
    except WorkshopProfile.DoesNotExist:
        return redirect('accounts:profile')  # Redirect if not a workshop

    showcase, created = Showcase.objects.get_or_create(workshop=workshop)

    if request.method == 'POST':
        form = ShowcaseForm(request.POST, request.FILES, instance=showcase)
        formset = GalleryFormSet(request.POST, request.FILES, queryset=showcase.gallery_images.all())
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
        formset = GalleryFormSet(queryset=showcase.gallery_images.all())

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
        else:
            return render(request, 'showcase/not_found.html', {'username': username})

    gallery = showcase.gallery_images.all()

    upload_form = None
    if is_owner and request.method == 'POST':
        upload_form = GalleryImageForm(request.POST, request.FILES)
        if upload_form.is_valid():
            new_image = upload_form.save(commit=False)
            new_image.showcase = showcase
            new_image.save()
            return redirect('showcase:view_showcase', username=username)
    elif is_owner:
        upload_form = GalleryImageForm()

    return render(request, 'showcase/view_showcase.html', {
        'workshop': workshop,
        'showcase': showcase,
        'gallery': gallery,
        'is_owner': is_owner,
        'upload_form': upload_form,
    })

