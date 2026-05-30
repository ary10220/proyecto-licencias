from django.db import models
from django.utils import timezone
from licencias.models import Tenant, Empresa
from empleados.models import Empleado

class PropuestaComercial(models.Model):
    """Precondición: Propuesta comercial que precede a la Nota de Alquiler."""
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    codigo_propuesta = models.CharField(max_length=50, unique=True)
    fecha_creacion = models.DateField(auto_now_add=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"Propuesta {self.codigo_propuesta} - {self.estado}"


class NotaAlquiler(models.Model):
    """Cierre Operativo: Paso final que confirma y ejecuta una propuesta comercial (0..1 a 1)."""
    ESTADOS_PAGO = (
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PAGADO', 'Pagado'),
        ('VENCIDO', 'Vencido / En Mora'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    propuesta = models.OneToOneField(PropuestaComercial, on_delete=models.PROTECT, related_name='nota_alquiler')
    nro_nota = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(default=timezone.now)
    fecha_vencimiento_pago = models.DateField(help_text="Fecha límite de pago que disparará las alertas automáticas")
    monto_pactado = models.DecimalField(max_digits=12, decimal_places=2)
    estado_pago = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='PENDIENTE')

    def __str__(self):
        return f"Nota Alquiler {self.nro_nota} | Propuesta: {self.propuesta.codigo_propuesta}"


class Notificacion(models.Model):
    """Módulo Auxiliar: Cabecera de la alerta generada por el sistema."""
    TIPOS = (
        ('ALERTA_VENCIMIENTO', 'Alerta de Vencimiento'),
        ('CIERRE_OPERATIVO', 'Confirmación de Cierre'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=30, choices=TIPOS)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    nota_alquiler = models.ForeignKey(NotaAlquiler, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"[{self.tipo}] {self.titulo}"


class DetalleNotifi(models.Model):
    """Módulo Auxiliar: Detalle de entrega por empleado receptor de la alerta."""
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE, related_name='detalles')
    empleado_destino = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    leido = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alerta para {self.empleado_destino.nombre_completo} - Leído: {self.leido}"