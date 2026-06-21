from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from licencias.models import Empresa, Tenant, TipoLicencia


def exigir_permiso(permiso, fallback='home'):
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


def filtros_comerciales_context() -> dict:
    """Catalogos reutilizados por filtros dinamicos de cotizaciones/facturas."""
    return {
        'tenants': Tenant.objects.filter(activo=True).order_by('nombre'),
        'empresas': Empresa.objects.filter(activo=True).select_related('tenant').order_by('tenant__nombre', 'nombre'),
        'tipos_licencia': TipoLicencia.objects.filter(activo=True).order_by('fabricante', 'nombre'),
    }
