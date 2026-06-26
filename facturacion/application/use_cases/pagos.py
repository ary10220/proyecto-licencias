"""Casos de uso para gestion de pagos de facturas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import transaction

from bitacora.actions.facturacion import log_pago_anular, log_pago_editar, log_pago_registrar
from ...services import enviar_factura_pagada_por_email
from ...infrastructure import repositories as repo
from ...infrastructure.models import Factura, PagoFactura
from .facturas import uc_generar_stock_factura


def _adjuntar_resultado_envio_factura(request, factura: Factura, mensaje: str, debe_enviar: bool) -> str:
    if not debe_enviar:
        return mensaje
    _, info_email = enviar_factura_pagada_por_email(factura, request=request)
    return f"{mensaje} {info_email}" if info_email else mensaje


def uc_listar_pagos(
    *,
    q: str = "",
    estado_pago: str = "todos",
    tenant_id: str | None = None,
    empresa_id: str | None = None,
    metodo_pago: str = "todos",
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    facturas = repo.list_facturas_para_pagos(
        q=q,
        estado_pago=estado_pago,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        metodo_pago=metodo_pago,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    pagos_recientes = repo.list_pagos_recientes(
        q=q,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        metodo_pago=metodo_pago,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return facturas, pagos_recientes


def construir_resumen_pagos(facturas) -> dict:
    total_facturado = Decimal('0')
    total_pagado = Decimal('0')
    pendientes = parciales = pagadas = anuladas = 0

    for factura in facturas:
        total_facturado += Decimal(str(factura.total))
        total_pagado += Decimal(str(factura.monto_pagado))
        estado = factura.estado_pago_calculado
        if estado == 'PAGADA':
            pagadas += 1
        elif estado == 'PAGO_PARCIAL':
            parciales += 1
        elif estado == 'ANULADA':
            anuladas += 1
        else:
            pendientes += 1

    saldo = total_facturado - total_pagado
    return {
        'total_facturado': total_facturado,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo if saldo > 0 else Decimal('0'),
        'pendientes': pendientes,
        'parciales': parciales,
        'pagadas': pagadas,
        'anuladas': anuladas,
        'cantidad_facturas': len(facturas),
    }


def uc_registrar_pago(*, request, factura: Factura, pago_form) -> tuple[bool, str, PagoFactura | None]:
    if factura.estado == 'ANULADA':
        return False, "No se pueden registrar pagos en una factura anulada.", None
    if factura.saldo_pendiente <= 0:
        return False, "La factura ya no tiene saldo pendiente.", None

    debe_enviar_factura = False
    with transaction.atomic():
        factura = Factura.objects.select_for_update().get(pk=factura.pk)
        estado_anterior = factura.estado_pago_calculado
        pago = pago_form.save(commit=False)
        if factura.saldo_pendiente <= 0:
            return False, "La factura ya no tiene saldo pendiente.", None
        if pago.monto > factura.saldo_pendiente:
            return False, "El monto supera el saldo pendiente actualizado.", None
        pago.factura = factura
        pago.creado_por = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        pago.estado = PagoFactura.ESTADO_ACTIVO
        pago.save()

        factura.sincronizar_estado_pago(metodo_pago=pago.metodo_pago)
        if factura.estado == 'PAGADA' and not factura.stock_generado:
            uc_generar_stock_factura(request=request, factura=factura)
        debe_enviar_factura = estado_anterior != 'PAGADA' and factura.estado == 'PAGADA'

        log_pago_registrar(request, pago)

    mensaje = f"Pago registrado correctamente para la factura {factura.numero}."
    mensaje = _adjuntar_resultado_envio_factura(request, factura, mensaje, debe_enviar_factura)
    return True, mensaje, pago


def uc_editar_pago(*, request, pago: PagoFactura, pago_form) -> tuple[bool, str, PagoFactura | None]:
    if pago.estado == PagoFactura.ESTADO_ANULADO:
        return False, "No se puede editar un pago anulado.", None

    debe_enviar_factura = False
    with transaction.atomic():
        pago_bloqueado = (
            PagoFactura.objects
            .select_for_update()
            .select_related('factura')
            .get(pk=pago.pk)
        )
        if pago_bloqueado.estado == PagoFactura.ESTADO_ANULADO:
            return False, "No se puede editar un pago anulado.", None

        factura = Factura.objects.select_for_update().get(pk=pago_bloqueado.factura_id)
        estado_anterior = factura.estado_pago_calculado
        pago_actualizado = pago_form.save(commit=False)
        saldo_disponible = factura.saldo_pendiente + pago_bloqueado.monto
        if pago_actualizado.monto > saldo_disponible:
            return False, f"El monto supera el saldo disponible actualizado ({saldo_disponible:.2f}).", None

        monto_anterior = pago_bloqueado.monto
        pago_bloqueado.fecha_pago = pago_actualizado.fecha_pago
        pago_bloqueado.monto = pago_actualizado.monto
        pago_bloqueado.metodo_pago = pago_actualizado.metodo_pago
        pago_bloqueado.referencia = pago_actualizado.referencia
        pago_bloqueado.comprobante = pago_actualizado.comprobante
        pago_bloqueado.observaciones = pago_actualizado.observaciones
        pago_bloqueado.save()

        factura.sincronizar_estado_pago(metodo_pago=pago_bloqueado.metodo_pago)
        if factura.estado == 'PAGADA' and not factura.stock_generado:
            uc_generar_stock_factura(request=request, factura=factura)
        debe_enviar_factura = estado_anterior != 'PAGADA' and factura.estado == 'PAGADA'

        log_pago_editar(request, pago_bloqueado, monto_anterior=monto_anterior)

    mensaje = f"Pago de la factura {pago_bloqueado.factura.numero} actualizado correctamente."
    mensaje = _adjuntar_resultado_envio_factura(request, factura, mensaje, debe_enviar_factura)
    return True, mensaje, pago_bloqueado


def uc_crear_pago_directo(
    *,
    request,
    factura: Factura,
    monto,
    metodo_pago: str,
    referencia: str = "",
    observaciones: str = "",
) -> tuple[bool, str, PagoFactura | None]:
    from ...interfaces.forms import PagoFacturaForm

    form = PagoFacturaForm(
        data={
            'fecha_pago': date.today().isoformat(),
            'monto': monto,
            'metodo_pago': metodo_pago,
            'referencia': referencia,
            'observaciones': observaciones,
        },
        factura=factura,
    )
    if not form.is_valid():
        return False, "No se pudo registrar el pago automatico.", None
    return uc_registrar_pago(request=request, factura=factura, pago_form=form)


def uc_anular_pago(*, request, pago: PagoFactura) -> tuple[bool, str]:
    if pago.estado == PagoFactura.ESTADO_ANULADO:
        return False, "El pago ya estaba anulado."

    with transaction.atomic():
        pago = PagoFactura.objects.select_for_update().select_related('factura').get(pk=pago.pk)
        pago.estado = PagoFactura.ESTADO_ANULADO
        pago.save(update_fields=['estado', 'actualizado_en'])
        pago.factura.sincronizar_estado_pago()
        log_pago_anular(request, pago)

    return True, f"Pago de la factura {pago.factura.numero} anulado correctamente."
