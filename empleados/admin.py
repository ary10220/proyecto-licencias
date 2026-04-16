from django.contrib import admin
from .models import Cargo, GerenciaDivision, GerenciaArea, Unidad, Empleado


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')

@admin.register(GerenciaDivision)
class GerenciaDivisionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'empresa')
    list_filter = ('empresa',)
    search_fields = ('nombre', 'codigo')


@admin.register(GerenciaArea)
class GerenciaAreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'division', 'empresa')
    list_filter = ('empresa', 'division')
    search_fields = ('nombre', 'codigo')
    autocomplete_fields = ['division']


@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'area')
    search_fields = ('nombre',)
    autocomplete_fields = ['area']


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'empresa', 'centro_de_costos', 'area', 'unidad', 'activo')
    list_filter = ('empresa', 'activo', 'area')
    search_fields = ('nombre_completo', 'ci', 'email_principal', 'centro_de_costos')
    autocomplete_fields = ['empresa', 'division', 'area', 'unidad']

    fieldsets = (
        ('Identidad', {
            'fields': ('empresa', 'nombre_completo', 'ci', 'email_principal', 'centro_de_costos')
        }),
        ('Jerarquía Organizacional', {
            'fields': ('division', 'area', 'unidad', 'puesto')
        }),
        ('Ubicación y Estado', {
            'fields': ('pais', 'ciudad', 'oficina', 'activo')
        }),
    )
