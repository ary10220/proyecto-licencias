"""
Vistas de Empresa (CU07 - Gestionar empresa cliente).
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .base import consumir_estado_modal, exigir_permiso, guardar_estado_modal
from ..forms import EmpresaForm
from ...application.use_cases import (
    uc_crear_empresa,
    uc_editar_empresa,
    uc_eliminar_empresa,
    uc_listar_empresas,
)
from ...infrastructure import repositories as repo


@login_required
@exigir_permiso('licencias.view_empresa')
def lista_empresas(request):
    puede_crear = request.user.is_superuser or request.user.has_perm('licencias.add_empresa')

    if request.method == 'POST':
        if not puede_crear:
            messages.error(request, 'No tienes permiso para esa accion.')
            return redirect('gestion_global:lista_empresas')
        form = EmpresaForm(request.POST)
        if form.is_valid():
            uc_crear_empresa(request=request, form=form)
            messages.success(request, 'Empresa creada correctamente.')
            return redirect('gestion_global:lista_empresas')
        guardar_estado_modal(request, 'empresas')
        return redirect('gestion_global:lista_empresas')

    form, modal_abierto = consumir_estado_modal(request, 'empresas', EmpresaForm, puede_crear=puede_crear)

    return render(request, 'gestion_global/empresas/lista.html', {
        'titulo': 'Empresas',
        'empresas': uc_listar_empresas(),
        'form': form,
        'puede_crear': puede_crear,
        'modal_abierto': modal_abierto,
        'gestion_global_active': 'empresas',
    })


@login_required


@login_required
@exigir_permiso('licencias.add_empresa')
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            uc_crear_empresa(request=request, form=form)
            messages.success(request, 'Empresa creada correctamente.')
            return redirect('gestion_global:lista_empresas')
    else:
        form = EmpresaForm()
    return render(request, 'gestion_global/empresas/form.html', {
        'titulo': 'Nueva empresa',
        'form': form,
        'gestion_global_active': 'empresas',
        'volver_url_name': 'gestion_global:lista_empresas',
    })


@login_required
@exigir_permiso('licencias.change_empresa')
def editar_empresa(request, pk):
    empresa = repo.get_empresa(pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            uc_editar_empresa(request=request, form=form, empresa=empresa)
            messages.success(request, 'Empresa actualizada.')
            return redirect('gestion_global:lista_empresas')
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'gestion_global/empresas/form.html', {
        'titulo': f'Editar empresa: {empresa.nombre}',
        'form': form,
        'gestion_global_active': 'empresas',
        'volver_url_name': 'gestion_global:lista_empresas',
    })


@login_required
@exigir_permiso('licencias.delete_empresa')
def eliminar_empresa(request, pk):
    empresa = repo.get_empresa(pk)
    if request.method == 'POST':
        label = uc_eliminar_empresa(request=request, empresa=empresa)
        messages.success(request, f"Empresa '{label}' eliminada.")
    return redirect('gestion_global:lista_empresas')
