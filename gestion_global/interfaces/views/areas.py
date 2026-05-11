"""
Vistas de Area (CU10 - Gestionar Areas).
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .base import consumir_estado_modal, exigir_permiso, guardar_estado_modal
from ..forms import AreaForm
from ...application.use_cases import (
    uc_crear_area,
    uc_editar_area,
    uc_eliminar_area,
    uc_listar_areas,
)
from ...infrastructure import repositories as repo


@login_required
@exigir_permiso('empleados.view_gerenciaarea')
def lista_areas(request):
    puede_crear = request.user.is_superuser or request.user.has_perm('empleados.add_gerenciaarea')

    if request.method == 'POST':
        if not puede_crear:
            messages.error(request, 'No tienes permiso para esa accion.')
            return redirect('gestion_global:lista_areas')
        form = AreaForm(request.POST)
        if form.is_valid():
            uc_crear_area(request=request, form=form)
            messages.success(request, 'Area creada correctamente.')
            return redirect('gestion_global:lista_areas')
        guardar_estado_modal(request, 'areas')
        return redirect('gestion_global:lista_areas')

    form, modal_abierto = consumir_estado_modal(request, 'areas', AreaForm, puede_crear=puede_crear)

    return render(request, 'gestion_global/areas/lista.html', {
        'titulo': 'Areas',
        'areas': uc_listar_areas(),
        'form': form,
        'puede_crear': puede_crear,
        'modal_abierto': modal_abierto,
        'gestion_global_active': 'areas',
    })


@login_required


@login_required
@exigir_permiso('empleados.add_gerenciaarea')
def crear_area(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            uc_crear_area(request=request, form=form)
            messages.success(request, 'Area creada correctamente.')
            return redirect('gestion_global:lista_areas')
    else:
        form = AreaForm()
    return render(request, 'gestion_global/areas/form.html', {
        'titulo': 'Nueva area',
        'form': form,
        'gestion_global_active': 'areas',
        'volver_url_name': 'gestion_global:lista_areas',
    })


@login_required
@exigir_permiso('empleados.change_gerenciaarea')
def editar_area(request, pk):
    area = repo.get_area(pk)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            uc_editar_area(request=request, form=form, area=area)
            messages.success(request, 'Area actualizada.')
            return redirect('gestion_global:lista_areas')
    else:
        form = AreaForm(instance=area)
    return render(request, 'gestion_global/areas/form.html', {
        'titulo': f'Editar area: {area.nombre}',
        'form': form,
        'gestion_global_active': 'areas',
        'volver_url_name': 'gestion_global:lista_areas',
    })


@login_required
@exigir_permiso('empleados.delete_gerenciaarea')
def eliminar_area(request, pk):
    area = repo.get_area(pk)
    if request.method == 'POST':
        label = uc_eliminar_area(request=request, area=area)
        messages.success(request, f"Area '{label}' eliminada.")
    return redirect('gestion_global:lista_areas')
