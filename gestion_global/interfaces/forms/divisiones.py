"""Formulario de Division (CU11)."""

from django import forms

from ...infrastructure.models import GerenciaDivision


class DivisionForm(forms.ModelForm):
    class Meta:
        model = GerenciaDivision
        fields = ['empresa', 'codigo', 'nombre']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Codigo'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la division'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        codigo = (cleaned_data.get('codigo') or '').strip()
        nombre = (cleaned_data.get('nombre') or '').strip()
        if empresa and codigo:
            qs = GerenciaDivision.objects.filter(empresa=empresa, codigo__iexact=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('codigo', 'Ya existe una division con este codigo en la empresa seleccionada.')
        if empresa and nombre:
            qs = GerenciaDivision.objects.filter(empresa=empresa, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('nombre', 'Ya existe una division con este nombre en la empresa seleccionada.')
        return cleaned_data
