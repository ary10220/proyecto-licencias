"""Formulario de Area (CU10)."""

from django import forms
from django.db.models import Q

from ...infrastructure.models import Empresa, GerenciaArea, GerenciaDivision


class AreaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        empresa_qs = Empresa.objects.filter(activo=True)
        division_qs = GerenciaDivision.objects.filter(activo=True)
        if self.instance.pk:
            if self.instance.empresa_id:
                empresa_qs = Empresa.objects.filter(Q(activo=True) | Q(pk=self.instance.empresa_id))
            if self.instance.division_id:
                division_qs = GerenciaDivision.objects.filter(Q(activo=True) | Q(pk=self.instance.division_id))
        self.fields['empresa'].queryset = empresa_qs.order_by('nombre')
        self.fields['division'].queryset = division_qs.select_related('empresa').order_by('empresa__nombre', 'nombre')

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
        division = cleaned_data.get('division')
        codigo = (cleaned_data.get('codigo') or '').strip()
        nombre = (cleaned_data.get('nombre') or '').strip()
        if empresa and not empresa.activo:
            self.add_error('empresa', 'No se puede asociar un area a una empresa inactiva.')
        if division and not division.activo:
            self.add_error('division', 'No se puede asociar un area a una division inactiva.')
        if empresa and division and division.empresa_id != empresa.id:
            self.add_error('division', 'La division seleccionada no pertenece a la empresa del area.')
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
