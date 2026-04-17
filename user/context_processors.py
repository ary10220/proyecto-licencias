from .models import PerfilUsuario


def force_password_change(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'force_password_change': False}

    try:
        perfil = user.perfil
    except Exception:
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)

    return {'force_password_change': bool(getattr(perfil, 'must_change_password', False))}

