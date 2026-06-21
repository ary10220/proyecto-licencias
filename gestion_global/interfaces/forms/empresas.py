"""Formulario de Empresa (CU07)."""

from django import forms
from django.db.models import Q

from ...infrastructure.models import Empresa, Tenant


class EmpresaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant_qs = Tenant.objects.filter(activo=True)
        if self.instance.pk and self.instance.tenant_id:
            tenant_qs = Tenant.objects.filter(Q(activo=True) | Q(pk=self.instance.tenant_id))
        self.fields['tenant'].queryset = tenant_qs.order_by('nombre')

    class Meta:
        model = Empresa
        fields = ['tenant', 'nombre']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Razon Social',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        tenant = cleaned_data.get('tenant')
        nombre = (cleaned_data.get('nombre') or '').strip()
        if tenant and not tenant.activo:
            self.add_error('tenant', 'No se puede asociar una empresa a un tenant inactivo.')
        if tenant and nombre:
            qs = Empresa.objects.filter(tenant=tenant, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('nombre', 'Ya existe una empresa con este nombre dentro del tenant seleccionado.')
        return cleaned_data
