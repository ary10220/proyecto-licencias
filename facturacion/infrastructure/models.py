"""
Modelos del modulo facturacion (Comercial).

Estructura:
  - PropuestaLicencia + DetallePropuesta  (cotizaciones)
  - Factura + DetalleFactura              (facturas emitidas)
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from licencias.models import Empresa, Licencia, Proveedor, Tenant, TipoLicencia


# ============================================================================
# PROPUESTAS COMERCIALES (COTIZACIONES)
# ============================================================================

class PropuestaLicencia(models.Model):
    ESTADOS = (
        ('BORRADOR',  'Borrador'),
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA',  'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('FACTURADA', 'Facturada'),
        ('ANULADA',   'Anulada'),
    )

    # Estados que permiten edicion completa (productos, precios, descuentos, etc.)
    ESTADOS_EDITABLES = {'BORRADOR', 'PENDIENTE'}
    # Estados de solo lectura (consulta/visualizacion)
    ESTADOS_SOLO_LECTURA = {'FACTURADA', 'ANULADA'}

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='propuestas_comerciales')

    # Numero autogenerado: PROP-YYYY-NNNN
    numero = models.CharField(max_length=30, unique=True, blank=True, verbose_name="Numero de propuesta")

    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='BORRADOR')

    # Descuento global y carga impositiva
    descuento_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Descuento global en porcentaje aplicado al total de la cotizacion.",
    )
    descuento_monto = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Descuento global en monto fijo (se aplica DESPUES del descuento porcentual).",
    )
    impuesto_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=13,
        help_text="IVA o impuesto general aplicado al subtotal con descuentos. Default 13%.",
    )

    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Cotizacion"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"Cotizacion {self.numero} - {self.empresa.nombre}"


    @property
    def puede_editarse_completo(self):
        """True si el usuario puede modificar productos, precios, fechas, etc."""
        return self.estado in self.ESTADOS_EDITABLES

    @property
    def es_solo_lectura(self):
        """True si la cotizacion no se puede modificar de ninguna forma."""
        return self.estado in self.ESTADOS_SOLO_LECTURA

    def save(self, *args, **kwargs):
        # Auto-generar numero si esta vacio
        if not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)

    @classmethod
    def _generar_numero(cls):
        """Genera el siguiente numero de propuesta con formato PROP-YYYY-NNNN."""
        anio = timezone.now().year
        prefix = f"PROP-{anio}-"
        ultimo = cls.objects.filter(numero__startswith=prefix).order_by('-numero').first()
        if ultimo:
            try:
                ultimo_num = int(ultimo.numero.split('-')[-1])
            except (ValueError, IndexError):
                ultimo_num = 0
        else:
            ultimo_num = 0
        return f"{prefix}{(ultimo_num + 1):04d}"

    @property
    def subtotal_bruto(self):
        """Suma de subtotales por linea (sin descuento global ni impuesto)."""
        total = Decimal('0')
        for d in self.detalles.all():
            total += Decimal(str(d.subtotal_con_descuento))
        return total

    @property
    def descuento_global_calculado(self):
        """Monto de descuento aplicado al subtotal_bruto."""
        sub = Decimal(str(self.subtotal_bruto))
        d_pct = Decimal(str(self.descuento_porcentaje or 0)) / Decimal('100')
        d_monto = Decimal(str(self.descuento_monto or 0))
        return (sub * d_pct) + d_monto

    @property
    def subtotal_con_descuento(self):
        return Decimal(str(self.subtotal_bruto)) - Decimal(str(self.descuento_global_calculado))

    @property
    def impuesto_calculado(self):
        imp_pct = Decimal(str(self.impuesto_porcentaje or 0)) / Decimal('100')
        return Decimal(str(self.subtotal_con_descuento)) * imp_pct

    @property
    def total(self):
        """Total final: subtotal - descuentos + impuesto."""
        return Decimal(str(self.subtotal_con_descuento)) + Decimal(str(self.impuesto_calculado))


class DetallePropuesta(models.Model):
    propuesta = models.ForeignKey(PropuestaLicencia, on_delete=models.CASCADE, related_name='detalles')
    tipo_licencia = models.ForeignKey(TipoLicencia, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Precio ofertado en la propuesta",
    )

    # Periodo de vigencia / uso de la licencia
    fecha_inicio_uso = models.DateField(
        null=True, blank=True,
        help_text="Inicio del periodo de uso/vigencia de la licencia.",
    )
    fecha_fin_uso = models.DateField(
        null=True, blank=True,
        help_text="Fin del periodo de uso/vigencia de la licencia.",
    )

    # Descuentos por linea
    descuento_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Descuento porcentual aplicado a esta linea.",
    )
    descuento_monto = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Descuento fijo aplicado a esta linea (despues del porcentaje).",
    )

    observaciones = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Detalle de propuesta"
        verbose_name_plural = "Detalles de propuesta"

    @property
    def subtotal_bruto(self):
        return Decimal(str(self.cantidad)) * Decimal(str(self.precio_unitario or 0))

    @property
    def descuento_calculado(self):
        sub = self.subtotal_bruto
        d_pct = Decimal(str(self.descuento_porcentaje or 0)) / Decimal('100')
        d_monto = Decimal(str(self.descuento_monto or 0))
        return (sub * d_pct) + d_monto

    @property
    def subtotal_con_descuento(self):
        return self.subtotal_bruto - self.descuento_calculado

    @property
    def subtotal(self):
        """Compat: retorna subtotal CON descuentos por linea aplicados."""
        return self.subtotal_con_descuento

    @property
    def duracion_dias(self):
        if self.fecha_inicio_uso and self.fecha_fin_uso:
            return (self.fecha_fin_uso - self.fecha_inicio_uso).days
        return None

    def __str__(self):
        return f"{self.tipo_licencia.nombre} x {self.cantidad}"


# ============================================================================
# FACTURAS
# ============================================================================

class Factura(models.Model):
    ESTADOS = (
        ('BORRADOR', 'Borrador'),
        ('EMITIDA', 'Emitida'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada'),
    )

    METODOS_PAGO = (
        ('CONTADO', 'Contado'),
        ('CREDITO', 'Credito'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
        ('TARJETA', 'Tarjeta'),
        ('OTRO', 'Otro'),
    )

    propuesta = models.ForeignKey(
        PropuestaLicencia, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='facturas',
    )
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='facturas_compra')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='facturas_comerciales')

    numero = models.CharField(max_length=30, unique=True, blank=True)
    fecha = models.DateField(default=timezone.now)

    # Datos tributarios del cliente
    razon_social = models.CharField(max_length=160, blank=True)
    nit = models.CharField(max_length=40, blank=True)
    direccion_fiscal = models.CharField(max_length=200, blank=True)

    # Pago
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='CONTADO')

    # Heredados de la propuesta
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento_monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=13)

    estado = models.CharField(max_length=15, choices=ESTADOS, default='EMITIDA')
    stock_generado = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"Factura {self.numero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)

    @classmethod
    def _generar_numero(cls):
        """Genera el siguiente numero de factura con formato FAC-YYYY-NNNN."""
        anio = timezone.now().year
        prefix = f"FAC-{anio}-"
        ultimo = cls.objects.filter(numero__startswith=prefix).order_by('-numero').first()
        if ultimo:
            try:
                n = int(ultimo.numero.split('-')[-1])
            except (ValueError, IndexError):
                n = 0
        else:
            n = 0
        return f"{prefix}{(n + 1):04d}"

    @property
    def subtotal_bruto(self):
        total = Decimal('0')
        for d in self.detalles.all():
            total += Decimal(str(d.subtotal_con_descuento))
        return total

    @property
    def descuento_global_calculado(self):
        sub = self.subtotal_bruto
        d_pct = Decimal(str(self.descuento_porcentaje or 0)) / Decimal('100')
        d_monto = Decimal(str(self.descuento_monto or 0))
        return (sub * d_pct) + d_monto

    @property
    def subtotal_con_descuento(self):
        return self.subtotal_bruto - self.descuento_global_calculado

    @property
    def impuesto_calculado(self):
        imp_pct = Decimal(str(self.impuesto_porcentaje or 0)) / Decimal('100')
        return self.subtotal_con_descuento * imp_pct

    @property
    def total(self):
        return self.subtotal_con_descuento + self.impuesto_calculado


class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    tipo_licencia = models.ForeignKey(TipoLicencia, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Precio por unidad de licencia",
    )
    fecha_vencimiento = models.DateField()

    # Periodo de vigencia (heredado de la propuesta)
    fecha_inicio_uso = models.DateField(null=True, blank=True)
    fecha_fin_uso = models.DateField(null=True, blank=True)

    # Descuento por linea (heredado de la propuesta)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento_monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    observaciones = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Detalle de factura"
        verbose_name_plural = "Detalles de factura"

    @property
    def subtotal_bruto(self):
        return Decimal(str(self.cantidad)) * Decimal(str(self.precio_unitario or 0))

    @property
    def descuento_calculado(self):
        sub = self.subtotal_bruto
        d_pct = Decimal(str(self.descuento_porcentaje or 0)) / Decimal('100')
        d_monto = Decimal(str(self.descuento_monto or 0))
        return (sub * d_pct) + d_monto

    @property
    def subtotal_con_descuento(self):
        return self.subtotal_bruto - self.descuento_calculado

    @property
    def subtotal(self):
        return self.subtotal_con_descuento

    def __str__(self):
        return f"{self.tipo_licencia.nombre} x {self.cantidad} @ {self.precio_unitario}"

    def crear_stock(self):
        """Genera stock de Licencia (1 por unidad)."""
        fecha_inicio = self.fecha_inicio_uso or self.factura.fecha
        licencias = [
            Licencia(
                tenant=self.factura.tenant,
                empresa=self.factura.empresa,
                tipo=self.tipo_licencia,
                proveedor=self.factura.proveedor,
                estado_operativo=Licencia.ESTADO_DISPONIBLE,
                origen=Licencia.ORIGEN_FACTURA,
                factura_origen=self.factura,
                detalle_factura_origen=self,
                fecha_compra=self.factura.fecha,
                fecha_inicio=fecha_inicio,
                fecha_activacion=fecha_inicio,
                fecha_vencimiento=self.fecha_vencimiento,
                observaciones=f"Generada automaticamente desde factura {self.factura.numero}.",
            )
            for _ in range(self.cantidad)
        ]
        return Licencia.objects.bulk_create(licencias)
