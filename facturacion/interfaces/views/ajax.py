"""
Endpoints AJAX usados por los formularios de facturacion.
"""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest

from licencias.models import TipoLicencia


@login_required
def precio_licencia(request):
    """
    GET /facturacion/ajax/precio-licencia/?tipo_id=<id>

    Retorna precio_venta + descripcion + proveedor_default del TipoLicencia
    para autocompletar el form de cotizacion / factura.
    """
    tipo_id = request.GET.get('tipo_id')
    if not tipo_id:
        return HttpResponseBadRequest('tipo_id requerido')

    tipo = TipoLicencia.objects.filter(pk=tipo_id).first()
    if not tipo:
        return JsonResponse({'error': 'TipoLicencia no encontrado'}, status=404)

    return JsonResponse({
        'id': tipo.id,
        'nombre': tipo.nombre,
        'fabricante': tipo.fabricante,
        'descripcion': getattr(tipo, 'descripcion', '') or '',
        'precio_venta': str(getattr(tipo, 'precio_venta', 0) or 0),
        'precio_compra': str(getattr(tipo, 'precio_compra', 0) or 0),
        'proveedor_default_id': getattr(tipo, 'proveedor_default_id', None),
        'proveedor_default_nombre': getattr(getattr(tipo, 'proveedor_default', None), 'nombre', None),
    })
