"""
Formularios del modulo licencias/.

Despues de la migracion a `gestion_global`, este archivo contiene:
  - EmpleadoForm        (operativo de empleados, vive aca por compat)
  - ProveedorForm       (catalogo de licenciamiento)
  - TipoLicenciaForm    (catalogo de licenciamiento, ahora con precios centralizados)
  - LicenciaForm        (operativo de licencias)

Los formularios de Tenant, Empresa, Division, Area, Unidad viven en
`gestion_global/interfaces/forms/`.
"""

from django import forms
from django.db.models import Q
from empleados.models import Empleado
from .models import Proveedor, TipoLicencia, Licencia


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
        fields = [
            'nombre', 'razon_social', 'nit',
            'contacto', 'email', 'telefono',
            'direccion', 'sitio_web',
            'observaciones', 'activo',
        ]
        widgets = {
            'nombre':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre comercial'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razon social legal'}),
            'nit':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIT / RUC'}),
            'contacto':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona de contacto'}),
            'email':        forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'comercial@proveedor.com'}),
            'telefono':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+591 70000000'}),
            'direccion':    forms.TextInput(attrs={'class': 'form-control'}),
            'sitio_web':    forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        fields = [
            'codigo', 'nombre', 'fabricante', 'descripcion',
            'precio_compra', 'precio_venta', 'moneda',
            'proveedor_default', 'stock_minimo', 'duracion_dias',
            'observaciones', 'activo',
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'M365-BB'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Microsoft 365 E3'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Microsoft'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Descripcion comercial visible en cotizaciones'
            }),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'precio_venta':  forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'proveedor_default': forms.Select(attrs={'class': 'form-select'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'duracion_dias': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        fields = [
            'tenant', 'empresa', 'tipo', 'proveedor',
            'estado_operativo', 'fecha_compra', 'fecha_inicio',
            'fecha_activacion', 'fecha_vencimiento', 'observaciones',
        ]
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'empresa': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'tipo': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'proveedor': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'estado_operativo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_activacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].queryset = TipoLicencia.objects.filter(activo=True).order_by('fabricante', 'nombre')
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True).order_by('nombre')
        self.fields['estado_operativo'].choices = Licencia.ESTADOS_OPERATIVOS

        tenant_qs = self.fields['tenant'].queryset
        if self.instance.pk and self.instance.tenant_id:
            tenant_qs = tenant_qs.filter(Q(activo=True) | Q(pk=self.instance.tenant_id))
        else:
            tenant_qs = tenant_qs.filter(activo=True)
        self.fields['tenant'].queryset = tenant_qs.order_by('nombre')

        tenant_id = None
        if self.is_bound:
            tenant_id = self.data.get(self.add_prefix('tenant')) or self.data.get('tenant')
        elif self.instance.pk and self.instance.tenant_id:
            tenant_id = self.instance.tenant_id

        if tenant_id:
            self.fields['empresa'].queryset = self.fields['empresa'].queryset.filter(
                tenant_id=tenant_id,
                activo=True,
            ).order_by('nombre')
        else:
            self.fields['empresa'].queryset = self.fields['empresa'].queryset.none()

    def clean(self):
        cleaned_data = super().clean()
        tenant = cleaned_data.get('tenant')
        empresa = cleaned_data.get('empresa')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        estado_operativo = cleaned_data.get('estado_operativo')
        if tenant and empresa and empresa.tenant_id != tenant.id:
            self.add_error('empresa', 'La empresa seleccionada no pertenece al tenant indicado.')
        if fecha_inicio and fecha_vencimiento and fecha_vencimiento < fecha_inicio:
            self.add_error('fecha_vencimiento', 'La fecha de vencimiento no puede ser anterior al inicio.')
        if self.instance.pk and self.instance.asignaciones.filter(activo=True).exists():
            if estado_operativo in {Licencia.ESTADO_DISPONIBLE, Licencia.ESTADO_REVOCADA}:
                self.add_error('estado_operativo', 'Libera la asignacion activa antes de marcarla disponible o revocada.')
        elif estado_operativo == Licencia.ESTADO_ASIGNADA:
            self.add_error('estado_operativo', 'Para marcar como asignada debes usar el flujo de asignacion.')
        return cleaned_data
