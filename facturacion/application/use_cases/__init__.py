"""
Casos de uso (capa application) del modulo `facturacion`.

Cada submodulo implementa un Caso de Uso del flujo comercial:

    Propuestas comerciales  -> use_cases/propuestas.py
    Facturas + generacion stock -> use_cases/facturas.py
    Pagos de facturas -> use_cases/pagos.py

Re-export para imports cortos:

    from facturacion.application.use_cases import uc_crear_propuesta
"""

from .propuestas import (
    uc_listar_propuestas,
    uc_actualizar_propuesta_administrativa,
    uc_crear_propuesta,
    uc_editar_propuesta,
    uc_aprobar_propuesta,
    uc_rechazar_propuesta,
    uc_eliminar_propuesta,
)
from .facturas import (
    uc_listar_facturas,
    uc_crear_factura,
    uc_editar_datos_fiscales_factura,
    uc_editar_factura,
    uc_anular_factura,
    uc_eliminar_factura,
    uc_generar_stock_factura,
    uc_emitir_factura_desde_propuesta,
)
from .pagos import (
    construir_resumen_pagos,
    uc_anular_pago,
    uc_crear_pago_directo,
    uc_editar_pago,
    uc_listar_pagos,
    uc_registrar_pago,
)

__all__ = [
    "uc_listar_propuestas",
    "uc_actualizar_propuesta_administrativa",
    "uc_crear_propuesta",
    "uc_editar_propuesta",
    "uc_aprobar_propuesta",
    "uc_rechazar_propuesta",
    "uc_eliminar_propuesta",
    "uc_listar_facturas",
    "uc_crear_factura",
    "uc_editar_datos_fiscales_factura",
    "uc_editar_factura",
    "uc_anular_factura",
    "uc_eliminar_factura",
    "uc_generar_stock_factura",
    "uc_emitir_factura_desde_propuesta",
    "uc_listar_pagos",
    "construir_resumen_pagos",
    "uc_registrar_pago",
    "uc_editar_pago",
    "uc_crear_pago_directo",
    "uc_anular_pago",
]
