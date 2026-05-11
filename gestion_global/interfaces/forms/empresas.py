"""Formulario de Empresa (CU07)."""

from django import forms

from ...infrastructure.models import Empresa


class EmpresaForm(forms.ModelForm):
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
        if tenant and nombre:
            qs = Empresa.objects.filter(tenant=tenant, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('nombre', 'Ya existe una empresa con este nombre dentro del tenant seleccionado.')
        return cleaned_data
