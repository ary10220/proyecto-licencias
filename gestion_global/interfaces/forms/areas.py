"""Formulario de Area (CU10)."""

from django import forms

from ...infrastructure.models import GerenciaArea


class AreaForm(forms.ModelForm):
    class Meta:
        model = GerenciaArea
        fields = ['empresa', 'division', 'codigo', 'nombre']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'division': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Codigo del area'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del area'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        codigo = (cleaned_data.get('codigo') or '').strip()
        nombre = (cleaned_data.get('nombre') or '').strip()
        if empresa and codigo:
            qs = GerenciaArea.objects.filter(empresa=empresa, codigo__iexact=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('codigo', 'Ya existe un area con este codigo en la empresa seleccionada.')
        if empresa and nombre:
            qs = GerenciaArea.objects.filter(empresa=empresa, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('nombre', 'Ya existe un area con este nombre en la empresa seleccionada.')
        return cleaned_data
