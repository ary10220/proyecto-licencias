"""
Vistas de Unidad (CU08 - Gestionar Unidades).
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .base import consumir_estado_modal, exigir_permiso, guardar_estado_modal
from ..forms import UnidadForm
from ...application.use_cases import (
    uc_crear_unidad,
    uc_editar_unidad,
    uc_eliminar_unidad,
    uc_listar_unidades,
    uc_reactivar_unidad,
)
from ...infrastructure import repositories as repo


@login_required
@exigir_permiso('empleados.view_unidad')
def lista_unidades(request):
    puede_crear = request.user.is_superuser or request.user.has_perm('empleados.add_unidad')
    q = (request.GET.get('q') or '').strip()
    estado = request.GET.get('estado') or 'activos'

    if request.method == 'POST':
        if not puede_crear:
            messages.error(request, 'No tienes permiso para esa accion.')
            return redirect('gestion_global:lista_unidades')
        form = UnidadForm(request.POST)
        if form.is_valid():
            uc_crear_unidad(request=request, form=form)
            messages.success(request, 'Unidad creada correctamente.')
            return redirect('gestion_global:lista_unidades')
        guardar_estado_modal(request, 'unidades')
        return redirect('gestion_global:lista_unidades')

    form, modal_abierto = consumir_estado_modal(request, 'unidades', UnidadForm, puede_crear=puede_crear)

    return render(request, 'gestion_global/unidades/lista.html', {
        'titulo': 'Unidades',
        'unidades': uc_listar_unidades(q=q, estado=estado),
        'form': form,
        'puede_crear': puede_crear,
        'modal_abierto': modal_abierto,
        'gestion_global_active': 'unidades',
        'q': q,
        'estado': estado,
    })


@login_required


@login_required
@exigir_permiso('empleados.add_unidad')
def crear_unidad(request):
    if request.method == 'POST':
        form = UnidadForm(request.POST)
        if form.is_valid():
            uc_crear_unidad(request=request, form=form)
            messages.success(request, 'Unidad creada correctamente.')
            return redirect('gestion_global:lista_unidades')
    else:
        form = UnidadForm()
    return render(request, 'gestion_global/unidades/form.html', {
        'titulo': 'Nueva unidad',
        'form': form,
        'gestion_global_active': 'unidades',
        'volver_url_name': 'gestion_global:lista_unidades',
    })


@login_required
@exigir_permiso('empleados.change_unidad')
def editar_unidad(request, pk):
    unidad = repo.get_unidad(pk)
    if request.method == 'POST':
        form = UnidadForm(request.POST, instance=unidad)
        if form.is_valid():
            uc_editar_unidad(request=request, form=form, unidad=unidad)
            messages.success(request, 'Unidad actualizada.')
            return redirect('gestion_global:lista_unidades')
    else:
        form = UnidadForm(instance=unidad)
    return render(request, 'gestion_global/unidades/form.html', {
        'titulo': f'Editar unidad: {unidad.nombre}',
        'form': form,
        'gestion_global_active': 'unidades',
        'volver_url_name': 'gestion_global:lista_unidades',
    })


@login_required
@exigir_permiso('empleados.delete_unidad')
def eliminar_unidad(request, pk):
    unidad = repo.get_unidad(pk)
    if request.method == 'POST':
        try:
            label = uc_eliminar_unidad(request=request, unidad=unidad)
            messages.success(request, f"Unidad '{label}' inactivada.")
        except ValidationError as exc:
            messages.error(request, exc.message)
    return redirect('gestion_global:lista_unidades')


@login_required
@exigir_permiso('empleados.change_unidad')
def reactivar_unidad(request, pk):
    unidad = repo.get_unidad(pk)
    if request.method == 'POST':
        try:
            label = uc_reactivar_unidad(request=request, unidad=unidad)
            messages.success(request, f"Unidad '{label}' reactivada.")
        except ValidationError as exc:
            messages.error(request, exc.message)
    return redirect('gestion_global:lista_unidades')
