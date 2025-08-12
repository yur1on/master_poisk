from .models import WorkshopProfile, ClientProfile

def user_type(request):
    if request.user.is_authenticated:
        try:
            request.user.workshopprofile
            return {'is_workshop': True, 'is_client': False}
        except WorkshopProfile.DoesNotExist:
            try:
                request.user.clientprofile
                return {'is_workshop': False, 'is_client': True}
            except ClientProfile.DoesNotExist:
                pass
    return {'is_workshop': False, 'is_client': False}