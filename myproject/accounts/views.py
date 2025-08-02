# accounts/views.py
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect

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
            login(request, form.get_user())
            return redirect('main:home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('main:home')

from django.shortcuts import render, redirect

def select_user_type(request):
    return render(request, 'accounts/select_user_type.html')


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from .forms import ClientRegisterForm, WorkshopRegisterForm
from .models import ClientProfile, WorkshopProfile
from django.contrib.auth import login

def register_client(request):
    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data['phone']
            ClientProfile.objects.create(user=user, phone=phone)
            login(request, user)
            return redirect('main:home')
    else:
        form = ClientRegisterForm()
    return render(request, 'accounts/register_client.html', {'form': form})

def register_workshop(request):
    if request.method == 'POST':
        form = WorkshopRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            WorkshopProfile.objects.create(
                user=user,
                workshop_name=form.cleaned_data['workshop_name'],
                workshop_address=form.cleaned_data['workshop_address'],
                phone=form.cleaned_data['phone'],
            )
            login(request, user)
            return redirect('main:home')
    else:
        form = WorkshopRegisterForm()
    return render(request, 'accounts/register_workshop.html', {'form': form})

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

@login_required
def profile_view(request):
    try:
        client_profile = request.user.clientprofile
        is_client = True
    except:
        client_profile = None
        is_client = False

    try:
        workshop_profile = request.user.workshopprofile
        is_workshop = True
    except:
        workshop_profile = None
        is_workshop = False

    return render(request, 'accounts/profile.html', {
        'client_profile': client_profile,
        'workshop_profile': workshop_profile,
        'is_client': is_client,
        'is_workshop': is_workshop,
    })

from .forms import ClientProfileForm, WorkshopProfileForm
from django.contrib.auth.models import User

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
                workshop_profile = form.save()
                user.email = form.cleaned_data['email']
                user.save()
                return redirect('accounts:profile')
        else:
            form = WorkshopProfileForm(instance=workshop_profile, initial={'email': user.email})
        return render(request, 'accounts/edit_workshop_profile.html', {'form': form})
    except WorkshopProfile.DoesNotExist:
        pass

    # если ни клиент ни мастер — редирект
    return redirect('main:home')
