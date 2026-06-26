from django.contrib import admin

from .models import DetalleFactura, DetallePropuesta, Factura, PagoFactura, PropuestaLicencia


class DetallePropuestaInline(admin.TabularInline):
    model = DetallePropuesta
    extra = 0


@admin.register(PropuestaLicencia)
class PropuestaLicenciaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'empresa', 'tenant', 'fecha', 'estado', 'total')
    list_filter = ('estado', 'tenant')
    search_fields = ('numero', 'empresa__nombre')
    inlines = [DetallePropuestaInline]


class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 0


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'empresa', 'proveedor', 'fecha', 'estado', 'stock_generado', 'total')
    list_filter = ('estado', 'tenant', 'stock_generado')
    search_fields = ('numero', 'empresa__nombre', 'razon_social', 'nit')
    inlines = [DetalleFacturaInline]


@admin.register(PagoFactura)
class PagoFacturaAdmin(admin.ModelAdmin):
    list_display = ('factura', 'fecha_pago', 'monto', 'metodo_pago', 'estado', 'creado_por')
    list_filter = ('estado', 'metodo_pago', 'fecha_pago')
    search_fields = ('factura__numero', 'factura__empresa__nombre', 'referencia')
    autocomplete_fields = ('factura', 'creado_por')

