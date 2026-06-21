"""
Bitacora actions: API publica del modulo bitacora hacia el resto del sistema.

Re-exporta funciones comunes para usar imports cortos:
`from bitacora.actions import ...`
"""

from .licencias import (  # noqa: F401
    log_asignacion_licencia,
    log_creacion_licencias,
    log_editar_licencia,
    log_eliminar_licencia,
    log_eliminar_licencias_masivo,
    log_exportar_excel,
    log_exportar_pdf,
    log_liberar_licencia,
)

from .usuarios import (  # noqa: F401
    log_area_usuario_crear,
    log_area_usuario_editar,
    log_area_usuario_eliminar,
    log_cargo_crear,
    log_cargo_editar,
    log_cargo_eliminar,
    log_password_change_inicial,
    log_perfil_actualizar_foto,
    log_perfil_eliminar_foto,
    log_rol_crear,
    log_rol_editar,
    log_rol_eliminar,
    log_usuario_crear,
    log_usuario_editar,
    log_usuario_toggle,
    log_usuario_reset_password,
)

from .empleados import (  # noqa: F401
    log_crear_empleado,
    log_editar_empleado,
    log_baja_empleado,
    log_reactivar_empleado,
)

from .facturacion import (  # noqa: F401
    log_propuesta_crear,
    log_propuesta_editar,
    log_propuesta_aprobar,
    log_propuesta_rechazar,
    log_propuesta_eliminar,
    log_factura_crear,
    log_factura_editar,
    log_factura_anular,
    log_factura_eliminar,
    log_factura_generar_stock,
)

from .configuracion import (  # noqa: F401
    log_area_crear,
    log_division_crear,
    log_empresa_crear,
    log_proveedor_crear,
    log_tenant_crear,
    log_tipo_licencia_crear,
    log_unidad_crear,
    log_area_editar,
    log_division_editar,
    log_empresa_editar,
    log_proveedor_editar,
    log_tenant_editar,
    log_tipo_licencia_editar,
    log_unidad_editar,
    log_area_eliminar,
    log_area_reactivar,
    log_division_eliminar,
    log_division_reactivar,
    log_empresa_eliminar,
    log_empresa_reactivar,
    log_proveedor_eliminar,
    log_tenant_eliminar,
    log_tenant_reactivar,
    log_tipo_licencia_eliminar,
    log_unidad_eliminar,
    log_unidad_reactivar,
)
