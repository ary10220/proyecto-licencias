"""
================================================================================
CU12 - Gestionar tenant
================================================================================
Permite administrar la configuracion del tenant corporativo (consultar,
actualizar y deshabilitar/eliminar) dentro del modulo de Gestion Global.

Actores:        A1 (Administrador)
Pre-condicion:  Sesion activa con permisos sobre el modulo de tenants.
Post-condicion: El tenant queda actualizado o eliminado y la accion
                queda registrada en la bitacora.

Regla del Dashboard:
  En el Dashboard principal debe haber un filtro de tenant, pero el
  nombre del tenant NO debe estar visible (mostrar solo codigo/alias).
================================================================================
"""

from __future__ import annotations

from bitacora.actions import log_tenant_crear, log_tenant_editar, log_tenant_eliminar
from ...infrastructure import repositories as repo
from ...infrastructure.models import Tenant


def uc_listar_tenants():
    return repo.list_tenants()


def uc_crear_tenant(*, request, form) -> Tenant:
    tenant = form.save()
    log_tenant_crear(request, tenant)
    return tenant


def uc_editar_tenant(*, request, form, tenant: Tenant) -> Tenant:
    tenant = form.save()
    log_tenant_editar(request, tenant)
    return tenant


def uc_eliminar_tenant(*, request, tenant: Tenant) -> str:
    label = str(tenant)
    repo.delete_tenant(tenant)
    log_tenant_eliminar(request, label)
    return label
