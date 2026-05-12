"""
Actions de bitacora para el modulo Configuracion / Parametrizacion Global.

Estas funciones se llaman desde las vistas del panel `configuracion` para
registrar altas/bajas/cambios de catalogos.
"""

from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event


def _safe_str(obj, fallback="N/D"):
    try:
        return str(obj)
    except Exception:
        return fallback


# ============================================================================
# CREAR
# ============================================================================

def log_tenant_crear(request, tenant):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creo el tenant corporativo {_safe_str(tenant)} (id={getattr(tenant, 'pk', 'N/D')}).",
    )


def log_empresa_crear(request, empresa):
    tenant = getattr(getattr(empresa, 'tenant', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creo la empresa {_safe_str(empresa)} (Tenant: {tenant}).",
    )


def log_proveedor_crear(request, proveedor):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creo el proveedor {_safe_str(proveedor)}.",
    )


def log_tipo_licencia_crear(request, tipo_licencia):
    fabricante = getattr(tipo_licencia, 'fabricante', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Creo el tipo de licencia {_safe_str(tipo_licencia)} (Fabricante: {fabricante}).",
    )


def log_division_crear(request, division):
    empresa = getattr(getattr(division, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creo la division {_safe_str(division)} (Empresa: {empresa}).",
    )


def log_area_crear(request, area):
    empresa = getattr(getattr(area, 'empresa', None), 'nombre', None) or 'N/D'
    division = getattr(getattr(area, 'division', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creo el area {_safe_str(area)} (Empresa: {empresa}; Division: {division}).",
    )


def log_unidad_crear(request, unidad):
    area = getattr(getattr(unidad, 'area', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creo la unidad {_safe_str(unidad)} (Area: {area}).",
    )


# ============================================================================
# EDITAR
# ============================================================================

def log_tenant_editar(request, tenant):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Actualizo el tenant corporativo {_safe_str(tenant)} (id={getattr(tenant, 'pk', 'N/D')}).",
    )


def log_empresa_editar(request, empresa):
    tenant = getattr(getattr(empresa, 'tenant', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Actualizo la empresa {_safe_str(empresa)} (Tenant: {tenant}).",
    )


def log_proveedor_editar(request, proveedor):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Actualizo el proveedor {_safe_str(proveedor)}.",
    )


def log_tipo_licencia_editar(request, tipo_licencia):
    fabricante = getattr(tipo_licencia, 'fabricante', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Actualizo el tipo de licencia {_safe_str(tipo_licencia)} (Fabricante: {fabricante}).",
    )


def log_division_editar(request, division):
    empresa = getattr(getattr(division, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Actualizo la division {_safe_str(division)} (Empresa: {empresa}).",
    )


def log_area_editar(request, area):
    empresa = getattr(getattr(area, 'empresa', None), 'nombre', None) or 'N/D'
    division = getattr(getattr(area, 'division', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Actualizo el area {_safe_str(area)} (Empresa: {empresa}; Division: {division}).",
    )


def log_unidad_editar(request, unidad):
    area = getattr(getattr(unidad, 'area', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Actualizo la unidad {_safe_str(unidad)} (Area: {area}).",
    )


# ============================================================================
# BAJA / REACTIVAR
# ============================================================================

def log_tenant_eliminar(request, tenant_label):
    log_event(
        request=request,
        accion=ACCIONES["BAJA"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Inactivo el tenant {tenant_label}.",
    )


def log_empresa_eliminar(request, empresa_label):
    log_event(
        request=request,
        accion=ACCIONES["BAJA"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Inactivo la empresa {empresa_label}.",
    )


def log_proveedor_eliminar(request, proveedor_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Elimino el proveedor {proveedor_label}.",
    )


def log_tipo_licencia_eliminar(request, tipo_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Elimino el tipo de licencia {tipo_label}.",
    )


def log_division_eliminar(request, division_label):
    log_event(
        request=request,
        accion=ACCIONES["BAJA"],
        modulo=MODULOS["ORG"],
        descripcion=f"Inactivo la division {division_label}.",
    )


def log_area_eliminar(request, area_label):
    log_event(
        request=request,
        accion=ACCIONES["BAJA"],
        modulo=MODULOS["ORG"],
        descripcion=f"Inactivo el area {area_label}.",
    )


def log_unidad_eliminar(request, unidad_label):
    log_event(
        request=request,
        accion=ACCIONES["BAJA"],
        modulo=MODULOS["ORG"],
        descripcion=f"Inactivo la unidad {unidad_label}.",
    )


def log_tenant_reactivar(request, tenant):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Reactivo el tenant {_safe_str(tenant)}.",
    )


def log_empresa_reactivar(request, empresa):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"],
        modulo=MODULOS["CONFIG"],
        descripcion=f"Reactivo la empresa {_safe_str(empresa)}.",
    )


def log_division_reactivar(request, division):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Reactivo la division {_safe_str(division)}.",
    )


def log_area_reactivar(request, area):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Reactivo el area {_safe_str(area)}.",
    )


def log_unidad_reactivar(request, unidad):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Reactivo la unidad {_safe_str(unidad)}.",
    )
