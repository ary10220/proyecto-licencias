from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from .models import (
    Tenant, Empresa, TipoLicencia, Licencia, Asignacion, Proveedor,
    PropuestaLicencia, NotaAlquiler, Notificacion, DetalleNotificacion
)
from licencias.application.use_cases.cierres_y_alertas import uc_crear_nota_alquiler

# =====================================================================
# REGISTROS ORIGINALES 
# =====================================================================

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


# =====================================================================
# INTEGRACIÓN DEL MÓDULO DE CIERRES Y ALERTAS 
# =====================================================================

@admin.register(PropuestaLicencia)
class PropuestaLicenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'empresa', 'fecha_creacion', 'get_estado_visual')
    list_filter = ('estado', 'tenant')
    search_fields = ('empresa__nombre',)
    actions = ['aprobar_y_generar_nota']

    @admin.display(description='Estado')
    def get_estado_visual(self, obj):
        if obj.estado == 'APROBADA':
            return '🔵 Aprobada / Confirmada'
        elif obj.estado == 'RECHAZADA':
            return '🔴 Rechazada'
        return '🟡 Pendiente'

    @admin.action(description='⚡ Ejecutar Cierre Operativo (Generar Nota de Alquiler)')
    def aprobar_y_generar_nota(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Por favor, selecciona únicamente una propuesta comercial para procesar el cierre.", messages.WARNING)
            return
            
        propuesta = queryset.first()
        
        if propuesta.estado == 'APROBADA':
            self.message_user(request, "Esta propuesta ya cuenta con un cierre operativo y una Nota de Alquiler activa.", messages.ERROR)
            return

        try:
            # Ejecución síncrona de tu Caso de Uso
            nota = uc_crear_nota_alquiler(
                request=request,
                propuesta_id=propuesta.id,
                numero_nota=f"NALQ-2026-{propuesta.id:04d}",
                monto=1850.00,  # Datos calculados/simulados para la demo en el navegador
                dias_para_vencer=30
            )
            self.message_user(
                request, 
                f"¡Cierre Operativo Exitoso! Propuesta comercial convertida a Nota de Alquiler: {nota.numero_nota}. "
                f"El subsistema calculó las fechas límite e inyectó una Alerta de Notificación preventiva en la base de datos.", 
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(request, f"Fallo en la transacción atómica: {str(e)}", messages.ERROR)


@admin.register(NotaAlquiler)
class NotaAlquilerAdmin(admin.ModelAdmin):
    list_display = ('numero_nota', 'propuesta', 'fecha_emision', 'fecha_vencimiento_pago', 'monto_total', 'procesado')
    list_filter = ('procesado', 'fecha_emision')
    search_fields = ('numero_nota',)
    readonly_fields = ('fecha_emision', 'fecha_vencimiento_pago', 'procesado')


class DetalleNotificacionInline(admin.TabularInline):
    model = DetalleNotificacion
    extra = 0
    readonly_fields = ('asunto', 'mensaje', 'referencia_nota')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'get_tipo_visual', 'fecha_alerta', 'get_estado_visual')
    list_filter = ('estado', 'tipo')
    inlines = [DetalleNotificacionInline]

    @admin.display(description='Tipo de Alerta')
    def get_tipo_visual(self, obj):
        if obj.tipo == 'VENCIMIENTO_PAGO':
            return '⚠️ Vencimiento de Pago de Alquiler'
        return '📅 Fecha Límite de Licencia'

    @admin.display(description='Estado Notificación')
    def get_estado_visual(self, obj):
        if obj.estado == 'PENDIENTE':
            return '⏳ Alerta Pendiente'
        elif obj.estado == 'ENVIADA':
            return '📩 Notificación Despachada'
        return '✅ Atendida / Solucionada'