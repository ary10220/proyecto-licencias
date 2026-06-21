from bitacora.actions import log_area_usuario_eliminar

from ...infrastructure import repositories as repo


def uc_eliminar_area_usuario(request, area) -> tuple[str, int]:
    nombre, total_cargos = repo.delete_area_usuario(area)
    log_area_usuario_eliminar(request, nombre, total_cargos)
    return nombre, total_cargos

