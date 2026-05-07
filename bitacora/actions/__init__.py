"""
Bitacora actions: API publica del modulo bitacora hacia el resto del sistema.

Aunque desde la pureza de Clean Architecture estos casos de uso pertenecerian
a `bitacora.application.use_cases`, conservamos `bitacora.actions` como
fachada estable porque otras apps (licencias, empleados, user) ya importan
desde aqui. Cambiar la ruta romperia decenas de imports sin aportar valor:
en este proyecto, `actions/` es el "boundary" reutilizable del modulo.

Cada submodulo agrupa funciones por contexto:
    - licencias: eventos relacionados a licencias y asignaciones.
    - usuarios: eventos de gestion de usuarios, roles, areas, cargos, perfil.
    - empleados: eventos del ciclo de vida de empleados.
    - configuracion: catalogos transversales (tenants, empresas, proveedores...).

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
    log_liberar_licencia,
    log_sincronizar_m365,
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

from .configuracion import (  # noqa: F401
    # Crear
    log_area_crear,
    log_division_crear,
    log_empresa_crear,
    log_proveedor_crear,
    log_tenant_crear,
    log_tipo_licencia_crear,
    log_unidad_crear,
    # Editar
    log_area_editar,
    log_division_editar,
    log_empresa_editar,
    log_proveedor_editar,
    log_tenant_editar,
    log_tipo_licencia_editar,
    log_unidad_editar,
    # Eliminar
    log_area_eliminar,
    log_division_eliminar,
    log_empresa_eliminar,
    log_proveedor_eliminar,
    log_tenant_eliminar,
    log_tipo_licencia_eliminar,
    log_unidad_eliminar,
)
