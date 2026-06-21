"""
================================================================================
CU - Gestionar facturas
================================================================================
Permite emitir, actualizar, anular y eliminar facturas. Una factura emitida
puede generar stock de Licencias automaticamente (1 Licencia por unidad
en cada DetalleFactura).

Actores:        A1 (Administrador), A2 (Ejecutivo Comercial)
Pre-condicion:  Sesion activa con permisos de facturas y licencias.
Post-condicion: La accion queda registrada en bitacora.

Reglas de negocio:
  - Si la factura tiene `stock_generado=True`, NO se puede eliminar.
  - Si la factura ya esta ANULADA, NO se puede editar.
  - Al emitir una factura con estado EMITIDA, se genera automaticamente
    el stock de licencias (1 por unidad en cada detalle).
  - Anular una factura cambia su estado a ANULADA pero no toca el stock
    de licencias ya generado (eso requiere una accion correctiva manual).
================================================================================
"""

from __future__ import annotations

from django.db import transaction

from bitacora.actions import (
    log_factura_anular,
    log_factura_crear,
    log_factura_editar,
    log_factura_eliminar,
    log_factura_generar_stock,
)
from ...infrastructure import repositories as repo
from ...infrastructure.models import Factura


def _resolver_proveedor_para_factura(detalles_propuesta):
    """Toma el proveedor default de los productos cotizados."""
    for detalle in detalles_propuesta:
        proveedor = getattr(detalle.tipo_licencia, 'proveedor_default', None)
        if proveedor:
            return proveedor

    from licencias.models import Proveedor
    proveedor_activo = Proveedor.objects.filter(activo=True).order_by('nombre').first()
    return proveedor_activo or Proveedor.objects.order_by('nombre').first()


def uc_listar_facturas(
    *,
    q: str = "",
    estado: str = "todos",
    tenant_id: str | None = None,
    empresa_id: str | None = None,
    tipo_id: str | None = None,
    stock: str = "todos",
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    return repo.list_facturas(
        q=q,
        estado=estado,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        tipo_id=tipo_id,
        stock=stock,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


def uc_crear_factura(*, request, factura_form, detalle_form) -> Factura:
    """
    Persiste factura + detalle en transaccion.

    Si el estado es EMITIDA y el stock aun no fue generado, ejecuta
    `uc_generar_stock_factura` para crear el stock de licencias asociado.
    """
    with transaction.atomic():
        factura = factura_form.save()
        detalle = detalle_form.save(commit=False)
        detalle.factura = factura
        detalle.save()
        log_factura_crear(request, factura)

        if factura.estado == 'EMITIDA' and not factura.stock_generado:
            cantidad = uc_generar_stock_factura(request=request, factura=factura)
            log_factura_generar_stock(request, factura, cantidad)

    return factura


def uc_editar_factura(*, request, factura_form, detalle_form) -> tuple[bool, str, Factura | None]:
    """
    Actualiza factura. Bloquea edicion si la factura ya esta ANULADA.

    Retorna: (ok, mensaje, factura | None)
    """
    factura_instance = factura_form.instance
    if factura_instance.estado == 'ANULADA':
        return False, "No se puede editar una factura anulada.", None

    with transaction.atomic():
        factura = factura_form.save()
        detalle = detalle_form.save(commit=False)
        detalle.factura = factura
        detalle.save()
    log_factura_editar(request, factura)
    return True, "Factura actualizada. El stock ya generado no se recalcula automaticamente.", factura


def uc_editar_datos_fiscales_factura(*, request, factura_form) -> tuple[bool, str, Factura | None]:
    """Actualiza solo datos fiscales, pago, estado y observaciones."""
    factura_instance = factura_form.instance
    if factura_instance.estado == 'ANULADA':
        return False, "No se puede editar una factura anulada.", None

    factura = factura_form.save()
    log_factura_editar(request, factura)
    return True, "Datos fiscales de la factura actualizados.", factura


def uc_anular_factura(*, request, factura: Factura) -> tuple[bool, str]:
    """
    Cambia estado de la factura a ANULADA.
    No elimina ni revierte el stock de licencias ya generado.
    """
    if factura.estado == 'ANULADA':
        return False, "La factura ya estaba anulada."
    factura.estado = 'ANULADA'
    factura.save(update_fields=['estado'])
    log_factura_anular(request, factura)
    return True, f"Factura {factura.numero} anulada."


def uc_eliminar_factura(*, request, factura: Factura) -> tuple[bool, str]:
    """
    Borrado fisico.
    Regla: si `stock_generado=True`, NO se puede eliminar
    (las licencias ya fueron creadas en el inventario).
    """
    if factura.stock_generado:
        return False, "No se elimino la factura porque ya genero stock de licencias. Use 'Anular' en su lugar."
    label = str(factura)
    repo.delete_factura(factura)
    log_factura_eliminar(request, label)
    return True, f"Factura '{label}' eliminada."


def uc_generar_stock_factura(*, request, factura: Factura) -> int:
    """
    Genera el stock de Licencias a partir de los detalles de la factura.

    Returns:
        Cantidad total de licencias creadas.
    """
    cantidad_total = 0
    for detalle in factura.detalles.all():
        creadas = detalle.crear_stock()
        cantidad_total += len(creadas)

    factura.stock_generado = True
    factura.save(update_fields=['stock_generado'])
    return cantidad_total


def uc_emitir_factura_desde_propuesta(
    *, request, propuesta, proveedor=None, numero=None, fecha=None,
    razon_social='', nit='', direccion_fiscal='', metodo_pago='CONTADO',
    observaciones='', fecha_vencimiento_default=None
) -> tuple[bool, str, "Factura | None"]:
    """
    Crea una Factura a partir de una PropuestaLicencia APROBADA.

    HEREDA AUTOMATICAMENTE de la propuesta:
      - tenant, empresa
      - cada DetallePropuesta -> DetalleFactura (tipo, cantidad, precio,
        fechas inicio/fin, descuentos por linea, observaciones)
      - descuento_porcentaje global, descuento_monto global, impuesto_porcentaje

    El formulario de factura solo pide datos adicionales de facturacion:
      numero (autogenerado si vacio), fecha, razon_social, nit,
      direccion_fiscal, metodo_pago, observaciones extra.

    Genera stock de licencias automaticamente (factura EMITIDA).
    Marca la propuesta como FACTURADA al exito.

    Reglas:
      - La propuesta debe estar en estado APROBADA.
      - Una propuesta solo puede facturarse una vez.
    """
    from datetime import date, timedelta
    if fecha is None:
        fecha = date.today()
    venc_default = fecha_vencimiento_default or (date.today() + timedelta(days=365))

    with transaction.atomic():
        propuesta = (
            propuesta.__class__.objects
            .select_for_update()
            .select_related('tenant', 'empresa')
            .prefetch_related('detalles__tipo_licencia__proveedor_default')
            .get(pk=propuesta.pk)
        )
        if propuesta.estado != 'APROBADA':
            return False, f"Solo se puede facturar una propuesta APROBADA (esta: {propuesta.get_estado_display()}).", None

        detalles_propuesta = list(propuesta.detalles.select_related('tipo_licencia__proveedor_default').all())
        if not detalles_propuesta:
            return False, "La propuesta no tiene detalles para facturar.", None

        proveedor = proveedor or _resolver_proveedor_para_factura(detalles_propuesta)
        if not proveedor:
            return False, "No se encontro proveedor para la factura. Configura un proveedor default en el catalogo de licencias.", None

        factura = Factura.objects.create(
            propuesta=propuesta,
            proveedor=proveedor,
            tenant=propuesta.tenant,
            empresa=propuesta.empresa,
            numero=numero or '',  # vacio -> autogenera FAC-YYYY-NNNN
            fecha=fecha,
            razon_social=razon_social or propuesta.empresa.nombre,
            nit=nit,
            direccion_fiscal=direccion_fiscal,
            metodo_pago=metodo_pago,
            estado='EMITIDA',
            # HEREDAR descuentos e impuesto de la propuesta
            descuento_porcentaje=propuesta.descuento_porcentaje,
            descuento_monto=propuesta.descuento_monto,
            impuesto_porcentaje=propuesta.impuesto_porcentaje,
            observaciones=observaciones or propuesta.observaciones or '',
        )

        # Copiar detalles propuesta -> detalle factura (con fechas y descuentos)
        from ...infrastructure.models import DetalleFactura
        for d in detalles_propuesta:
            # fecha_vencimiento: usar fecha_fin_uso si esta, sino el default
            fecha_vto = d.fecha_fin_uso or venc_default
            DetalleFactura.objects.create(
                factura=factura,
                tipo_licencia=d.tipo_licencia,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                fecha_vencimiento=fecha_vto,
                fecha_inicio_uso=d.fecha_inicio_uso,
                fecha_fin_uso=d.fecha_fin_uso,
                descuento_porcentaje=d.descuento_porcentaje,
                descuento_monto=d.descuento_monto,
                observaciones=d.observaciones,
            )

        log_factura_crear(request, factura)

        # Generar stock de licencias automaticamente
        cantidad = uc_generar_stock_factura(request=request, factura=factura)
        log_factura_generar_stock(request, factura, cantidad)

        # Marcar propuesta como FACTURADA
        propuesta.estado = 'FACTURADA'
        propuesta.save(update_fields=['estado'])

    return True, f"Factura {factura.numero} emitida desde {propuesta.numero} ({cantidad} licencias generadas).", factura
