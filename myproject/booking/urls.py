# booking/urls.py
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Для владельца (workshop)
    path('specialists/', views.owner_specialists_list, name='owner_specialists_list'),
    path('specialist/<int:pk>/schedule/', views.owner_schedule_manage, name='owner_schedule_manage'),
    path('specialist/<int:pk>/appointments/', views.owner_appointments_list, name='owner_appointments_list'),
    path('appointment/<int:pk>/confirm/', views.owner_confirm_appointment, name='owner_confirm_appointment'),
    path('appointment/<int:pk>/cancel/', views.owner_cancel_appointment, name='owner_cancel_appointment'),

    # Для клиента
    path('specialist/<int:pk>/book/', views.client_book_appointment, name='client_book_appointment'),
    path('my-appointments/', views.client_my_appointments, name='client_my_appointments'),
    path('appointment/<int:pk>/cancel-client/', views.client_cancel_appointment, name='client_cancel_appointment'),
    path('appointment/<int:pk>/delete/', views.owner_delete_appointment, name='owner_delete_appointment'),
]

