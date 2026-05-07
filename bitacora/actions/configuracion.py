"""
Actions de bitácora para el módulo Configuración / Parametrización Global.

Estas funciones se llaman desde las vistas del panel `configuracion` (licencias/views.py)
para registrar altas/bajas/cambios de catálogos.

Nota: Para mantener coherencia con la UI:
- Tenants/Empresas/Proveedores/Tipos de licencia => MODULOS["PARAM"]
- Divisiones/Áreas/Unidades (estructura organizacional) => MODULOS["PARAM"]
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
        modulo=MODULOS["PARAM"],
        descripcion=f"Creó el tenant corporativo {_safe_str(tenant)} (id={getattr(tenant, 'pk', 'N/D')}).",
    )


def log_empresa_crear(request, empresa):
    tenant = getattr(getattr(empresa, 'tenant', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Creó la empresa {_safe_str(empresa)} (Tenant: {tenant}).",
    )


def log_proveedor_crear(request, proveedor):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Creó el proveedor {_safe_str(proveedor)}.",
    )


def log_tipo_licencia_crear(request, tipo_licencia):
    fabricante = getattr(tipo_licencia, 'fabricante', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Creó el tipo de licencia {_safe_str(tipo_licencia)} (Fabricante: {fabricante}).",
    )


def log_division_crear(request, division):
    empresa = getattr(getattr(division, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Creó la división {_safe_str(division)} (Empresa: {empresa}).",
    )


def log_area_crear(request, area):
    empresa = getattr(getattr(area, 'empresa', None), 'nombre', None) or 'N/D'
    division = getattr(getattr(area, 'division', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Creó el área {_safe_str(area)} (Empresa: {empresa}; División: {division}).",
    )


def log_unidad_crear(request, unidad):
    area = getattr(getattr(unidad, 'area', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Creó la unidad {_safe_str(unidad)} (Área: {area}).",
    )


# ============================================================================
# EDITAR
# ============================================================================

def log_tenant_editar(request, tenant):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Actualizo el tenant corporativo {_safe_str(tenant)} (id={getattr(tenant, 'pk', 'N/D')}).",
    )


def log_empresa_editar(request, empresa):
    tenant = getattr(getattr(empresa, 'tenant', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Actualizo la empresa {_safe_str(empresa)} (Tenant: {tenant}).",
    )


def log_proveedor_editar(request, proveedor):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Actualizo el proveedor {_safe_str(proveedor)}.",
    )


def log_tipo_licencia_editar(request, tipo_licencia):
    fabricante = getattr(tipo_licencia, 'fabricante', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Actualizo el tipo de licencia {_safe_str(tipo_licencia)} (Fabricante: {fabricante}).",
    )


def log_division_editar(request, division):
    empresa = getattr(getattr(division, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Actualizo la division {_safe_str(division)} (Empresa: {empresa}).",
    )


def log_area_editar(request, area):
    empresa = getattr(getattr(area, 'empresa', None), 'nombre', None) or 'N/D'
    division = getattr(getattr(area, 'division', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Actualizo el area {_safe_str(area)} (Empresa: {empresa}; Division: {division}).",
    )


def log_unidad_editar(request, unidad):
    area = getattr(getattr(unidad, 'area', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Actualizo la unidad {_safe_str(unidad)} (Area: {area}).",
    )


# ============================================================================
# ELIMINAR
# Se reciben labels (strings), no objetos, porque el registro se invoca
# despues del delete() y la instancia ya no existe en BD.
# ============================================================================

def log_tenant_eliminar(request, tenant_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Elimino el tenant {tenant_label}.",
    )


def log_empresa_eliminar(request, empresa_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Elimino la empresa {empresa_label}.",
    )


def log_proveedor_eliminar(request, proveedor_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Elimino el proveedor {proveedor_label}.",
    )


def log_tipo_licencia_eliminar(request, tipo_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Elimino el tipo de licencia {tipo_label}.",
    )


def log_division_eliminar(request, division_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Elimino la division {division_label}.",
    )


def log_area_eliminar(request, area_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Elimino el area {area_label}.",
    )


def log_unidad_eliminar(request, unidad_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PARAM"],
        descripcion=f"Elimino la unidad {unidad_label}.",
    )
