"""Excepciones de dominio del módulo de licencias.

Permiten que la capa de presentación traduzca cada caso de error a un
mensaje de usuario sin que el service conozca request/response.
"""


class LicenciaServiceError(Exception):
    """Base de excepciones del módulo de licencias."""


class LicenciaNoEncontradaError(LicenciaServiceError):
    """No existe licencia con el id provisto."""


class EmpleadoNoEncontradoError(LicenciaServiceError):
    """No existe empleado con el id provisto."""


class AsignacionNoEncontradaError(LicenciaServiceError):
    """No existe asignación con el id provisto."""


class LicenciaYaAsignadaError(LicenciaServiceError):
    """La licencia ya tiene una asignación activa (race condition)."""

    def __init__(self, empleado_actual_nombre: str):
        self.empleado_actual_nombre = empleado_actual_nombre
        super().__init__(f"Licencia ya asignada a {empleado_actual_nombre}")


class EmpleadoYaTieneTipoError(LicenciaServiceError):
    """El empleado ya tiene una licencia activa del mismo TipoLicencia."""

    def __init__(self, empleado_nombre: str, tipo_nombre: str):
        self.empleado_nombre = empleado_nombre
        self.tipo_nombre = tipo_nombre
        super().__init__(f"{empleado_nombre} ya tiene '{tipo_nombre}' activa")


class AsignacionInactivaError(LicenciaServiceError):
    """Se intentó liberar una asignación que ya no está activa."""


class EmpleadoYaInactivoError(LicenciaServiceError):
    """Se intentó dar de baja a un empleado que ya estaba inactivo."""

    def __init__(self, empleado_nombre: str):
        self.empleado_nombre = empleado_nombre
        super().__init__(f"{empleado_nombre} ya estaba inactivo")
