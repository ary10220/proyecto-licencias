from django.shortcuts import redirect
from django.urls import reverse

from .models import PerfilUsuario


class ForcePasswordChangeMiddleware:
    """
    If a user account was created with a default password, force them to change it
    on first login before accessing the system.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            try:
                perfil = user.perfil
            except Exception:
                perfil, _ = PerfilUsuario.objects.get_or_create(user=user)

            if getattr(perfil, 'must_change_password', False):
                password_change_url = reverse('password_change')
                home_url = reverse('home')
                inicio_url = reverse('inicio')
                allowed_prefixes = (
                    password_change_url,
                    reverse('password_change_done'),
                    reverse('logout'),
                    reverse('reset_password'),
                    reverse('password_reset_done'),
                    '/reset/',
                    reverse('password_reset_complete'),
                    reverse('login'),
                    '/admin/',
                    '/static/',
                    '/media/',
                    home_url,
                    inicio_url,
                    '/dashboard/',
                )

                if not any(request.path.startswith(prefix) for prefix in allowed_prefixes):
                    # Let the user enter the app (home) and show the blocking modal there.
                    return redirect('home')

        return self.get_response(request)
