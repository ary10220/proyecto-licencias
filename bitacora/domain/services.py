"""
Reglas y constantes de dominio de bitacora.

Este modulo es PURO: no importa Django ni nada externo. Toda la logica
puede probarse con tests unitarios sin levantar la base de datos.
"""

from __future__ import annotations

import unicodedata


ACCIONES = {
    "CREAR": "CREAR",
    "EDITAR": "EDITAR",
    "ELIMINAR": "ELIMINAR",
    "ASIGNAR": "ASIGNAR",
    "LIBERAR": "LIBERAR",
    "BAJA": "BAJA",
    "REACTIVAR": "REACTIVAR",
    "SINCRONIZAR": "SINCRONIZAR",
    "EXPORTAR": "EXPORTAR",
    "LOGIN": "LOGIN",
    "LOGOUT": "LOGOUT",
    "ERROR": "ERROR",
}

MODULOS = {
    "AUTH": "Autenticacion",
    "INICIO_DASHBOARD": "Inicio y Dashboard",
    "LICENCIAS": "Inicio y Dashboard",
    "REPORTES": "Inicio y Dashboard",
    "SYNC": "Inicio y Dashboard",
    "EMPLEADOS": "Empleados",
    "PARAM": "Parametrizacion Global",
    "CONFIG": "Parametrizacion Global",
    "USUARIOS_ACCESOS": "Usuarios y Accesos",
    "USUARIOS": "Usuarios y Accesos",
    "ROLES": "Usuarios y Accesos",
    "AREAS": "Usuarios y Accesos",
    "CARGOS": "Usuarios y Accesos",
    "PERFIL": "Perfil",
    "BITACORA": "Bitacora",
    "ORG": "Organizacion",
}

NIVEL_INFO = "INFO"
NIVEL_ALERTA = "ALERTA"
NIVEL_CRITICO = "CRITICO"

NIVELES = (NIVEL_INFO, NIVEL_ALERTA, NIVEL_CRITICO)

_NIVEL_POR_ACCION = {
    "CREAR": NIVEL_INFO,
    "EDITAR": NIVEL_INFO,
    "ELIMINAR": NIVEL_ALERTA,
    "ASIGNAR": NIVEL_INFO,
    "LIBERAR": NIVEL_INFO,
    "BAJA": NIVEL_ALERTA,
    "REACTIVAR": NIVEL_INFO,
    "SINCRONIZAR": NIVEL_INFO,
    "EXPORTAR": NIVEL_INFO,
    "LOGIN": NIVEL_INFO,
    "LOGOUT": NIVEL_INFO,
    "ERROR": NIVEL_CRITICO,
}

_COLOR_POR_NIVEL = {
    NIVEL_INFO: "info",
    NIVEL_ALERTA: "warning",
    NIVEL_CRITICO: "danger",
}


def _normalize_text(value):
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.strip().lower().split())


_LABELS_NORMALIZADOS = {
    _normalize_text(label): label
    for label in MODULOS.values()
}

for code, label in MODULOS.items():
    _LABELS_NORMALIZADOS[_normalize_text(code)] = label

_LABELS_NORMALIZADOS.update(
    {
        "autenticacion": MODULOS["AUTH"],
        "auth": MODULOS["AUTH"],
        "inicio": MODULOS["INICIO_DASHBOARD"],
        "dashboard": MODULOS["INICIO_DASHBOARD"],
        "inicio y dashboard": MODULOS["INICIO_DASHBOARD"],
        "licencia": MODULOS["LICENCIAS"],
        "licencias": MODULOS["LICENCIAS"],
        "sincronizacion m365": MODULOS["SYNC"],
        "reportes": MODULOS["REPORTES"],
        "empleado": MODULOS["EMPLEADOS"],
        "empleados": MODULOS["EMPLEADOS"],
        "configuracion": MODULOS["CONFIG"],
        "parametrizacion global": MODULOS["PARAM"],
        "organizacion": MODULOS["PARAM"],
        "usuario": MODULOS["USUARIOS"],
        "usuarios": MODULOS["USUARIOS"],
        "rol": MODULOS["ROLES"],
        "roles": MODULOS["ROLES"],
        "areas": MODULOS["AREAS"],
        "cargos": MODULOS["CARGOS"],
        "usuarios y accesos": MODULOS["USUARIOS_ACCESOS"],
        "perfil": MODULOS["PERFIL"],
        "bitacora": MODULOS["BITACORA"],
    }
)


def clasificar_nivel(accion):
    if not accion:
        return NIVEL_INFO
    return _NIVEL_POR_ACCION.get(accion.upper(), NIVEL_INFO)


def es_evento_critico(accion):
    return clasificar_nivel(accion) == NIVEL_CRITICO


def color_para_nivel(nivel):
    return _COLOR_POR_NIVEL.get(nivel, "secondary")


def color_para_accion(accion):
    return color_para_nivel(clasificar_nivel(accion))


def label_modulo(codigo):
    if not codigo:
        return ""
    normalized = _normalize_text(codigo)
    return _LABELS_NORMALIZADOS.get(normalized, str(codigo).strip())


def inferir_modulo(descripcion, accion=None):
    text = _normalize_text(descripcion)
    if not text:
        if accion in (ACCIONES["LOGIN"], ACCIONES["LOGOUT"]):
            return MODULOS["AUTH"]
        return ""

    if any(token in text for token in ("inicio sesion", "inicio de sesion", "cerro sesion", "cambio su contrasena", "restablecimiento", "desbloqueo", "codigo de acceso")):
        return MODULOS["AUTH"]
    if "foto de perfil" in text:
        return MODULOS["PERFIL"]
    if any(token in text for token in ("sincroniz", "m365", "excel", "export", "reporte")):
        return MODULOS["INICIO_DASHBOARD"]
    if "licencia" in text or "asignacion" in text or "asigno" in text or "libero" in text:
        return MODULOS["INICIO_DASHBOARD"]
    if "empleado" in text:
        return MODULOS["EMPLEADOS"]
    if any(token in text for token in ("rol ", "roles ", "permiso", "usuario ", "roles actuales", "area de usuario", "cargo ", "cargos ")):
        return MODULOS["USUARIOS_ACCESOS"]
    if any(token in text for token in ("tenant", "empresa", "proveedor", "tipo de licencia", "division", "area ", "unidad", "gerencia")):
        return MODULOS["PARAM"]
    return ""


def resolver_modulo(modulo, descripcion="", accion=None):
    modulo_actual = label_modulo(modulo)
    modulo_inferido = inferir_modulo(descripcion, accion=accion)

    if not modulo_actual:
        return modulo_inferido

    if modulo_actual in {"Configuracion", "Organizacion", MODULOS["CONFIG"], MODULOS["ORG"]} and modulo_inferido in {MODULOS["PARAM"], MODULOS["USUARIOS_ACCESOS"]}:
        return modulo_inferido

    if modulo_actual in {"Licencias", "Reportes", "Sincronizacion M365"}:
        return MODULOS["INICIO_DASHBOARD"]

    return modulo_actual or modulo_inferido


def limpiar_descripcion(descripcion):
    if not descripcion:
        return ""
    return " ".join(str(descripcion).split())
