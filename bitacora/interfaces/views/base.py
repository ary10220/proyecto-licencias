"""
Imports y helpers compartidos por las vistas del modulo `bitacora`.

Las vistas concretas (bitacora, filtros) hacen `from .base import *` para
heredar todo lo necesario sin repetir imports.
"""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render

from ..forms import BitacoraFiltroForm  # noqa: F401  (re-export)


def permiso_requerido(permiso: str, *, json: bool = False):
    """
    Decorador que valida un permiso especifico.

    - Por defecto levanta PermissionDenied (renderiza 403).
    - Si `json=True`, devuelve JsonResponse con status 403 (util para endpoints AJAX).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.has_perm(permiso):
                return view_func(request, *args, **kwargs)
            if json:
                return JsonResponse({"error": "No autorizado"}, status=403)
            raise PermissionDenied
        return wrapper
    return decorator
