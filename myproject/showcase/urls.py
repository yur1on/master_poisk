from django.urls import path
from . import views

app_name = 'showcase'

urlpatterns = [
    path('edit/', views.edit_showcase, name='edit_showcase'),
    path('upload-gallery-image/', views.upload_gallery_image, name='upload_gallery_image'),
    path('<str:username>/', views.view_showcase, name='view_showcase'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
]