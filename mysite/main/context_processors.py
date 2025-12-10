from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib.auth.models import AnonymousUser

def show_2fa_setup(request):
    """
    Context processor для показу модалки 2FA
    """
    show_setup = False
    
    # Перевіряємо чи користувач авторизований і чи потрібно показати модалку
    if not isinstance(request.user, AnonymousUser) and request.user.is_authenticated:
        has_2fa = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
        show_setup = not has_2fa
    
    return {
        'show_2fa_setup': show_setup
    }