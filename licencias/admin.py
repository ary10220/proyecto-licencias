from django.contrib import admin
from django.utils import timezone
from .models import Tenant, Empresa, TipoLicencia, Licencia, Asignacion, Proveedor

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('nombre',)


@admin.register(TipoLicencia)
class TipoLicenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fabricante')
    list_filter = ('fabricante',)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono')
    search_fields = ('nombre',)


class EstadoLicenciaFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para evaluar el estado en tiempo real de una licencia
    basado en su fecha de vencimiento y asignaciones activas.
    """
    title = 'Estado Operativo'
    parameter_name = 'estado_real'

    def lookups(self, request, model_admin):
        return (
            ('disponible', '🟢 Disponible'),
            ('asignada', '🔴 Asignada'),
            ('vencida', '⚫ Vencida'),
        )

    def queryset(self, request, queryset):
        hoy = timezone.now().date()

        if self.value() == 'vencida':
            return queryset.filter(fecha_vencimiento__lt=hoy)

        if self.value() == 'asignada':
            return queryset.filter(
                fecha_vencimiento__gte=hoy,
                asignaciones__activo=True
            ).distinct()

        if self.value() == 'disponible':
            return queryset.filter(
                fecha_vencimiento__gte=hoy
            ).exclude(asignaciones__activo=True)

        return queryset


class AsignacionInline(admin.TabularInline):
    """
    Gestión en línea del historial de asignaciones dentro de la vista de Licencia.
    Ordenado cronológicamente inverso para priorizar la asignación actual.
    """
    model = Asignacion
    extra = 0
    can_delete = True 
    autocomplete_fields = ['empleado'] 
    ordering = ('-fecha_asignacion',) 
    readonly_fields = ('fecha_asignacion', 'fecha_retiro', 'area_snapshot', 'division_snapshot')
    fields = ('empleado', 'activo', 'fecha_asignacion', 'fecha_retiro', 'observaciones', 'area_snapshot')


@admin.register(Licencia)
class LicenciaAdmin(admin.ModelAdmin):
    list_display = (
        'tipo', 
        'tenant', 
        'empresa',
        'proveedor',
        'get_estado_visual', 
        'get_fecha_asignacion',
        'fecha_vencimiento',
        'get_usuario_actual'
    )
    
    list_filter = (
        'tenant',
        'empresa',
        'proveedor',
        'tipo',
        EstadoLicenciaFilter,
    )
    
    search_fields = (
        'tipo__nombre', 
        'asignaciones__empleado__nombre_completo', 
        'asignaciones__empleado__email_principal'
    )
    
    autocomplete_fields = ['empresa', 'proveedor']
    inlines = [AsignacionInline]

    @admin.display(description='Usuario Asignado')
    def get_usuario_actual(self, obj):
        asignacion = obj.asignaciones.filter(activo=True).first()
        if asignacion:
            area = asignacion.area_snapshot or 'S/D'
            return f"👤 {asignacion.empleado.nombre_completo} [{area}]"
        return "-"

    @admin.display(description='Fecha Asignación')
    def get_fecha_asignacion(self, obj):
        asignacion = obj.asignaciones.filter(activo=True).first()
        if asignacion:
            return asignacion.fecha_asignacion.strftime('%d/%m/%Y')
        return "-"

    @admin.display(description='Estado')
    def get_estado_visual(self, obj):
        estado = obj.estado
        if estado == 'VENCIDA':
            return '⚫ Vencida'
        elif estado == 'ASIGNADA':
            return '🔴 Asignada'
        else:
            return '🟢 Disponible'