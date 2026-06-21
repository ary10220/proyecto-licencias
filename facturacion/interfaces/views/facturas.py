"""
Vistas de Factura (CU - Gestionar factura).

Delega toda la logica a `application.use_cases.facturas`.
"""

from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .base import exigir_permiso, filtros_comerciales_context
from ..forms import DetalleFacturaForm, FacturaFiscalForm, FacturaForm
from ...application.use_cases import (
    uc_anular_factura,
    uc_crear_factura,
    uc_editar_datos_fiscales_factura,
    uc_editar_factura,
    uc_eliminar_factura,
    uc_listar_facturas,
)
from ...infrastructure import repositories as repo


@login_required
@exigir_permiso('facturacion.view_factura')
def lista_facturas(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'todos')
    tenant_id = request.GET.get('tenant') or ''
    empresa_id = request.GET.get('empresa') or ''
    tipo_id = request.GET.get('tipo') or ''
    stock = request.GET.get('stock', 'todos')
    fecha_desde = request.GET.get('fecha_desde') or ''
    fecha_hasta = request.GET.get('fecha_hasta') or ''
    facturas = uc_listar_facturas(
        q=q,
        estado=estado,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        tipo_id=tipo_id,
        stock=stock,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    context = {
        'facturas': facturas,
        'q': q,
        'estado': estado,
        'tenant_filtro': tenant_id,
        'empresa_filtro': empresa_id,
        'tipo_filtro': tipo_id,
        'stock_filtro': stock,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'puede_crear': request.user.has_perm('facturacion.add_factura') or request.user.is_superuser,
        'facturacion_active': 'facturas',
    }
    context.update(filtros_comerciales_context())
    return render(request, 'facturacion/facturas/lista.html', context)


@login_required
@exigir_permiso('facturacion.add_factura')
@exigir_permiso('licencias.add_licencia')
def crear_factura(request):
    if request.method == 'POST':
        factura_form = FacturaForm(request.POST)
        detalle_form = DetalleFacturaForm(request.POST)
        if factura_form.is_valid() and detalle_form.is_valid():
            uc_crear_factura(
                request=request,
                factura_form=factura_form,
                detalle_form=detalle_form,
            )
            messages.success(request, 'Factura registrada correctamente.')
            return redirect('lista_facturas')
    else:
        factura_form = FacturaForm()
        detalle_form = DetalleFacturaForm()

    return render(request, 'facturacion/facturas/form.html', {
        'factura_form': factura_form,
        'detalle_form': detalle_form,
        'modo': 'crear',
        'facturacion_active': 'facturas',
    })


@login_required
@exigir_permiso('facturacion.change_factura')
def editar_factura(request, pk):
    factura = repo.get_factura(pk)

    if request.method == 'POST':
        factura_form = FacturaFiscalForm(request.POST, instance=factura)
        if factura_form.is_valid():
            ok, info, _ = uc_editar_datos_fiscales_factura(
                request=request,
                factura_form=factura_form,
            )
            (messages.success if ok else messages.error)(request, info)
            if ok:
                return redirect('detalle_factura', pk=factura.pk)
    else:
        factura_form = FacturaFiscalForm(instance=factura)

    return render(request, 'facturacion/facturas/form_fiscal.html', {
        'factura': factura,
        'factura_form': factura_form,
        'modo': 'editar',
        'facturacion_active': 'facturas',
    })


@login_required
@exigir_permiso('facturacion.change_factura')
def anular_factura(request, pk):
    factura = repo.get_factura(pk)
    if request.method == 'POST':
        ok, info = uc_anular_factura(request=request, factura=factura)
        (messages.success if ok else messages.warning)(request, info)
    return redirect('lista_facturas')


@login_required
@exigir_permiso('facturacion.delete_factura')
def eliminar_factura(request, pk):
    factura = repo.get_factura(pk)
    if request.method == 'POST':
        ok, info = uc_eliminar_factura(request=request, factura=factura)
        (messages.success if ok else messages.error)(request, info)
    return redirect('lista_facturas')


from ...infrastructure.models import PropuestaLicencia


@login_required
@exigir_permiso('facturacion.add_factura')
@exigir_permiso('licencias.add_licencia')
def emitir_factura_desde_propuesta(request, propuesta_id):
    """
    Pre-rellena el form de Factura con datos de la PropuestaLicencia
    aprobada. Al hacer POST, crea la Factura + DetalleFactura + stock
    de licencias en una sola transaccion.
    """
    from ...application.use_cases import uc_emitir_factura_desde_propuesta

    propuesta = PropuestaLicencia.objects.select_related('empresa', 'tenant') \
        .prefetch_related('detalles__tipo_licencia__proveedor_default').filter(pk=propuesta_id).first()
    if not propuesta:
        messages.error(request, "Cotizacion no encontrada.")
        return redirect('lista_cotizaciones')

    if propuesta.estado != 'APROBADA':
        messages.warning(
            request,
            f"Solo se puede facturar una propuesta APROBADA (esta: {propuesta.get_estado_display()})."
        )
        return redirect('lista_cotizaciones')

    if request.method == 'POST':
        razon_social = (request.POST.get('razon_social') or '').strip()
        nit = (request.POST.get('nit') or '').strip()
        direccion_fiscal = (request.POST.get('direccion_fiscal') or '').strip()
        metodo_pago = (request.POST.get('metodo_pago') or 'CONTADO').strip()
        observaciones = (request.POST.get('observaciones') or '').strip()

        ok, info, factura = uc_emitir_factura_desde_propuesta(
            request=request,
            propuesta=propuesta,
            fecha=date.today(),
            razon_social=razon_social,
            nit=nit,
            direccion_fiscal=direccion_fiscal,
            metodo_pago=metodo_pago,
            observaciones=observaciones,
        )
        (messages.success if ok else messages.error)(request, info)
        if ok:
            return redirect('detalle_factura', pk=factura.pk)

    return render(request, 'facturacion/facturas/emitir_desde_propuesta.html', {
        'propuesta': propuesta,
        'fecha_emision': date.today(),
        'facturacion_active': 'facturas',
    })


@login_required
@exigir_permiso('facturacion.add_factura')
@exigir_permiso('licencias.add_licencia')
def seleccionar_cotizacion(request):
    """
    Punto de entrada para crear una factura.

    Muestra un selector con las cotizaciones APROBADAS pendientes de facturar.
    Al seleccionar una, redirige a `emitir_factura_desde_propuesta` que
    pre-carga todos los datos.
    """
    cotizaciones_aprobadas = (
        PropuestaLicencia.objects
        .filter(estado='APROBADA')
        .select_related('empresa', 'tenant')
        .prefetch_related('detalles__tipo_licencia')
        .order_by('-fecha', '-id')
    )

    if request.method == 'POST':
        propuesta_id = request.POST.get('cotizacion_id')
        if propuesta_id:
            return redirect('emitir_factura_desde_cotizacion', propuesta_id=propuesta_id)
        messages.warning(request, "Selecciona una cotizacion para continuar.")

    return render(request, 'facturacion/facturas/seleccionar_cotizacion.html', {
        'cotizaciones': cotizaciones_aprobadas,
        'facturacion_active': 'facturas',
    })


@login_required
@exigir_permiso('facturacion.view_factura')
def detalle_factura(request, pk):
    """Vista de solo lectura de una factura."""
    from ...infrastructure.models import Factura
    factura = get_object_or_404(
        Factura.objects.select_related('empresa', 'tenant', 'proveedor', 'propuesta')
                       .prefetch_related('detalles__tipo_licencia'),
        pk=pk,
    )
    return render(request, 'facturacion/facturas/detalle.html', {
        'factura': factura,
        'facturacion_active': 'facturas',
    })


@login_required
@exigir_permiso('facturacion.view_factura')
def pdf_factura(request, pk):
    """Genera PDF profesional de la factura. ?download=1 fuerza descarga."""
    from facturacion.services import factura_pdf_response
    from ...infrastructure.models import Factura
    factura = get_object_or_404(
        Factura.objects.select_related('empresa', 'tenant', 'proveedor', 'propuesta')
                       .prefetch_related('detalles__tipo_licencia'),
        pk=pk,
    )
    download = request.GET.get('download') == '1'
    preview = request.GET.get('preview') == '1'
    paper_size = request.GET.get('paper') or 'letter'
    return factura_pdf_response(factura, download=download, preview=preview, paper_size=paper_size)
