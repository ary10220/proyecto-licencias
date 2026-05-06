from .base import *  # noqa: F401,F403

from ...application.use_cases import uc_eliminar_cargo
from ...infrastructure import repositories as repo


# LISTAR CARGOS
@login_required
@permiso_requerido('empleados.view_cargo')
def lista_cargos(request):
    cargos = repo.list_cargos()
    context = {
        'cargos': cargos,
        'tenants': repo.list_tenants(),
        'titulo': 'Gestión de Cargos',
    }
    return render(request, 'user/cargos/lista.html', context)


# CREAR CARGO
@login_required
@permiso_requerido('empleados.add_cargo')
def crear_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            cargo = form.save()
            log_cargo_crear(request, cargo)
            messages.success(
                request,
                f"Cargo {cargo.nombre} creado correctamente. Puedes revisar o completar sus datos.",
            )
            return redirect('lista_cargos')
    else:
        form = CargoForm()

    context = {
        'form': form,
        'tenants': repo.list_tenants(),
        'titulo': 'Crear Cargo',
        'modo': 'crear',
    }
    return render(request, 'user/cargos/form.html', context)


# EDITAR CARGO
@login_required
@permiso_requerido('empleados.change_cargo')
def editar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)

    if request.method == 'POST':
        form = CargoForm(request.POST, instance=cargo)
        if form.is_valid():
            cargo = form.save()
            log_cargo_editar(request, cargo)
            messages.success(request, f"Cargo {cargo.nombre} actualizado correctamente.")
            return redirect('lista_cargos')
    else:
        form = CargoForm(instance=cargo)

    context = {
        'form': form,
        'cargo': cargo,
        'tenants': repo.list_tenants(),
        'titulo': f'Editar Cargo: {cargo.nombre}',
        'modo': 'editar',
    }
    return render(request, 'user/cargos/form.html', context)


# ELIMINAR CARGO
@login_required
@permiso_requerido('empleados.delete_cargo', fallback='lista_cargos')
@require_POST
def eliminar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    nombre = uc_eliminar_cargo(request, cargo)
    messages.success(request, f"Cargo {nombre} eliminado correctamente.")
    return redirect('lista_cargos')
