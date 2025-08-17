from django.urls import path
from . import views

app_name = 'showcase'

urlpatterns = [
    path('showcase/<str:username>/', views.view_showcase, name='view_showcase'),
    path('edit/', views.edit_showcase, name='edit_showcase'),
    path('upload/', views.upload_gallery_image, name='upload_gallery_image'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
]