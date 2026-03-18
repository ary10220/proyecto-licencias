from django import forms
from empleados.models import Empleado, GerenciaDivision, GerenciaArea, Unidad
from .models import Tenant, Empresa, Proveedor, TipoLicencia, Licencia

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
            'ci': {
                'unique': 'Ya existe un empleado registrado con esta Cédula de Identidad.',
            },
            'email_principal': {
                'unique': 'Este correo electrónico ya está en uso por otro empleado.',
            }
        }


class GerenciaDivisionForm(forms.ModelForm):
    class Meta:
        model = GerenciaDivision
        fields = ['empresa', 'codigo', 'nombre']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: GDO'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Gerencia de Operaciones'}),
        }


class GerenciaAreaForm(forms.ModelForm):
    class Meta:
        model = GerenciaArea
        fields = ['empresa', 'division', 'codigo', 'nombre']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'division': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: GOM (Opcional)'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Mantenimiento'}),
        }


class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ['area', 'nombre']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Activos Fijos'}),
        }


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Grupo Corporativo'}),
        }


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['tenant', 'nombre']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Razón Social'}),
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


class TipoLicenciaForm(forms.ModelForm):
    class Meta:
        model = TipoLicencia
        fields = ['nombre', 'fabricante']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Microsoft 365 E3'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Microsoft'}),
        }


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