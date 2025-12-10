from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib import messages

class Require2FAMiddleware:
    """
    Middleware для обов'язкової двофакторної автентифікації
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URL-и, які не потребують 2FA перевірки
        exempt_urls = [
            '/login/',
            '/register/',
            '/setup-2fa/',
            '/logout/',
            '/admin/',
        ]
        
        # Статичні файли та адмін панель
        exempt_prefixes = ['/static/', '/media/', '/admin/']
        
        # Middleware тепер не блокує доступ, а тільки показує модалку через context processor

        response = self.get_response(request)
        return response