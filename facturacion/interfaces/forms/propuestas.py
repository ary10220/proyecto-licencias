"""Forms de Propuesta comercial (cotizacion)."""

from django import forms
from django.forms import inlineformset_factory
from django.db.models import Q

from licencias.models import Empresa, Tenant
from ...infrastructure.models import DetallePropuesta, PropuestaLicencia


class PropuestaForm(forms.ModelForm):
    """
    Form principal de la cotizacion.

    El campo `numero` es de SOLO LECTURA: se autogenera en `save()`
    del modelo con formato PROP-YYYY-NNNN. El widget se renderiza
    deshabilitado en el form para que el usuario vea el numero pero
    no lo pueda editar.
    """

    class Meta:
        model = PropuestaLicencia
        fields = [
            'tenant', 'empresa', 'numero', 'fecha',
            'descuento_porcentaje', 'descuento_monto', 'impuesto_porcentaje',
            'observaciones',
        ]
        widgets = {
            'tenant':  forms.Select(attrs={'class': 'form-select'}),
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'numero':  forms.TextInput(attrs={
                'class': 'form-control bg-light',
                'placeholder': 'Auto-generado: PROP-YYYY-NNNN',
                'readonly': 'readonly',
            }),
            'fecha':   forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'descuento_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'descuento_monto':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'impuesto_porcentaje':  forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Numero opcional (se autogenera en save)
        self.fields['numero'].required = False

        # Tenant: solo activos (+ el actual al editar)
        tenant_qs = Tenant.objects.filter(activo=True)
        if self.instance.pk and self.instance.tenant_id:
            tenant_qs = Tenant.objects.filter(Q(activo=True) | Q(pk=self.instance.tenant_id))
        self.fields['tenant'].queryset = tenant_qs.order_by('nombre')

        tenant_id = None
        if self.is_bound:
            tenant_id = self.data.get(self.add_prefix('tenant')) or self.data.get('tenant')
        elif self.instance.pk and self.instance.tenant_id:
            tenant_id = self.instance.tenant_id

        # Empresa: vacia hasta elegir tenant; en POST se carga desde el tenant enviado.
        if tenant_id:
            self.fields['empresa'].queryset = Empresa.objects.filter(
                tenant_id=tenant_id
            ).order_by('nombre')
        else:
            self.fields['empresa'].queryset = Empresa.objects.none()
            self.fields['empresa'].widget.attrs['data-needs-tenant'] = '1'

    def clean(self):
        cleaned_data = super().clean()
        tenant = cleaned_data.get('tenant')
        empresa = cleaned_data.get('empresa')
        if tenant and empresa and empresa.tenant_id != tenant.id:
            self.add_error('empresa', 'La empresa seleccionada no pertenece al tenant indicado.')
        return cleaned_data


class PropuestaEditForm(PropuestaForm):
    class Meta(PropuestaForm.Meta):
        fields = [
            'tenant', 'empresa', 'numero', 'fecha', 'estado',
            'descuento_porcentaje', 'descuento_monto', 'impuesto_porcentaje',
            'observaciones',
        ]
        widgets = {
            **PropuestaForm.Meta.widgets,
            'estado': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].choices = [
            ('BORRADOR', 'Borrador'),
            ('PENDIENTE', 'Pendiente'),
        ]


class PropuestaAdminForm(forms.ModelForm):
    """
    Edicion administrativa para cotizaciones aprobadas.

    No permite tocar cliente, productos, precios, descuentos ni fechas; solo
    estado administrativo y observaciones.
    """

    class Meta:
        model = PropuestaLicencia
        fields = ['estado', 'observaciones']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].choices = [
            ('APROBADA', 'Aprobada'),
            ('ANULADA', 'Anulada'),
        ]


class DetallePropuestaForm(forms.ModelForm):
    """
    Detalle de cotizacion con fechas de vigencia + descuentos por linea.

    Si `precio_unitario` queda en 0/vacio, se autorrellena desde
    `TipoLicencia.precio_venta` en `clean()`.
    """

    class Meta:
        model = DetallePropuesta
        fields = [
            'tipo_licencia', 'cantidad', 'precio_unitario',
            'fecha_inicio_uso', 'fecha_fin_uso',
            'descuento_porcentaje', 'descuento_monto',
            'observaciones',
        ]
        widgets = {
            'tipo_licencia': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto',
                'step': '0.01', 'min': '0',
            }),
            'fecha_inicio_uso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin_uso':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descuento_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'descuento_monto':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'observaciones': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['precio_unitario'].required = False

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 1:
            raise forms.ValidationError('La cantidad debe ser al menos 1.')
        return cantidad

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_licencia')
        precio = cleaned_data.get('precio_unitario')
        # Auto-fill desde catalogo si vino vacio o 0
        if tipo and (precio is None or precio == 0):
            cleaned_data['precio_unitario'] = getattr(tipo, 'precio_venta', 0) or 0

        # Validar coherencia de fechas
        ini = cleaned_data.get('fecha_inicio_uso')
        fin = cleaned_data.get('fecha_fin_uso')
        if ini and fin and fin < ini:
            self.add_error('fecha_fin_uso', 'La fecha fin no puede ser anterior a la fecha inicio.')

        return cleaned_data


DetallePropuestaFormSet = inlineformset_factory(
    PropuestaLicencia,
    DetallePropuesta,
    form=DetallePropuestaForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
