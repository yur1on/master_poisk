from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from . import views

app_name = 'showcase'

urlpatterns = [
    # public showcase
    path('showcase/<str:username>/', views.view_showcase, name='view_showcase'),

    # public specialists
    path('showcase/<str:username>/specialists/', views.specialists_list, name='specialists_list'),
    path('showcase/<str:username>/specialist/<int:pk>/', views.specialist_detail, name='specialist_detail'),

    # owner management (access via profile/dashboard)
    path('specialists/manage/', views.specialists_manage, name='specialists_manage'),
    path('specialists/create/', views.specialist_create, name='specialist_create'),
    path('specialists/<int:pk>/edit/', views.specialist_edit, name='specialist_edit'),
    path('specialists/<int:pk>/delete/', views.specialist_delete, name='specialist_delete'),

    # existing routes
    path('edit/', views.edit_showcase, name='edit_showcase'),
    path('upload/', views.upload_gallery_image, name='upload_gallery_image'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),

]
