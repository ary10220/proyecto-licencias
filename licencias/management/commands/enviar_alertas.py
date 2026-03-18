from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from licencias.models import Licencia # Ojo: Asegúrate que 'licencias' es el nombre de tu app
from django.conf import settings

class Command(BaseCommand):
    help = 'Envía una única alerta exactamente 30 días antes del vencimiento de una licencia.'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        
        # Calculamos la fecha EXACTA de aquí a un mes (30 días)
        fecha_objetivo = hoy + timedelta(days=30)

        # Buscamos en la base de datos SOLO las licencias que vencen en ese día exacto.
        # Ignoramos por completo las que ya vencieron o las que vencen en 29 o 31 días.
        licencias_a_vencer = Licencia.objects.filter(fecha_vencimiento=fecha_objetivo)

        # Si hoy no hay ninguna licencia que cumpla esa condición, el script termina en silencio.
        if not licencias_a_vencer.exists():
            self.stdout.write(self.style.SUCCESS(f'Silencio. No hay licencias que venzan exactamente el {fecha_objetivo.strftime("%d/%m/%Y")}.'))
            return

        # Si encontró coincidencias, armamos un correo limpio y directo
        mensaje = f"Hola Equipo,\n\nEste es un recordatorio automático. Las siguientes licencias vencerán exactamente en 30 días (el {fecha_objetivo.strftime('%d/%m/%Y')}):\n\n"

        for lic in licencias_a_vencer:
            # Buscamos a quién está asignada para dar más contexto en el correo
            if lic.usuario_activo:
                empleado = lic.usuario_activo.empleado.nombre_completo
            else:
                empleado = "Libre (Sin asignar)"

            mensaje += f"- Software: {lic.tipo.nombre} ({lic.tipo.fabricante})\n"
            mensaje += f"  Empresa: {lic.empresa.nombre if lic.empresa else lic.tenant.nombre}\n"
            mensaje += f"  Usuario Actual: {empleado}\n"
            mensaje += f"  Proveedor: {lic.proveedor.nombre if lic.proveedor else 'Directo'}\n\n"

        mensaje += "Por favor, evalúen si se requiere renovar la compra con el proveedor.\n\nSaludos,\nSistema de Gestión de Licencias."

        # Pon los correos de los gerentes y el tuyo
        destinatarios = ['arianyclaure@gmail.com']
        
        try:
            send_mail(
                subject=f'🔔 Renovación requerida: Licencias vencen el {fecha_objetivo.strftime("%d/%m/%Y")}',
                message=mensaje,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=destinatarios,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'¡Alerta enviada para las licencias del {fecha_objetivo.strftime("%d/%m/%Y")}!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al enviar el correo: {e}'))