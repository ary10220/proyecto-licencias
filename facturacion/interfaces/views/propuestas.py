"""
Vistas de PropuestaLicencia (CU - Gestionar propuesta comercial).

Las views aqui delegan toda la logica de negocio a `application.use_cases.propuestas`.
Esta capa solo se encarga de:
  - Verificar permisos
  - Parsear request
  - Construir form / formset
  - Llamar al use case
  - Render / redirect / messages
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .base import exigir_permiso, filtros_comerciales_context
from ..forms import (
    DetallePropuestaFormSet,
    PropuestaAdminForm,
    PropuestaEditForm,
    PropuestaForm,
)
from ...application.use_cases import (
    uc_actualizar_propuesta_administrativa,
    uc_aprobar_propuesta,
    uc_crear_propuesta,
    uc_editar_propuesta,
    uc_eliminar_propuesta,
    uc_listar_propuestas,
    uc_rechazar_propuesta,
)
from ...infrastructure import repositories as repo


@login_required
@exigir_permiso('facturacion.view_propuestalicencia')
def lista_propuestas(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'todos')
    tenant_id = request.GET.get('tenant') or ''
    empresa_id = request.GET.get('empresa') or ''
    tipo_id = request.GET.get('tipo') or ''
    fecha_desde = request.GET.get('fecha_desde') or ''
    fecha_hasta = request.GET.get('fecha_hasta') or ''
    propuestas = uc_listar_propuestas(
        q=q,
        estado=estado,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        tipo_id=tipo_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    context = {
        'propuestas': propuestas,
        'q': q,
        'estado': estado,
        'tenant_filtro': tenant_id,
        'empresa_filtro': empresa_id,
        'tipo_filtro': tipo_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'puede_crear': request.user.has_perm('facturacion.add_propuestalicencia') or request.user.is_superuser,
        'facturacion_active': 'propuestas',
    }
    context.update(filtros_comerciales_context())
    return render(request, 'facturacion/propuestas/lista.html', context)


@login_required
@exigir_permiso('facturacion.add_propuestalicencia')
def crear_propuesta(request):
    if request.method == 'POST':
        propuesta_form = PropuestaForm(request.POST)
        detalle_formset = DetallePropuestaFormSet(request.POST)
        if propuesta_form.is_valid() and detalle_formset.is_valid():
            uc_crear_propuesta(
                request=request,
                propuesta_form=propuesta_form,
                detalle_formset=detalle_formset,
            )
            messages.success(request, 'Cotizacion registrada correctamente.')
            return redirect('lista_propuestas')
    else:
        propuesta_form = PropuestaForm()
        detalle_formset = DetallePropuestaFormSet()

    return render(request, 'facturacion/propuestas/form.html', {
        'propuesta_form': propuesta_form,
        'detalle_formset': detalle_formset,
        'modo': 'crear',
        'facturacion_active': 'propuestas',
    })


@login_required
@exigir_permiso('facturacion.change_propuestalicencia')
def editar_propuesta(request, pk):
    propuesta = repo.get_propuesta(pk)

    if propuesta.es_solo_lectura or propuesta.estado in {'RECHAZADA', 'ANULADA'}:
        return redirect('detalle_cotizacion', pk=pk)

    if propuesta.estado == 'APROBADA':
        if request.method == 'POST':
            propuesta_form = PropuestaAdminForm(request.POST, instance=propuesta)
            if propuesta_form.is_valid():
                uc_actualizar_propuesta_administrativa(
                    request=request,
                    propuesta_form=propuesta_form,
                )
                messages.success(request, 'Datos administrativos actualizados correctamente.')
                return redirect('detalle_cotizacion', pk=pk)
        else:
            propuesta_form = PropuestaAdminForm(instance=propuesta)

        return render(request, 'facturacion/propuestas/admin_form.html', {
            'propuesta': propuesta,
            'propuesta_form': propuesta_form,
            'facturacion_active': 'propuestas',
        })

    if request.method == 'POST':
        propuesta_form = PropuestaEditForm(request.POST, instance=propuesta)
        detalle_formset = DetallePropuestaFormSet(request.POST, instance=propuesta)
        if propuesta_form.is_valid() and detalle_formset.is_valid():
            uc_editar_propuesta(
                request=request,
                propuesta_form=propuesta_form,
                detalle_formset=detalle_formset,
            )
            messages.success(request, 'Cotizacion actualizada correctamente.')
            return redirect('lista_propuestas')
    else:
        propuesta_form = PropuestaEditForm(instance=propuesta)
        detalle_formset = DetallePropuestaFormSet(instance=propuesta)

    return render(request, 'facturacion/propuestas/form.html', {
        'propuesta_form': propuesta_form,
        'detalle_formset': detalle_formset,
        'propuesta': propuesta,
        'modo': 'editar',
        'facturacion_active': 'propuestas',
    })


@login_required
@exigir_permiso('facturacion.change_propuestalicencia')
def aprobar_propuesta(request, pk):
    propuesta = repo.get_propuesta(pk)
    if request.method == 'POST':
        ok, info = uc_aprobar_propuesta(request=request, propuesta=propuesta)
        (messages.success if ok else messages.warning)(request, info)
    return redirect('lista_propuestas')


@login_required
@exigir_permiso('facturacion.change_propuestalicencia')
def rechazar_propuesta(request, pk):
    propuesta = repo.get_propuesta(pk)
    if request.method == 'POST':
        ok, info = uc_rechazar_propuesta(request=request, propuesta=propuesta)
        (messages.success if ok else messages.warning)(request, info)
    return redirect('lista_propuestas')


@login_required
@exigir_permiso('facturacion.delete_propuestalicencia')
def eliminar_propuesta(request, pk):
    propuesta = repo.get_propuesta(pk)
    if request.method == 'POST':
        ok, info = uc_eliminar_propuesta(request=request, propuesta=propuesta)
        (messages.success if ok else messages.error)(request, info)
    return redirect('lista_propuestas')


@login_required
@exigir_permiso('facturacion.view_propuestalicencia')
def detalle_cotizacion(request, pk):
    """
    Vista de solo lectura de una cotizacion.

    Muestra todos los datos (lineas, totales, descuentos) sin permitir
    edicion. Se usa para cotizaciones APROBADAS o FACTURADAS donde la
    edicion esta bloqueada.
    """
    propuesta = repo.get_propuesta(pk)
    return render(request, 'facturacion/propuestas/detalle.html', {
        'propuesta': propuesta,
        'facturacion_active': 'propuestas',
        'es_lectura': True,
    })


@login_required
@exigir_permiso('facturacion.view_propuestalicencia')
def pdf_cotizacion(request, pk):
    """Genera PDF profesional de la cotizacion. ?download=1 fuerza descarga."""
    from facturacion.services import cotizacion_pdf_response
    propuesta = repo.get_propuesta(pk)
    download = request.GET.get('download') == '1'
    preview = request.GET.get('preview') == '1'
    paper_size = request.GET.get('paper') or 'letter'
    return cotizacion_pdf_response(propuesta, download=download, preview=preview, paper_size=paper_size)


@login_required
@exigir_permiso('facturacion.view_propuestalicencia')
def pdf_contrato(request, pk):
    """Genera PDF de contrato comercial (APROBADA o FACTURADA). ?download=1 fuerza descarga."""
    from facturacion.services import contrato_pdf_response
    propuesta = repo.get_propuesta(pk)
    if propuesta.estado not in ('APROBADA', 'FACTURADA'):
        from django.contrib import messages
        messages.warning(request, "Solo se puede generar contrato de cotizaciones APROBADAS o FACTURADAS.")
        return redirect('detalle_cotizacion', pk=pk)
    download = request.GET.get('download') == '1'
    preview = request.GET.get('preview') == '1'
    paper_size = request.GET.get('paper') or 'letter'
    return contrato_pdf_response(propuesta, download=download, preview=preview, paper_size=paper_size)
