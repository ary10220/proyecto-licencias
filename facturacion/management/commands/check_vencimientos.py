# facturacion/management/commands/check_vencimientos.py

from django.core.management.base import BaseCommand
from facturacion.application.use_cases.notificar_vencimientos import (
    uc_notificar_propuestas_por_vencer,
    uc_notificar_contratos_por_vencer
)

class Command(BaseCommand):
    help = "Evalúa de forma automática las propuestas comerciales y contratos (facturas) próximos a vencer y envía alertas por correo electrónico."

    def add_arguments(self, parser):
        # Permitimos parametrizar los días de anticipación desde la consola si se desea
        parser.add_argument(
            '--dias-propuestas',
            type=int,
            default=5,
            help='Días de anticipación para alertar sobre propuestas pendientes.'
        )
        parser.add_argument(
            '--dias-contratos',
            type=int,
            default=15,
            help='Días de anticipación para avisar sobre vencimientos de contratos de licencias.'
        )

    def handle(self, *args, **options):
        dias_p = options['dias_propuestas']
        dias_c = options['dias_contratos']

        self.stdout.write(self.style.WARNING("=== Iniciando proceso automático de verificación ==="))

        try:
            # 1. Procesar alertas de propuestas comerciales
            self.stdout.write(f"Buscando propuestas que vencen en {dias_p} días...")
            propuestas_procesadas = uc_notificar_propuestas_por_vencer(dias_anticipacion=dias_p)
            self.stdout.write(self.style.SUCCESS(f"-> Se enviaron {propuestas_procesadas} alertas de propuestas."))

            # 2. Procesar alertas de contratos / fin de uso de licencias
            self.stdout.write(f"Buscando contratos de licencias que vencen en {dias_c} días...")
            contratos_procesados = uc_notificar_contratos_por_vencer(dias_anticipacion=dias_c)
            self.stdout.write(self.style.SUCCESS(f"-> Se enviaron {contratos_procesados} notificaciones de contratos."))

            self.stdout.write(self.style.SUCCESS("=== Proceso finalizado exitosamente ==="))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ocurrió un error crítico durante la ejecución: {str(e)}"))