from .base import *  # noqa: F401,F403

from ...application.use_cases import uc_eliminar_area_usuario
from ...infrastructure import repositories as repo


# LISTAR AREAS DE USUARIO
@login_required
@permiso_requerido('user.view_areausuario')
def lista_areas(request):
    areas = repo.list_areas_usuario()
    context = {
        'areas': areas,
        'tenants': repo.list_tenants(),
        'titulo': 'Gestion de Areas de Usuario',
    }
    return render(request, 'user/areas/lista.html', context)


@login_required
@permiso_requerido('user.add_areausuario')
def crear_area(request):
    if request.method == 'POST':
        form = AreaUsuarioForm(request.POST)
        if form.is_valid():
            area = form.save()
            cargos_creados = crear_cargos_de_area(area, form.cleaned_data.get('cargos_iniciales'))
            log_area_usuario_crear(request, area, cargos_creados=len(cargos_creados))
            messages.success(request, f"Area {area.nombre} creada correctamente.")
            return redirect('lista_areas')
    else:
        form = AreaUsuarioForm()

    context = {
        'form': form,
        'tenants': repo.list_tenants(),
        'titulo': 'Crear Area',
        'modo': 'crear',
    }
    return render(request, 'user/areas/form.html', context)


@login_required
@permiso_requerido('user.change_areausuario')
def editar_area(request, area_id):
    area = get_object_or_404(AreaUsuario, id=area_id)

    if request.method == 'POST':
        form = AreaUsuarioForm(request.POST, instance=area)
        if form.is_valid():
            area = form.save()
            cargos_creados = crear_cargos_de_area(area, form.cleaned_data.get('cargos_iniciales'))
            log_area_usuario_editar(request, area, cargos_creados=len(cargos_creados))
            messages.success(request, f"Area {area.nombre} actualizada correctamente.")
            return redirect('lista_areas')
    else:
        form = AreaUsuarioForm(instance=area)

    context = {
        'form': form,
        'area': area,
        'cargos_area': area.cargos.order_by('nombre'),
        'tenants': repo.list_tenants(),
        'titulo': f'Editar Area: {area.nombre}',
        'modo': 'editar',
    }
    return render(request, 'user/areas/form.html', context)


@login_required
@permiso_requerido('user.delete_areausuario', fallback='lista_areas')
@require_POST
def eliminar_area(request, area_id):
    area = get_object_or_404(AreaUsuario, id=area_id)
    nombre, _total_cargos = uc_eliminar_area_usuario(request, area)
    messages.success(request, f"Area {nombre} eliminada correctamente. Sus cargos quedaron sin area.")
    return redirect('lista_areas')
