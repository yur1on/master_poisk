from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from accounts.models import WorkshopProfile
from showcase.models import Showcase

from django.shortcuts import render
from accounts.models import WorkshopProfile
from showcase.models import Showcase

def search_view(request):
    workshops = WorkshopProfile.objects.all().order_by('workshop_name')
    workshop_data = []
    for workshop in workshops:
        activities = ', '.join([area.name for area in workshop.activity_area.all()])
        try:
            showcase = workshop.showcase
            banner = showcase.cover_photo.url if showcase.cover_photo else None
        except Showcase.DoesNotExist:
            banner = None
        workshop_data.append({
            'username': workshop.user.username,
            'name': workshop.workshop_name,
            'activities': activities or 'Не указано',
            'banner': banner,
        })
    return render(request, 'search/search.html', {'workshops': workshop_data})