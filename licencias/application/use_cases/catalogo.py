"""
================================================================================
CU - Gestionar catalogo de licenciamiento
================================================================================
Permite administrar Proveedores y Tipos de Licencia (SKUs).
Estos NO son CU del CICLO 2 pero son catalogos operativos
necesarios para el flujo de licencias.

Actores:        A1 (Administrador)
Pre-condicion:  Sesion activa con permisos.
Post-condicion: La accion queda registrada en bitacora.

Reglas:
  - No se puede eliminar un Proveedor con licencias activas
    (PROTECT en FK).
  - No se puede eliminar un TipoLicencia con licencias activas
    (PROTECT en FK).
================================================================================
"""

from __future__ import annotations

from bitacora.actions import (
    log_proveedor_crear,
    log_proveedor_editar,
    log_proveedor_eliminar,
    log_tipo_licencia_crear,
    log_tipo_licencia_editar,
    log_tipo_licencia_eliminar,
)
from ...models import Proveedor, TipoLicencia
from ...infrastructure import repositories as repo


# ---------- Proveedor ----------

def uc_listar_proveedores():
    return repo.list_proveedores()


def uc_crear_proveedor(*, request, form) -> Proveedor:
    proveedor = form.save()
    log_proveedor_crear(request, proveedor)
    return proveedor


def uc_editar_proveedor(*, request, form, proveedor: Proveedor) -> Proveedor:
    proveedor = form.save()
    log_proveedor_editar(request, proveedor)
    return proveedor


def uc_eliminar_proveedor(*, request, proveedor: Proveedor) -> str:
    label = str(proveedor)
    proveedor.activo = False
    proveedor.save(update_fields=['activo'])
    log_proveedor_eliminar(request, label)
    return label


# ---------- TipoLicencia ----------

def uc_listar_tipos_licencia():
    return repo.list_tipos_licencia()


def uc_crear_tipo_licencia(*, request, form) -> TipoLicencia:
    tipo = form.save()
    log_tipo_licencia_crear(request, tipo)
    return tipo


def uc_editar_tipo_licencia(*, request, form, tipo: TipoLicencia) -> TipoLicencia:
    tipo = form.save()
    log_tipo_licencia_editar(request, tipo)
    return tipo


def uc_eliminar_tipo_licencia(*, request, tipo: TipoLicencia) -> str:
    label = str(tipo)
    tipo.activo = False
    tipo.save(update_fields=['activo'])
    log_tipo_licencia_eliminar(request, label)
    return label
