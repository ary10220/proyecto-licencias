"""
Vistas de Division (CU11 - Gestionar Divisiones).
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .base import consumir_estado_modal, exigir_permiso, guardar_estado_modal
from ..forms import DivisionForm
from ...application.use_cases import (
    uc_crear_division,
    uc_editar_division,
    uc_eliminar_division,
    uc_listar_divisiones,
)
from ...infrastructure import repositories as repo


@login_required
@exigir_permiso('empleados.view_gerenciadivision')
def lista_divisiones(request):
    puede_crear = request.user.is_superuser or request.user.has_perm('empleados.add_gerenciadivision')

    if request.method == 'POST':
        if not puede_crear:
            messages.error(request, 'No tienes permiso para esa accion.')
            return redirect('gestion_global:lista_divisiones')
        form = DivisionForm(request.POST)
        if form.is_valid():
            uc_crear_division(request=request, form=form)
            messages.success(request, 'Division creada correctamente.')
            return redirect('gestion_global:lista_divisiones')
        guardar_estado_modal(request, 'divisiones')
        return redirect('gestion_global:lista_divisiones')

    form, modal_abierto = consumir_estado_modal(request, 'divisiones', DivisionForm, puede_crear=puede_crear)

    return render(request, 'gestion_global/divisiones/lista.html', {
        'titulo': 'Divisiones',
        'divisiones': uc_listar_divisiones(),
        'form': form,
        'puede_crear': puede_crear,
        'modal_abierto': modal_abierto,
        'gestion_global_active': 'divisiones',
    })


@login_required


@login_required
@exigir_permiso('empleados.add_gerenciadivision')
def crear_division(request):
    if request.method == 'POST':
        form = DivisionForm(request.POST)
        if form.is_valid():
            uc_crear_division(request=request, form=form)
            messages.success(request, 'Division creada correctamente.')
            return redirect('gestion_global:lista_divisiones')
    else:
        form = DivisionForm()
    return render(request, 'gestion_global/divisiones/form.html', {
        'titulo': 'Nueva division',
        'form': form,
        'gestion_global_active': 'divisiones',
        'volver_url_name': 'gestion_global:lista_divisiones',
    })


@login_required
@exigir_permiso('empleados.change_gerenciadivision')
def editar_division(request, pk):
    division = repo.get_division(pk)
    if request.method == 'POST':
        form = DivisionForm(request.POST, instance=division)
        if form.is_valid():
            uc_editar_division(request=request, form=form, division=division)
            messages.success(request, 'Division actualizada.')
            return redirect('gestion_global:lista_divisiones')
    else:
        form = DivisionForm(instance=division)
    return render(request, 'gestion_global/divisiones/form.html', {
        'titulo': f'Editar division: {division.nombre}',
        'form': form,
        'gestion_global_active': 'divisiones',
        'volver_url_name': 'gestion_global:lista_divisiones',
    })


@login_required
@exigir_permiso('empleados.delete_gerenciadivision')
def eliminar_division(request, pk):
    division = repo.get_division(pk)
    if request.method == 'POST':
        label = uc_eliminar_division(request=request, division=division)
        messages.success(request, f"Division '{label}' eliminada.")
    return redirect('gestion_global:lista_divisiones')
