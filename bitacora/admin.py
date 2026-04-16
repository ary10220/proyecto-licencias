from django.contrib import admin
from .models import Bitacora

@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'modulo', 'fecha')
    search_fields = ('usuario__username', 'accion', 'modulo')
    list_filter = ('modulo', 'accion', 'fecha')