"""
Re-export centralizado de los modelos que gestiona Gestion Global.

Los modelos fisicamente viven en otras apps (licencias, empleados) por
razones historicas / migraciones; este modulo los EXPONE como propios
para mantener la separacion logica:

    from gestion_global.infrastructure.models import Empresa, Tenant
"""

from licencias.models import Empresa, Tenant   # noqa: F401
from empleados.models import (                  # noqa: F401
    GerenciaArea,
    GerenciaDivision,
    Unidad,
)

__all__ = [
    "Empresa",
    "Tenant",
    "GerenciaArea",
    "GerenciaDivision",
    "Unidad",
]
