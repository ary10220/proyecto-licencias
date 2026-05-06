"""
Actions de bitácora para el módulo Configuración / Parametrización Global.

Estas funciones se llaman desde las vistas del panel `configuracion` (licencias/views.py)
para registrar altas/bajas/cambios de catálogos.

Nota: Para mantener coherencia con la UI:
- Tenants/Empresas/Proveedores/Tipos de licencia => MODULOS["CONFIG"]
- Divisiones/Áreas/Unidades (estructura organizacional) => MODULOS["ORG"]
"""

from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event


def _safe_str(obj, fallback="N/D"):
    try:
        return str(obj)
    except Exception:
        return fallback


def log_tenant_crear(request, tenant):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creó el tenant corporativo {_safe_str(tenant)} (id={getattr(tenant, 'pk', 'N/D')}).",
    )


def log_empresa_crear(request, empresa):
    tenant = getattr(getattr(empresa, 'tenant', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creó la empresa {_safe_str(empresa)} (Tenant: {tenant}).",
    )


def log_proveedor_crear(request, proveedor):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creó el proveedor {_safe_str(proveedor)}.",
    )


def log_tipo_licencia_crear(request, tipo_licencia):
    fabricante = getattr(tipo_licencia, 'fabricante', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creó el tipo de licencia {_safe_str(tipo_licencia)} (Fabricante: {fabricante}).",
    )


def log_division_crear(request, division):
    empresa = getattr(getattr(division, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creó la división {_safe_str(division)} (Empresa: {empresa}).",
    )


def log_area_crear(request, area):
    empresa = getattr(getattr(area, 'empresa', None), 'nombre', None) or 'N/D'
    division = getattr(getattr(area, 'division', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creó el área {_safe_str(area)} (Empresa: {empresa}; División: {division}).",
    )


def log_unidad_crear(request, unidad):
    area = getattr(getattr(unidad, 'area', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creó la unidad {_safe_str(unidad)} (Área: {area}).",
    )
