"""
================================================================================
CU07 - Gestionar empresa cliente
================================================================================
Permite registrar, actualizar, consultar y deshabilitar (inactivar)
empresas clientes dentro del sistema multitenant.

Actores:        A1 (Administrador), A2 (Ejecutivo Comercial)
Pre-condicion:  Sesion activa con permisos sobre el modulo de empresas.
Post-condicion: La accion queda registrada en la bitacora.

Flujo principal:
  1. El actor accede a la vista Gestionar Empresa Cliente.
  2. Selecciona la operacion (registrar/actualizar/consultar/deshabilitar).
  3. La vista delega al control (este use_case).
  4. El control ejecuta la operacion sobre la entidad Empresa.
  5. La entidad responde al control con el resultado.
  6. El control retorna a la vista para presentar al actor.

Excepciones:
  4a. Empresa duplicada (NIT/RUC) -> notificar conflicto.
  4b. Empresa con empleados activos -> requerir confirmacion adicional.
================================================================================
"""

from __future__ import annotations

from django.core.exceptions import ValidationError

from bitacora.actions import (
    log_empresa_crear,
    log_empresa_editar,
    log_empresa_eliminar,
    log_empresa_reactivar,
)
from empleados.models import Empleado
from ...infrastructure import repositories as repo
from ...infrastructure.models import Empresa


def uc_listar_empresas(*, q="", estado="activos"):
    """Retorna el listado de empresas (consulta)."""
    return repo.list_empresas(q=q, estado=estado)


def uc_crear_empresa(*, request, form) -> Empresa:
    """Crea una empresa via form ya validado y la registra en bitacora."""
    empresa = form.save()
    log_empresa_crear(request, empresa)
    return empresa


def uc_editar_empresa(*, request, form, empresa: Empresa) -> Empresa:
    """Actualiza la empresa via form ya validado y registra en bitacora."""
    empresa = form.save()
    log_empresa_editar(request, empresa)
    return empresa


def uc_eliminar_empresa(*, request, empresa: Empresa) -> str:
    """Inactiva la empresa y registra en bitacora."""
    if Empleado.objects.filter(empresa=empresa, activo=True).exists():
        raise ValidationError("No se puede inactivar una empresa con empleados activos.")
    label = str(empresa)
    repo.set_empresa_activa(empresa, False)
    log_empresa_eliminar(request, label)
    return label


def uc_reactivar_empresa(*, request, empresa: Empresa) -> str:
    if not empresa.tenant.activo:
        raise ValidationError("No se puede reactivar una empresa cuyo tenant esta inactivo.")
    repo.set_empresa_activa(empresa, True)
    log_empresa_reactivar(request, empresa)
    return str(empresa)
