from django.db import models
from django.utils import timezone
from empleados.models import Empleado


class Tenant(models.Model):
    """Representa el grupo corporativo o conglomerado principal."""
    nombre = models.CharField(max_length=80, unique=True)
    
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