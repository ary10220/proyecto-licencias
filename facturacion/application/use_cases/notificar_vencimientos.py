# facturacion/application/use_cases/notificar_vencimientos.py

from __future__ import annotations
from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from ...infrastructure.models import PropuestaLicencia, DetalleFactura

def uc_notificar_propuestas_por_vencer(dias_anticipacion: int = 5) -> int:
    """
    Busca propuestas en estado PENDIENTE que fueron creadas hace (5 - dias_anticipacion) 
    o cuya fecha base sumada a la validez comercial coincida con el rango de alerta.
    
    Si asumimos que una propuesta vence 5 días después de su campo 'fecha':
    fecha_propuesta + 5 días = hoy + dias_anticipacion
    """
    # Si las propuestas expiran por ejemplo a los 5 días de emitidas, 
    # buscamos las propuestas cuya (fecha de emisión) sea exactamente igual a:
    # hoy + dias_anticipacion - validez_comercial
    # Para simplificar y probar con tus datos reales, buscaremos propuestas 
    # cuya 'fecha' de emisión tenga exactamente los días de diferencia requeridos.
    
    fecha_objetivo = date.today() + timedelta(days=dias_anticipacion) - timedelta(days=5)
    
    # Filtramos usando el campo real 'fecha' reconocido por tu modelo
    propuestas = PropuestaLicencia.objects.filter(
        estado='PENDIENTE',
        fecha=fecha_objetivo
    ).select_related('tenant', 'empresa')
    
    contador = 0
    for propuesta in propuestas:
        asunto = f"[ALERTA] Propuesta Comercial {propuesta.numero} próxima a vencer"
        mensaje = (
            f"Estimado equipo comercial,\n\n"
            f"La propuesta comercial Nro: {propuesta.numero} emitida para la empresa "
            f"'{propuesta.empresa.nombre}' (Fecha Emisión: {propuesta.fecha}) está próxima a expirar "
            f"({dias_anticipacion} días restantes para el seguimiento obligatorio) y aún se encuentra PENDIENTE.\n\n"
            f"Por favor, realice el seguimiento correspondiente.\n\n"
            f"Atentamente,\nSistema de Gestión de Licencias"
        )
        
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        contador += 1
        
    return contador


def uc_notificar_contratos_por_vencer(dias_anticipacion: int = 15) -> int:
    """
    Busca ítems de facturas EMITIDAS (contratos vigentes de uso de software) 
    cuya fecha_vencimiento coincida con los días de anticipación y notifica al cliente.
    """
    fecha_alerta = date.today() + timedelta(days=dias_anticipacion)
    
    # DetalleFactura sí cuenta con el campo 'fecha_vencimiento' heredado en la emisión
    detalles_por_vencer = DetalleFactura.objects.filter(
        factura__estado='EMITIDA',
        fecha_vencimiento=fecha_alerta
    ).select_related('factura__empresa', 'tipo_licencia')
    
    contador = 0
    for detalle in detalles_por_vencer:
        factura = detalle.factura
        empresa = factura.empresa
        
        asunto = f"[AVISO DE VENCIMIENTO] Su servicio de licencia expira pronto"
        mensaje = (
            f"Estimado equipo de {empresa.nombre},\n\n"
            f"Le escribimos para notificarle que su contrato de uso de software asociado a la "
            f"licencia '{detalle.tipo_licencia.nombre}' (Cantidad: {detalle.cantidad}) está próximo a vencer.\n\n"
            f"Detalles del vencimiento:\n"
            f"- Factura de Origen: {factura.numero}\n"
            f"- Fecha de expiración: {detalle.fecha_vencimiento}\n"
            f"- Días restantes: {dias_anticipacion} días.\n\n"
            f"Para evitar interrupciones en el servicio, póngase en contacto con su ejecutivo comercial.\n\n"
            f"Atentamente,\nMamaya Tech"
        )
        
        correo_cliente = getattr(empresa, 'email', settings.EMAIL_HOST_USER)
        
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[correo_cliente],
            fail_silently=False,
        )
        contador += 1
        
    return contador