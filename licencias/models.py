from django.db import models
from django.utils import timezone
from empleados.models import Empleado


class Tenant(models.Model):
    """Representa el grupo corporativo o conglomerado principal."""
    nombre = models.CharField(max_length=80, unique=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    """Entidad proveedora o reseller de licenciamiento."""
    nombre = models.CharField(max_length=100, unique=True)
    contacto = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre del contacto comercial o email")
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class Empresa(models.Model):
    """Razón social específica vinculada a un Tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='empresas')
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.tenant.nombre})"


class TipoLicencia(models.Model):
    """Catálogo de SKUs y tipos de licencias de software."""
    nombre = models.CharField(max_length=50)
    fabricante = models.CharField(max_length=100, default='Microsoft')
    
    def __str__(self):
        return self.nombre


class Licencia(models.Model):
    """
    Registro individual de un activo de software en el inventario.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Empresa Dueña")
    tipo = models.ForeignKey(TipoLicencia, on_delete=models.PROTECT)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Proveedor (Reseller)")

    fecha_compra = models.DateField()
    fecha_activacion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField()

    def __str__(self):
        empresa_nombre = self.empresa.nombre if self.empresa else self.tenant.nombre
        return f"{self.tipo.nombre} - {empresa_nombre}"

    @property
    def usuario_activo(self):
        """Retorna la asignación activa actual, si existe."""
        return self.asignaciones.filter(activo=True).first()

    # ==========================================
    # LÓGICA DE ESTADO OPERATIVO
    # ==========================================

    @property
    def esta_vencida(self):
        return self.fecha_vencimiento < timezone.now().date()

    @property
    def esta_asignada(self):
        return self.asignaciones.filter(activo=True).exists()

    @property
    def estado(self):
        """
        Determina el estado confiable de la licencia basado en reglas de negocio.
        Jerarquía de evaluación: Vencida -> Asignada -> Disponible.
        """
        if self.esta_vencida:
            return 'VENCIDA'
        if self.esta_asignada:
            return 'ASIGNADA'
        return 'DISPONIBLE'


class Asignacion(models.Model):
    """
    Registro transaccional que vincula una licencia con un empleado.
    Mantiene un historial de auditoría y snapshots de la estructura organizacional.
    """
    licencia = models.ForeignKey(Licencia, on_delete=models.CASCADE, related_name='asignaciones')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT)

    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_retiro = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    observaciones = models.TextField(blank=True)

    # Snapshots organizacionales (Datos inmutables al momento de la asignación)
    area_snapshot = models.CharField(max_length=100, blank=True, null=True)     
    division_snapshot = models.CharField(max_length=100, blank=True, null=True) 
    unidad_snapshot = models.CharField(max_length=100, blank=True, null=True)   

    class Meta:
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"{self.licencia} -> {self.empleado}"

    def save(self, *args, **kwargs):
        # 1. Generación de Snapshots en la creación inicial
        if not self.pk:
            if self.empleado.area:
                self.area_snapshot = self.empleado.area.codigo 
            
            if self.empleado.division:
                self.division_snapshot = self.empleado.division.codigo

            if hasattr(self.empleado, 'unidad') and self.empleado.unidad:
                self.unidad_snapshot = self.empleado.unidad.nombre

        # 2. Registro automatizado de fecha de retiro
        if not self.activo and not self.fecha_retiro:
            self.fecha_retiro = timezone.now()

        super().save(*args, **kwargs)

        # 3. Política de retención de historial (Máximo 5 registros inactivos por optimización)
        historial = Asignacion.objects.filter(
            licencia=self.licencia,
            activo=False
        ).order_by('-fecha_retiro')

        if historial.count() > 5:
            excedentes = historial[5:]
            ultimo_viviente = historial[4]
            
            # Consolidación de datos antiguos en observaciones para evitar pérdida de trazabilidad
            resumen_borrados = "Auditoría de historial archivado:\n"
            for viejo in excedentes:
                fecha_str = viejo.fecha_retiro.strftime('%d/%m/%y') if viejo.fecha_retiro else "N/D"
                area_code = viejo.area_snapshot or "S/A"
                resumen_borrados += f"- {viejo.empleado.nombre_completo} ({area_code}) ({fecha_str})\n"

            if "Auditoría de historial archivado" not in (ultimo_viviente.observaciones or ""):
                ultimo_viviente.observaciones = (ultimo_viviente.observaciones or "") + "\n\n" + resumen_borrados
                ultimo_viviente.save(update_fields=['observaciones'])

            # Depuración física de registros excedentes
            for viejo in excedentes:
                viejo.delete()

class Factura(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='facturas'
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE
    )

    numero = models.CharField(max_length=30, unique=True)

    fecha = models.DateField(default=timezone.now)

    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Factura {self.numero}"

    @property
    def total(self):
        return sum(d.subtotal for d in self.detalles.all())


class DetalleFactura(models.Model):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    tipo_licencia = models.ForeignKey(
        TipoLicencia,
        on_delete=models.PROTECT
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT
    )

    cantidad = models.PositiveIntegerField(default=1)

    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Precio por unidad de licencia (en USD o moneda local)"
    )

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return f"{self.tipo_licencia.nombre} x {self.cantidad} @ {self.precio_unitario}"

    fecha_vencimiento = models.DateField()

    def __str__(self):
        return f"{self.tipo_licencia.nombre} x {self.cantidad}"
    
class PropuestaLicencia(models.Model):
    """Representa la propuesta comercial preliminar antes de ser confirmada."""
    ESTADOS_PROPUESTA = [
        ('PENDIENTE', 'Pendiente de Aprobación'),
        ('APROBADA', 'Aprobada / Confirmada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    fecha_creacion = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS_PROPUESTA, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Propuesta #{self.id} - {self.empresa.nombre} ({self.estado})"


class NotaAlquiler(models.Model):
    """
    Cierre Operativo: Formaliza el contrato de alquiler basado en una propuesta aprobada.
    Relación 0..1 a 1 con PropuestaLicencia.
    """
    propuesta = models.OneToOneField(
        PropuestaLicencia, 
        on_delete=models.PROTECT, 
        related_name='nota_alquiler',
        help_text="Propuesta comercial que origina este cierre operativo"
    )
    numero_nota = models.CharField(max_length=50, unique=True, verbose_name="Número de Nota de Alquiler")
    fecha_emision = models.DateField(default=timezone.now)
    fecha_vencimiento_pago = models.DateField(help_text="Fecha límite para el pago del alquiler")
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    procesado = models.BooleanField(default=False)

    def __str__(self):
        return f"Nota de Alquiler {self.numero_nota} (Propuesta #{self.propuesta.id})"


class Notificacion(models.Model):
    """Módulo auxiliar de Alertas del Sistema."""
    TIPOS_ALERTA = [
        ('VENCIMIENTO_PAGO', 'Vencimiento de Pago de Alquiler'),
        ('LIMITE_CONTRATO', 'Fecha Límite de Licencia'),
    ]
    ESTADOS_NOTIFICACION = [
        ('PENDIENTE', 'Alerta Pendiente'),
        ('ENVIADA', 'Notificación Despachada'),
        ('PROCESADA', 'Atendida / Solucionada'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=30, choices=TIPOS_ALERTA)
    fecha_alerta = models.DateField(help_text="Fecha en la que debe saltar o mostrarse la alerta")
    estado = models.CharField(max_length=20, choices=ESTADOS_NOTIFICACION, default='PENDIENTE')
    
    def __str__(self):
        return f"Alerta {self.tipo} - {self.fecha_alerta} ({self.estado})"


class DetalleNotificacion(models.Model):
    """Desglose y contenido específico de cada alerta generada."""
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE, related_name='detalles')
    asunto = models.CharField(max_length=150)
    mensaje = models.TextField()
    referencia_nota = models.ForeignKey(NotaAlquiler, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Detalle Alerta: {self.asunto}"