from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from licencias.models import PropuestaLicencia, NotaAlquiler, Notificacion, DetalleNotificacion

def uc_crear_nota_alquiler(*, request, propuesta_id, numero_nota, monto, dias_para_vencer) -> NotaAlquiler:
    """
    Caso de Uso: Registra la Nota de Alquiler, aprueba la propuesta comercial
    y genera alertas automáticas de vencimiento en las tablas de Notificaciones.
    """
    # Garantizamos atomicidad: O se guarda la nota y la alerta juntas, o nada.
    with transaction.atomic():
        
        # 1. Recuperar la propuesta comercial existente
        propuesta = PropuestaLicencia.objects.get(id=propuesta_id)
        
        # 2. Validar idempotencia (que no tenga ya una nota asociada)
        if hasattr(propuesta, 'nota_alquiler'):
            raise ValueError("Esta propuesta ya posee una Nota de Alquiler asociada.")
            
        # 3. Transición de estado de la propuesta a APROBADA
        propuesta.estado = 'APROBADA'
        propuesta.save()
        
        # 4. Cálculo de línea de tiempo operativa
        fecha_actual = timezone.now().date()
        fecha_vencimiento = fecha_actual + timedelta(days=dias_para_vencer)
        
        # 5. Persistencia del Cierre Operativo (NotaAlquiler)
        nota = NotaAlquiler.objects.create(
            propuesta=propuesta,
            numero_nota=numero_nota,
            fecha_emision=fecha_actual,
            fecha_vencimiento_pago=fecha_vencimiento,
            monto_total=monto,
            procesado=True
        )
        
        # 6. Despacho síncrono del subsistema de alertas (Trigger lógico)
        # La alerta saltará preventivamente 3 días antes del vencimiento real del pago
        fecha_disparo_alerta = fecha_vencimiento - timedelta(days=3)
        
        alerta = Notificacion.objects.create(
            tenant=propuesta.tenant,
            tipo='VENCIMIENTO_PAGO',
            fecha_alerta=fecha_disparo_alerta,
            estado='PENDIENTE'
        )
        
        DetalleNotificacion.objects.create(
            notificacion=alerta,
            asunto=f"ALERTA CRÍTICA: Vencimiento de Pago de Nota {nota.numero_nota}",
            mensaje=(
                f"Alerta preventiva para la empresa {propuesta.empresa.nombre}. "
                f"La Nota de Alquiler {nota.numero_nota} por un monto de ${nota.monto_total} USD "
                f"vencerá el próximo {nota.fecha_vencimiento_pago}."
            ),
            referencia_nota=nota
        )
        
        return nota