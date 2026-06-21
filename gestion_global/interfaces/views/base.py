"""
Helpers compartidos entre todas las vistas de gestion_global.

Centraliza decoradores de permisos para no repetir el chequeo en cada
vista del modulo.
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


MODAL_STATE_KEY = '_gg_modal_state'


def exigir_permiso(permiso, fallback='home'):
    """
    Decorador: exige `permiso` al usuario, sino redirige con mensaje.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.has_perm(permiso):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para esa accion.")
            return redirect(fallback)
        return wrapper
    return decorator


def exigir_algun_permiso(permisos, fallback='home'):
    """Decorador: exige al menos UNO de los permisos listados."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or any(user.has_perm(p) for p in permisos):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para acceder a esta seccion.")
            return redirect(fallback)
        return wrapper
    return decorator


def guardar_estado_modal(request, modal_name):
    request.session[MODAL_STATE_KEY] = {
        'modal': modal_name,
        'data': dict(request.POST.items()),
    }
    request.session.modified = True


def consumir_estado_modal(request, modal_name, form_class, puede_crear=True):
    state = request.session.pop(MODAL_STATE_KEY, None)
    if not puede_crear or not state or state.get('modal') != modal_name:
        return (form_class() if puede_crear else None), ''

    form = form_class(state.get('data') or None)
    form.is_valid()
    return form, modal_name
