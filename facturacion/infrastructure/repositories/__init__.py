"""
Repositorios (capa infrastructure) del modulo `facturacion`.

Re-export para imports cortos:

    from facturacion.infrastructure import repositories as repo
"""

from .propuestas import (
    list_propuestas,
    get_propuesta,
    delete_propuesta,
    distinct_estados_propuesta,
)
from .facturas import (
    list_facturas,
    get_factura,
    delete_factura,
    distinct_estados_factura,
)
from .pagos import (
    get_pago,
    list_facturas_para_pagos,
    list_pagos_recientes,
)

__all__ = [
    "list_propuestas", "get_propuesta", "delete_propuesta", "distinct_estados_propuesta",
    "list_facturas", "get_factura", "delete_factura", "distinct_estados_factura",
    "list_facturas_para_pagos", "list_pagos_recientes", "get_pago",
]
