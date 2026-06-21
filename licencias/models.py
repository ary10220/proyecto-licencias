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
    """
    Entidad proveedora o reseller de licenciamiento.

    Centraliza los datos comerciales del proveedor. Se reutiliza en:
      - TipoLicencia.proveedor_default (catalogo)
      - Licencia.proveedor (stock)
      - Factura.proveedor (comercial)
    """
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre comercial.")
    razon_social = models.CharField(max_length=160, blank=True, help_text="Razon social legal.")
    nit = models.CharField(max_length=40, blank=True, help_text="NIT / RUC / identificacion fiscal.")
    contacto = models.CharField(max_length=100, blank=True, null=True, help_text="Persona de contacto principal.")
    email = models.EmailField(blank=True, help_text="Correo comercial.")
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True)
    sitio_web = models.URLField(blank=True)
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

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
    """
    Catalogo de SKUs y tipos de licencias de software.

    Fuente UNICA de informacion comercial: precio_compra, precio_venta,
    descripcion, proveedor_default. Otros modulos (Facturacion, Cotizaciones)
    consultan esta tabla y NO mantienen copias propias de los precios.
    """
    MONEDAS = (
        ('BOB', 'Bolivianos (BOB)'),
        ('USD', 'Dolares (USD)'),
        ('EUR', 'Euros (EUR)'),
    )

    codigo = models.CharField(
        max_length=30, blank=True, db_index=True,
        help_text="SKU o codigo interno. Ej: M365-BB, ADBE-CC. Opcional.",
    )
    nombre = models.CharField(max_length=80)
    fabricante = models.CharField(max_length=100, default='Microsoft')
    descripcion = models.TextField(blank=True, default='', help_text="Descripcion comercial visible en cotizaciones.")
    precio_compra = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Precio al que se compra al proveedor (referencia interna).",
    )
    precio_venta = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Precio sugerido al cliente. Usado por cotizaciones y facturas.",
    )
    moneda = models.CharField(max_length=3, choices=MONEDAS, default='BOB')
    proveedor_default = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tipos_licencia',
        help_text="Proveedor sugerido al crear cotizacion (no obligatorio).",
    )
    stock_minimo = models.PositiveIntegerField(
        default=0,
        help_text="Stock minimo de licencias antes de alertar (logico, no fisico).",
    )
    duracion_dias = models.PositiveIntegerField(
        default=365,
        help_text="Duracion sugerida de la licencia en dias.",
    )
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['fabricante', 'nombre']

    @property
    def stock_logico(self):
        """Cuenta licencias disponibles (sin asignacion activa)."""
        return self.cantidad_disponible

    @property
    def cantidad_total(self):
        return self.licencia_set.count()

    @property
    def cantidad_asignada(self):
        return self.licencia_set.filter(asignaciones__activo=True).distinct().count()

    @property
    def cantidad_disponible(self):
        hoy = timezone.now().date()
        return (
            self.licencia_set
            .filter(estado_operativo=Licencia.ESTADO_DISPONIBLE, fecha_vencimiento__gte=hoy)
            .exclude(asignaciones__activo=True)
            .distinct()
            .count()
        )

    def __str__(self):
        return self.nombre


class Licencia(models.Model):
    """
    Registro individual de un activo de software en el inventario.
    """
    ESTADO_DISPONIBLE = 'DISPONIBLE'
    ESTADO_ASIGNADA = 'ASIGNADA'
    ESTADO_VENCIDA = 'VENCIDA'
    ESTADO_SUSPENDIDA = 'SUSPENDIDA'
    ESTADO_PENDIENTE_ACTIVACION = 'PENDIENTE_ACTIVACION'
    ESTADO_REVOCADA = 'REVOCADA'

    ESTADOS_OPERATIVOS = (
        (ESTADO_DISPONIBLE, 'Disponible'),
        (ESTADO_ASIGNADA, 'Asignada'),
        (ESTADO_VENCIDA, 'Vencida'),
        (ESTADO_SUSPENDIDA, 'Suspendida'),
        (ESTADO_PENDIENTE_ACTIVACION, 'Pendiente de activacion'),
        (ESTADO_REVOCADA, 'Revocada'),
    )

    ORIGEN_MANUAL = 'MANUAL'
    ORIGEN_FACTURA = 'FACTURA'
    ORIGEN_SYNC = 'SYNC'

    ORIGENES = (
        (ORIGEN_MANUAL, 'Registro manual'),
        (ORIGEN_FACTURA, 'Facturacion'),
        (ORIGEN_SYNC, 'Sincronizacion'),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Empresa Dueña")
    tipo = models.ForeignKey(TipoLicencia, on_delete=models.PROTECT)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Proveedor (Reseller)")

    estado_operativo = models.CharField(
        max_length=24,
        choices=ESTADOS_OPERATIVOS,
        default=ESTADO_DISPONIBLE,
        db_index=True,
    )
    origen = models.CharField(max_length=12, choices=ORIGENES, default=ORIGEN_MANUAL, db_index=True)
    factura_origen = models.ForeignKey(
        'facturacion.Factura',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='licencias_generadas',
    )
    detalle_factura_origen = models.ForeignKey(
        'facturacion.DetalleFactura',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='licencias_generadas',
    )

    fecha_compra = models.DateField()
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_activacion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField()
    observaciones = models.TextField(blank=True)

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
        if self.estado_operativo in {
            self.ESTADO_SUSPENDIDA,
            self.ESTADO_PENDIENTE_ACTIVACION,
            self.ESTADO_REVOCADA,
        }:
            return self.estado_operativo
        if self.esta_vencida:
            return self.ESTADO_VENCIDA
        if self.esta_asignada:
            return self.ESTADO_ASIGNADA
        return self.ESTADO_DISPONIBLE

    @property
    def puede_asignarse(self):
        return self.estado == self.ESTADO_DISPONIBLE

    @property
    def duracion_dias(self):
        inicio = self.fecha_inicio or self.fecha_activacion or self.fecha_compra
        if inicio and self.fecha_vencimiento:
            return (self.fecha_vencimiento - inicio).days
        return None


class Asignacion(models.Model):
    """
    Registro transaccional que vincula una licencia con un empleado.
    Mantiene un historial de auditoria y snapshots de la estructura organizacional.

    Estados del ciclo de vida (campo `estado`):
      - ASIGNADA   : licencia activa con un empleado.
      - LIBERADA   : el empleado dejo de usar la licencia (vuelve al pool).
      - SUSPENDIDA : pausada temporalmente (no cuenta como disponible, no se usa).
      - VENCIDA    : la licencia llego a su fecha de vencimiento sin liberar.

    El campo `activo` se mantiene por compatibilidad con codigo existente:
      activo=True  cuando estado='ASIGNADA' o 'SUSPENDIDA'
      activo=False cuando estado='LIBERADA' o 'VENCIDA'
    """

    ESTADOS = (
        ('ASIGNADA',   'Asignada'),
        ('LIBERADA',   'Liberada'),
        ('SUSPENDIDA', 'Suspendida'),
        ('VENCIDA',    'Vencida'),
    )

    licencia = models.ForeignKey(Licencia, on_delete=models.CASCADE, related_name='asignaciones')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT)

    estado = models.CharField(max_length=12, choices=ESTADOS, default='ASIGNADA')
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
        self.activo = self.estado in {'ASIGNADA', 'SUSPENDIDA'}

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
