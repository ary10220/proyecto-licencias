"""
Actions de bitacora para el modulo Facturacion (Comercial).

Cubre:
  - Propuestas comerciales (crear, editar, aprobar, rechazar, eliminar)
  - Facturas (crear, editar, anular, eliminar, generar stock de licencias)
  - Pagos de facturas (registrar, editar, anular)

Estas funciones se llaman desde los use cases de `facturacion/application/`.
"""

from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event


def _safe_str(obj, fallback="N/D"):
    try:
        return str(obj)
    except Exception:
        return fallback


# ============================================================================
# PROPUESTAS COMERCIALES
# ============================================================================

def log_propuesta_crear(request, propuesta):
    empresa = getattr(getattr(propuesta, 'empresa', None), 'nombre', None) or 'N/D'
    total = getattr(propuesta, 'total', 0)
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PROPUESTAS"],
        descripcion=f"Creo la propuesta comercial {_safe_str(propuesta)} (Empresa: {empresa}; Total: {total}).",
    )


def log_propuesta_editar(request, propuesta):
    empresa = getattr(getattr(propuesta, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PROPUESTAS"],
        descripcion=f"Actualizo la propuesta {_safe_str(propuesta)} (Empresa: {empresa}).",
    )


def log_propuesta_aprobar(request, propuesta):
    empresa = getattr(getattr(propuesta, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PROPUESTAS"],
        descripcion=f"Aprobo la propuesta {_safe_str(propuesta)} (Empresa: {empresa}).",
    )


def log_propuesta_rechazar(request, propuesta):
    empresa = getattr(getattr(propuesta, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PROPUESTAS"],
        descripcion=f"Rechazo la propuesta {_safe_str(propuesta)} (Empresa: {empresa}).",
    )


def log_propuesta_eliminar(request, propuesta_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PROPUESTAS"],
        descripcion=f"Elimino la propuesta {propuesta_label}.",
    )


# ============================================================================
# FACTURAS
# ============================================================================

def log_factura_crear(request, factura):
    empresa = getattr(getattr(factura, 'empresa', None), 'nombre', None) or 'N/D'
    proveedor = getattr(getattr(factura, 'proveedor', None), 'nombre', None) or 'N/D'
    total = getattr(factura, 'total', 0)
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["FACTURAS"],
        descripcion=(
            f"Emitio la factura {_safe_str(factura)} "
            f"(Empresa: {empresa}; Proveedor: {proveedor}; Total: {total})."
        ),
    )


def log_factura_editar(request, factura):
    empresa = getattr(getattr(factura, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["FACTURAS"],
        descripcion=f"Actualizo la factura {_safe_str(factura)} (Empresa: {empresa}).",
    )


def log_factura_anular(request, factura):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["FACTURAS"],
        descripcion=f"Anulo la factura {_safe_str(factura)}.",
    )


def log_factura_eliminar(request, factura_label):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["FACTURAS"],
        descripcion=f"Elimino la factura {factura_label}.",
    )


def log_factura_generar_stock(request, factura, cantidad_licencias: int):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["FACTURAS"],
        descripcion=(
            f"Genero stock de {cantidad_licencias} licencia(s) "
            f"desde la factura {_safe_str(factura)}."
        ),
    )


def log_pago_registrar(request, pago):
    factura = getattr(pago, 'factura', None)
    empresa = getattr(getattr(factura, 'empresa', None), 'nombre', None) or 'N/D'
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["PAGOS"],
        descripcion=(
            f"Registro pago de {getattr(pago, 'monto', 0)} para {_safe_str(factura)} "
            f"(Empresa: {empresa}; Metodo: {getattr(pago, 'metodo_pago', 'N/D')})."
        ),
    )


def log_pago_editar(request, pago, monto_anterior=None):
    factura = getattr(pago, 'factura', None)
    empresa = getattr(getattr(factura, 'empresa', None), 'nombre', None) or 'N/D'
    detalle_monto = ""
    if monto_anterior is not None and monto_anterior != getattr(pago, 'monto', None):
        detalle_monto = f" Monto anterior: {monto_anterior}."
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PAGOS"],
        descripcion=(
            f"Actualizo pago de {getattr(pago, 'monto', 0)} para {_safe_str(factura)} "
            f"(Empresa: {empresa}; Metodo: {getattr(pago, 'metodo_pago', 'N/D')})."
            f"{detalle_monto}"
        ),
    )


def log_pago_anular(request, pago):
    factura = getattr(pago, 'factura', None)
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PAGOS"],
        descripcion=(
            f"Anulo pago de {getattr(pago, 'monto', 0)} "
            f"asociado a {_safe_str(factura)}."
        ),
    )
