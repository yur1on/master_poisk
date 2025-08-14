# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.select_user_type, name='select_user_type'),
    path('register/client/', views.register_client, name='register_client'),
    path('register/workshop/', views.register_workshop, name='register_workshop'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/edit-prices/', views.edit_prices, name='edit_prices'),
]