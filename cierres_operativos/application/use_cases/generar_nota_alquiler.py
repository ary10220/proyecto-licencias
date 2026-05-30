from django.db import transaction
from django.core.exceptions import ValidationError
from ...infrastructure.models import PropuestaComercial, NotaAlquiler, Notificacion, DetalleNotifi
from empleados.models import Empleado

class GenerarNotaAlquilerCasoUso:
    """
    Caso de Uso del módulo de cierres: Vincula una Nota de Alquiler a una propuesta 
    existente y automatiza el registro de alertas inmediatas.
    """

    @transaction.atomic
    def ejecutar(self, propuesta_id: int, nro_nota: str, fecha_vencimiento_pago, empleados_a_notificar_ids: list):
        # 1. Validar existencia y estado de la propuesta
        try:
            propuesta = PropuestaComercial.objects.get(pk=propuesta_id)
        except PropuestaComercial.DoesNotExist:
            raise ValidationError("La propuesta comercial especificada no existe.")

        if propuesta.estado != 'PENDIENTE':
            raise ValidationError(f"Operación inválida. La propuesta ya se encuentra {propuesta.estado}.")

        # 2. Transición de estado de la propuesta comercial (Cierre operativo)
        propuesta.estado = 'APROBADA'
        propuesta.save()

        # 3. Generar la Nota de Alquiler heredando el Tenant y el Monto de la propuesta
        nota = NotaAlquiler.objects.create(
            tenant=propuesta.tenant,
            propuesta=propuesta,
            nro_nota=nro_nota,
            fecha_vencimiento_pago=fecha_vencimiento_pago,
            monto_pactado=propuesta.monto_total,
            estado_pago='PENDIENTE'
        )

        # 4. Registrar la alerta automática de cierre en la tabla de Notificaciones
        notificacion = Notificacion.objects.create(
            tenant=nota.tenant,
            titulo=f"Cierre de Alquiler Confirmado: Nota {nota.nro_nota}",
            mensaje=f"Se ha confirmado la propuesta {propuesta.codigo_propuesta}. El pago límite está fijado para el {fecha_vencimiento_pago}.",
            tipo='CIERRE_OPERATIVO',
            nota_alquiler=nota
        )

        # 5. Registrar el desglose para cada empleado destino en DetalleNotifi
        for empleado_id in empleados_a_notificar_ids:
            try:
                empleado = Empleado.objects.get(pk=empleado_id, activo=True)
                DetalleNotifi.objects.create(
                    notificacion=notificacion,
                    empleado_destino=empleado
                )
            except Empleado.DoesNotExist:
                continue

        return nota