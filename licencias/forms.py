"""
Formularios del modulo licencias/.

Despues de la migracion a `gestion_global`, este archivo solo contiene:
  - EmpleadoForm        (sera migrado a `empleados/` cuando se haga CU09)
  - ProveedorForm       (catalogo de licenciamiento, no migra)
  - TipoLicenciaForm    (catalogo de licenciamiento, no migra)
  - LicenciaForm        (operativo de licencias)

Los formularios de Tenant, Empresa, Division, Area, Unidad viven ahora
en `gestion_global/interfaces/forms/`.
"""

from django import forms
from django.forms import inlineformset_factory
from empleados.models import Empleado
from .models import Proveedor, TipoLicencia, Licencia, PropuestaLicencia, DetallePropuesta


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'nombre_completo', 'ci', 'email_principal',
            'empresa', 'division', 'area', 'unidad',
            'puesto', 'centro_de_costos', 'pais', 'ciudad', 'oficina'
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Perez'}),
            'ci': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Carnet de Identidad'}),
            'email_principal': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'juan.perez@dominio.com'}),
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'division': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'area': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'unidad': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Analista de Sistemas'}),
            'centro_de_costos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'oficina': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Planta Administrativa'}),
        }
        error_messages = {
            'ci': {'unique': 'Ya existe un empleado registrado con esta Cedula de Identidad.'},
            'email_principal': {'unique': 'Este correo electronico ya esta en uso por otro empleado.'},
        }


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Proveedor Inc.'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ejecutivo de Cuenta (email)'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +591 70000000'}),
        }

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        qs = Proveedor.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if nombre and qs.exists():
            raise forms.ValidationError('Ya existe un proveedor con este nombre.')
        return nombre


class TipoLicenciaForm(forms.ModelForm):
    class Meta:
        model = TipoLicencia
        fields = ['nombre', 'fabricante']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Microsoft 365 E3'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Microsoft'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        nombre = (cleaned_data.get('nombre') or '').strip()
        fabricante = (cleaned_data.get('fabricante') or '').strip()
        if nombre and fabricante:
            qs = TipoLicencia.objects.filter(nombre__iexact=nombre, fabricante__iexact=fabricante)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('nombre', 'Ya existe un tipo de licencia con ese nombre y fabricante.')
        return cleaned_data


class LicenciaForm(forms.ModelForm):
    class Meta:
        model = Licencia
        fields = ['tenant', 'empresa', 'tipo', 'proveedor', 'fecha_compra', 'fecha_activacion', 'fecha_vencimiento']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'tipo': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'proveedor': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_activacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class PropuestaForm(forms.ModelForm):
    class Meta:
        model = PropuestaLicencia
        # No incluimos el total aquí porque se calcula solo
        fields = [
            'empresa',
            'tenant',
            'numero',
            'fecha',
            #'estado',
            'observaciones'
        ]
        
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }

# Formulario exclusivo para EDITAR (Aquí sí permitimos cambiar el estado)
class PropuestaEditForm(forms.ModelForm):
    class Meta:
        model = PropuestaLicencia
        fields = ['empresa', 'tenant', 'numero', 'fecha', 'estado', 'observaciones']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DetallePropuestaForm(forms.ModelForm):
    class Meta:
        model = DetallePropuesta
        # Ojo: No incluimos el campo 'propuesta' aquí.
        # Ese campo lo llenaremos "por debajo de la mesa" en la vista (views.py)
        fields = [
            'tipo_licencia',
            'cantidad',
            'precio_unitario'
        ]
        
        widgets = {
            'tipo_licencia': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={ 
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
        }

# ==========================================
# FORMSET: Fábrica de múltiples detalles
# ==========================================
DetallePropuestaFormSet = inlineformset_factory(
    PropuestaLicencia,      # El modelo Padre (Maestro)
    DetallePropuesta,       # El modelo Hijo (Detalle)
    form=DetallePropuestaForm, # El molde que usará para cada fila
    extra=1,                # Cuántas filas vacías mostrar por defecto al entrar
    can_delete=True         # Permite que el usuario elimine una fila si se equivoca
)