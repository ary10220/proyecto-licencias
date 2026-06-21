import logging
from collections import Counter

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from licencias.models import Licencia
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envia un resumen ejecutivo por email a los usuarios suscritos cuando hay licencias proximas a vencer.'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()

        dias_aviso = getattr(settings, 'ALERTAS_DIAS_AVISO', [30, 15, 7, 1])
        fechas_objetivo = [hoy + timedelta(days=d) for d in dias_aviso]

        logger.info('enviar_alertas: inicio. Dias de aviso=%s, fechas objetivo=%s', dias_aviso, fechas_objetivo)

        # Una sola lectura de BD (con select_related/prefetch_related para evitar N+1).
        licencias_a_vencer = list(
            Licencia.objects
            .filter(fecha_vencimiento__in=fechas_objetivo)
            .select_related('tipo', 'empresa', 'tenant', 'proveedor')
            .prefetch_related('asignaciones__empleado')
            .order_by('fecha_vencimiento')
        )

        total = len(licencias_a_vencer)
        if total == 0:
            logger.info('enviar_alertas: sin licencias por vencer en las fechas objetivo. No se envia correo.')
            self.stdout.write(self.style.SUCCESS('Silencio. No hay licencias que venzan en los dias de aviso configurados.'))
            return

        destinatarios = list(
            User.objects
            .filter(perfil__recibir_alertas_vencimiento=True, is_active=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )
        if not destinatarios:
            fallback = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or settings.EMAIL_HOST_USER
            destinatarios = [fallback]
            logger.warning('enviar_alertas: ningun usuario suscrito. Usando fallback %s', fallback)

        # --- Agregaciones en memoria (un solo recorrido, sin queries extra ni N+1) ---
        conteo_dias = Counter()
        conteo_empresas = Counter()
        conteo_tipos = Counter()
        criticas = []

        for lic in licencias_a_vencer:
            dias = (lic.fecha_vencimiento - hoy).days
            conteo_dias[dias] += 1
            empresa_nombre = lic.empresa.nombre if lic.empresa else lic.tenant.nombre
            conteo_empresas[empresa_nombre] += 1
            conteo_tipos[lic.tipo.nombre] += 1
            if dias <= 1:
                criticas.append(lic)

        n1 = conteo_dias.get(1, 0)
        n7 = conteo_dias.get(7, 0)
        n15 = conteo_dias.get(15, 0)
        n30 = conteo_dias.get(30, 0)
        num_criticas = len(criticas)

        top_empresas = conteo_empresas.most_common(5)
        top_tipos = conteo_tipos.most_common(5)

        # --- Cuerpo: resumen ejecutivo, sin emojis, tono empresarial ---
        sep = '-' * 40
        lineas = []
        lineas.append('Estimado/a,')
        lineas.append('')
        lineas.append('Por medio del presente, le informamos del estado de licencias proximas a vencer')
        lineas.append('en el sistema de Gestion de Licencias.')
        lineas.append('')
        lineas.append(sep)
        lineas.append('RESUMEN GENERAL')
        lineas.append(sep)
        lineas.append(f'Total de licencias por vencer: {total}')
        lineas.append(f'Fecha del reporte: {hoy.strftime("%d/%m/%Y")}')
        lineas.append('')
        lineas.append(sep)
        lineas.append('DISTRIBUCION POR URGENCIA')
        lineas.append(sep)
        lineas.append(f'{"En 1 dia (Critico):".ljust(22)}{n1}')
        lineas.append(f'{"En 7 dias (Urgente):".ljust(22)}{n7}')
        lineas.append(f'{"En 15 dias:".ljust(22)}{n15}')
        lineas.append(f'{"En 30 dias:".ljust(22)}{n30}')
        lineas.append('')
        lineas.append(sep)
        lineas.append('TOP 5 EMPRESAS CON MAS VENCIMIENTOS')
        lineas.append(sep)
        for i, (nombre, cant) in enumerate(top_empresas, 1):
            lineas.append(f'{i}. {(nombre + ":").ljust(20)} {cant} licencias')
        lineas.append('')
        lineas.append(sep)
        lineas.append('TOP 5 TIPOS DE LICENCIA POR VENCER')
        lineas.append(sep)
        for i, (nombre, cant) in enumerate(top_tipos, 1):
            lineas.append(f'{i}. {(nombre + ":").ljust(20)} {cant} licencias')
        lineas.append('')
        lineas.append(sep)
        lineas.append('LICENCIAS CRITICAS (vencen en 1 dia o menos)')
        lineas.append(sep)
        if num_criticas == 0:
            lineas.append('No hay licencias con vencimiento critico.')
        else:
            for lic in criticas[:10]:
                empresa_nombre = lic.empresa.nombre if lic.empresa else lic.tenant.nombre
                asignacion = lic.usuario_activo
                empleado = asignacion.empleado.nombre_completo if asignacion else 'Libre (Sin asignar)'
                lineas.append(f'- {lic.tipo.nombre} ({lic.tipo.fabricante}) | Empresa: {empresa_nombre} | Usuario: {empleado}')
            if num_criticas > 10:
                lineas.append(f'... y {num_criticas - 10} licencias mas con vencimiento critico.')
        lineas.append('')
        lineas.append('Para revisar el detalle completo y gestionar las renovaciones, ingrese')
        lineas.append('al sistema en la siguiente direccion:')
        lineas.append('')
        lineas.append('http://127.0.0.1:8000/dashboard/')
        lineas.append('')
        lineas.append('Atentamente,')
        lineas.append('Sistema de Gestion de Licencias')

        mensaje = '\n'.join(lineas)

        logger.info('enviar_alertas: %s licencia(s), %s critica(s), enviando a %s destinatario(s): %s',
                    total, num_criticas, len(destinatarios), destinatarios)

        try:
            send_mail(
                subject=f'Alerta: {total} licencia(s) por vencer ({num_criticas} critica/s)',
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=destinatarios,
                fail_silently=False,
            )
            logger.info('enviar_alertas: correo enviado correctamente a %s destinatario(s).', len(destinatarios))
            self.stdout.write(self.style.SUCCESS(
                f'Alerta enviada a {len(destinatarios)} destinatario(s) para {total} licencia(s) ({num_criticas} critica/s).'
            ))
        except Exception as e:
            logger.error('enviar_alertas: error al enviar el correo: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'Error al enviar el correo: {e}'))
