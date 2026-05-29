from django.contrib import admin

from .models import DetalleFactura, DetallePropuesta, Factura, PropuestaLicencia


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

