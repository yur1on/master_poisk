from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ClientRegisterForm, WorkshopRegisterForm, ClientProfileForm, WorkshopProfileForm
from .models import ClientProfile, WorkshopProfile
from collections import OrderedDict
from django.db import IntegrityError

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
            # Conditional redirect based on user type
            try:
                user.workshopprofile  # Check if workshop
                return redirect('showcase:view_showcase', username=user.username)
            except WorkshopProfile.DoesNotExist:
                try:
                    user.clientprofile  # Check if client
                    return redirect('accounts:profile')
                except ClientProfile.DoesNotExist:
                    pass
            return redirect('main:home')  # Fallback for other users
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
                # Redirect to profile for clients
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
            # Redirect to showcase for workshops
            return redirect('showcase:view_showcase', username=user.username)
    else:
        form = WorkshopRegisterForm()
    return render(request, 'accounts/register_workshop.html', {'form': form})

@login_required
def profile_view(request):
    try:
        client_profile = request.user.clientprofile
        is_client = True
    except ClientProfile.DoesNotExist:
        client_profile = None
        is_client = False

    try:
        workshop_profile = request.user.workshopprofile
        is_workshop = True
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
    except WorkshopProfile.DoesNotExist:
        workshop_profile = None
        is_workshop = False
        grouped_activities = {}

    return render(request, 'accounts/profile.html', {
        'client_profile': client_profile,
        'workshop_profile': workshop_profile,
        'is_client': is_client,
        'is_workshop': is_workshop,
        'grouped_activities': grouped_activities,
        'user': request.user
    })

@login_required
def edit_profile(request):
    user = request.user

    try:
        client_profile = user.clientprofile
        if request.method == 'POST':
            form = ClientProfileForm(request.POST, instance=client_profile)
            if form.is_valid():
                client_profile = form.save()
                user.email = form.cleaned_data['email']
                user.save()
                return redirect('accounts:profile')
        else:
            form = ClientProfileForm(instance=client_profile, initial={'email': user.email})
        return render(request, 'accounts/edit_client_profile.html', {'form': form})

    except ClientProfile.DoesNotExist:
        pass

    try:
        workshop_profile = user.workshopprofile
        if request.method == 'POST':
            form = WorkshopProfileForm(request.POST, instance=workshop_profile)
            if form.is_valid():
                workshop_profile = form.save(commit=False)
                user.email = form.cleaned_data['email']
                user.save()
                workshop_profile.save()
                form.save_m2m()
                return redirect('accounts:profile')
        else:
            form = WorkshopProfileForm(
                instance=workshop_profile,
                initial={'email': user.email}
            )
        return render(request, 'accounts/edit_workshop_profile.html', {'form': form})

    except WorkshopProfile.DoesNotExist:
        pass

    return redirect('main:home')