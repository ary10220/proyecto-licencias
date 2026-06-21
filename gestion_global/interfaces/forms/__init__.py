"""
Formularios (capa interfaces) del modulo `gestion_global`.

Re-export para imports cortos:

    from gestion_global.interfaces.forms import EmpresaForm
"""

from .empresas import EmpresaForm
from .tenants import TenantForm
from .areas import AreaForm
from .divisiones import DivisionForm
from .unidades import UnidadForm

__all__ = [
    "EmpresaForm",
    "TenantForm",
    "AreaForm",
    "DivisionForm",
    "UnidadForm",
]
