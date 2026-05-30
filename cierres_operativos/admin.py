from django.contrib import admin
from .models import PropuestaComercial, NotaAlquiler, Notificacion, DetalleNotifi

@admin.register(PropuestaComercial)
class PropuestaComercialAdmin(admin.ModelAdmin):
    list_display = ('codigo_propuesta', 'empresa', 'monto_total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tenant')

@admin.register(NotaAlquiler)
class NotaAlquilerAdmin(admin.ModelAdmin):
    list_display = ('nro_nota', 'propuesta', 'monto_pactado', 'estado_pago', 'fecha_emision')

admin.site.register(Notificacion)
admin.site.register(DetalleNotifi)