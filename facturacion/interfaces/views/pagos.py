"""Vistas de pagos de facturas."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .base import exigir_permiso, filtros_comerciales_context
from ..forms import PagoFacturaForm
from ...application.use_cases import (
    construir_resumen_pagos,
    uc_anular_pago,
    uc_editar_pago,
    uc_listar_pagos,
    uc_registrar_pago,
)
from ...infrastructure import repositories as repo
from ...infrastructure.models import Factura


@login_required
@exigir_permiso('facturacion.view_factura')
def lista_pagos(request):
    q = request.GET.get('q', '').strip()
    estado_pago = request.GET.get('estado_pago', 'todos')
    tenant_id = request.GET.get('tenant') or ''
    empresa_id = request.GET.get('empresa') or ''
    metodo_pago = request.GET.get('metodo_pago', 'todos')
    fecha_desde = request.GET.get('fecha_desde') or ''
    fecha_hasta = request.GET.get('fecha_hasta') or ''

    facturas_qs, pagos_recientes = uc_listar_pagos(
        q=q,
        estado_pago=estado_pago,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        metodo_pago=metodo_pago,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    facturas = list(facturas_qs)
    resumen = construir_resumen_pagos(facturas)

    context = {
        'facturas': facturas,
        'pagos_recientes': pagos_recientes,
        'resumen': resumen,
        'q': q,
        'estado_pago': estado_pago,
        'tenant_filtro': tenant_id,
        'empresa_filtro': empresa_id,
        'metodo_pago_filtro': metodo_pago,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'metodos_pago': Factura.METODOS_PAGO,
        'puede_registrar': request.user.has_perm('facturacion.change_factura') or request.user.is_superuser,
        'facturacion_active': 'pagos',
    }
    context.update(filtros_comerciales_context())
    return render(request, 'facturacion/pagos/lista.html', context)


@login_required
@exigir_permiso('facturacion.change_factura')
def registrar_pago(request, factura_id):
    factura = repo.get_factura(factura_id)
    if factura.estado == 'ANULADA':
        messages.warning(request, "No se pueden registrar pagos en una factura anulada.")
        return redirect('detalle_factura', pk=factura.pk)
    if factura.saldo_pendiente <= 0:
        messages.info(request, "La factura ya no tiene saldo pendiente.")
        return redirect('detalle_factura', pk=factura.pk)

    if request.method == 'POST':
        form = PagoFacturaForm(request.POST, request.FILES, factura=factura)
        if form.is_valid():
            ok, info, _ = uc_registrar_pago(request=request, factura=factura, pago_form=form)
            (messages.success if ok else messages.error)(request, info)
            if ok:
                next_url = request.POST.get('next') or request.GET.get('next')
                return redirect(next_url or 'lista_pagos')
    else:
        form = PagoFacturaForm(factura=factura)

    return render(request, 'facturacion/pagos/form.html', {
        'factura': factura,
        'form': form,
        'modo': 'crear',
        'next': request.GET.get('next') or '',
        'facturacion_active': 'pagos',
    })


@login_required
@exigir_permiso('facturacion.change_factura')
def editar_pago(request, pk):
    pago = repo.get_pago(pk)
    factura = pago.factura
    if pago.estado == 'ANULADO':
        messages.warning(request, "No se puede editar un pago anulado.")
        return redirect('detalle_factura', pk=factura.pk)

    if request.method == 'POST':
        form = PagoFacturaForm(request.POST, request.FILES, factura=factura, instance=pago)
        if form.is_valid():
            ok, info, _ = uc_editar_pago(request=request, pago=pago, pago_form=form)
            (messages.success if ok else messages.error)(request, info)
            if ok:
                next_url = request.POST.get('next') or request.GET.get('next')
                return redirect(next_url or 'lista_pagos')
    else:
        form = PagoFacturaForm(factura=factura, instance=pago)

    return render(request, 'facturacion/pagos/form.html', {
        'factura': factura,
        'pago': pago,
        'form': form,
        'modo': 'editar',
        'next': request.GET.get('next') or '',
        'facturacion_active': 'pagos',
    })


@login_required
@exigir_permiso('facturacion.change_factura')
def anular_pago(request, pk):
    pago = repo.get_pago(pk)
    if request.method == 'POST':
        ok, info = uc_anular_pago(request=request, pago=pago)
        (messages.success if ok else messages.warning)(request, info)
    next_url = request.POST.get('next') or request.GET.get('next')
    return redirect(next_url or 'lista_pagos')
