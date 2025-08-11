from django.urls import path
from . import views

app_name = 'showcase'

urlpatterns = [
    path('edit/', views.edit_showcase, name='edit_showcase'),
    path('<str:username>/', views.view_showcase, name='view_showcase'),
]