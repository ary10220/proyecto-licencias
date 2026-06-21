"""
Construye el catalogo real del sistema (ids + nombres) que se le pasa al
modelo como grounding, para que mapee nombres -> ids y no invente entidades.

Solo se incluyen registros activos. El asistente valida despues que cada id
devuelto por el modelo pertenezca a este catalogo.
"""
from __future__ import annotations

from licencias.models import Empresa, Proveedor, Tenant, TipoLicencia


def construir_catalogo() -> dict:
    return {
        'tenants': [
            {'id': t.id, 'nombre': t.nombre}
            for t in Tenant.objects.filter(activo=True).order_by('nombre')
        ],
        'empresas': [
            {'id': e.id, 'nombre': e.nombre}
            for e in Empresa.objects.filter(activo=True).order_by('nombre')
        ],
        'tipos': [
            {'id': t.id, 'nombre': f'{t.fabricante} {t.nombre}'.strip()}
            for t in TipoLicencia.objects.filter(activo=True).order_by('fabricante', 'nombre')
        ],
        'proveedores': [
            {'id': p.id, 'nombre': p.nombre}
            for p in Proveedor.objects.filter(activo=True).order_by('nombre')
        ],
    }
