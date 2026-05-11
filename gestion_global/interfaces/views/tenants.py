"""
Vistas de Tenant (CU12 - Gestionar tenant).
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .base import consumir_estado_modal, exigir_permiso, guardar_estado_modal
from ..forms import TenantForm
from ...application.use_cases import (
    uc_crear_tenant,
    uc_editar_tenant,
    uc_eliminar_tenant,
    uc_listar_tenants,
    uc_reactivar_tenant,
)
from ...infrastructure import repositories as repo


@login_required
@exigir_permiso('licencias.view_tenant')
def lista_tenants(request):
    puede_crear = request.user.is_superuser or request.user.has_perm('licencias.add_tenant')
    q = (request.GET.get('q') or '').strip()
    estado = request.GET.get('estado') or 'activos'

    if request.method == 'POST':
        if not puede_crear:
            messages.error(request, 'No tienes permiso para esa accion.')
            return redirect('gestion_global:lista_tenants')
        form = TenantForm(request.POST)
        if form.is_valid():
            uc_crear_tenant(request=request, form=form)
            messages.success(request, 'Tenant creado correctamente.')
            return redirect('gestion_global:lista_tenants')
        guardar_estado_modal(request, 'tenants')
        return redirect('gestion_global:lista_tenants')

    form, modal_abierto = consumir_estado_modal(request, 'tenants', TenantForm, puede_crear=puede_crear)

    return render(request, 'gestion_global/tenants/lista.html', {
        'titulo': 'Tenants',
        'tenants': uc_listar_tenants(q=q, estado=estado),
        'form': form,
        'puede_crear': puede_crear,
        'modal_abierto': modal_abierto,
        'gestion_global_active': 'tenants',
        'q': q,
        'estado': estado,
    })


@login_required


@login_required
@exigir_permiso('licencias.add_tenant')
def crear_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            uc_crear_tenant(request=request, form=form)
            messages.success(request, 'Tenant creado correctamente.')
            return redirect('gestion_global:lista_tenants')
    else:
        form = TenantForm()
    return render(request, 'gestion_global/tenants/form.html', {
        'titulo': 'Nuevo tenant',
        'form': form,
        'gestion_global_active': 'tenants',
        'volver_url_name': 'gestion_global:lista_tenants',
    })


@login_required
@exigir_permiso('licencias.change_tenant')
def editar_tenant(request, pk):
    tenant = repo.get_tenant(pk)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            uc_editar_tenant(request=request, form=form, tenant=tenant)
            messages.success(request, 'Tenant actualizado.')
            return redirect('gestion_global:lista_tenants')
    else:
        form = TenantForm(instance=tenant)
    return render(request, 'gestion_global/tenants/form.html', {
        'titulo': f'Editar tenant: {tenant.nombre}',
        'form': form,
        'gestion_global_active': 'tenants',
        'volver_url_name': 'gestion_global:lista_tenants',
    })


@login_required
@exigir_permiso('licencias.delete_tenant')
def eliminar_tenant(request, pk):
    tenant = repo.get_tenant(pk)
    if request.method == 'POST':
        try:
            label = uc_eliminar_tenant(request=request, tenant=tenant)
            messages.success(request, f"Tenant '{label}' inactivado.")
        except ValidationError as exc:
            messages.error(request, exc.message)
    return redirect('gestion_global:lista_tenants')


@login_required
@exigir_permiso('licencias.change_tenant')
def reactivar_tenant(request, pk):
    tenant = repo.get_tenant(pk)
    if request.method == 'POST':
        label = uc_reactivar_tenant(request=request, tenant=tenant)
        messages.success(request, f"Tenant '{label}' reactivado.")
    return redirect('gestion_global:lista_tenants')
