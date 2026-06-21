"""Formulario de Tenant (CU12)."""

from django import forms

from ...infrastructure.models import Tenant


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Grupo Corporativo',
            }),
        }

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        qs = Tenant.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if nombre and qs.exists():
            raise forms.ValidationError('Ya existe un tenant con este nombre.')
        return nombre
