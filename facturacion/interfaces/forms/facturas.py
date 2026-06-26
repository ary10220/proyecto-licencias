from django import forms
from django.db.models import Q

from licencias.models import Empresa, Tenant
from ...infrastructure.models import DetalleFactura, Factura, PagoFactura


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = [
            'propuesta',
            'proveedor',
            'tenant',
            'empresa',
            'numero',
            'fecha',
            'razon_social',
            'nit',
            'estado',
            'observaciones',
        ]
        widgets = {
            'propuesta': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'tenant':    forms.Select(attrs={'class': 'form-select'}),
            'empresa':   forms.Select(attrs={'class': 'form-select'}),
            'numero':    forms.TextInput(attrs={'class': 'form-control'}),
            'fecha':     forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nit':       forms.TextInput(attrs={'class': 'form-control'}),
            'estado':    forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

        # Empresa: vacia hasta elegir tenant. En POST se carga desde el tenant enviado.
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
        propuesta = cleaned_data.get('propuesta')
        if tenant and empresa and empresa.tenant_id != tenant.id:
            self.add_error('empresa', 'La empresa seleccionada no pertenece al tenant de la factura.')
        if propuesta and empresa and propuesta.empresa_id != empresa.id:
            self.add_error('propuesta', 'La propuesta seleccionada pertenece a otra empresa.')
        return cleaned_data


class FacturaFiscalForm(forms.ModelForm):
    """Edicion limitada a datos fiscales/complementarios de la factura."""

    class Meta:
        model = Factura
        fields = [
            'razon_social',
            'nit',
            'direccion_fiscal',
            'metodo_pago',
            'estado',
            'observaciones',
        ]
        widgets = {
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nit': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_fiscal': forms.TextInput(attrs={'class': 'form-control'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DetalleFacturaForm(forms.ModelForm):
    class Meta:
        model = DetalleFactura
        fields = ['tipo_licencia', 'cantidad', 'precio_unitario', 'fecha_vencimiento']
        widgets = {
            'tipo_licencia': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto (precio_venta)',
                'step': '0.01',
                'min': '0',
            }),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
        if tipo and (precio is None or precio == 0):
            cleaned_data['precio_unitario'] = getattr(tipo, 'precio_venta', 0) or 0
        return cleaned_data


class PagoFacturaForm(forms.ModelForm):
    """Registro de pagos asociados a una factura."""

    class Meta:
        model = PagoFactura
        fields = ['fecha_pago', 'monto', 'metodo_pago', 'referencia', 'comprobante', 'observaciones']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaccion, comprobante o recibo',
            }),
            'comprobante': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas internas del pago',
            }),
        }

    def __init__(self, *args, factura=None, **kwargs):
        instance = kwargs.get('instance')
        self.factura = factura or getattr(instance, 'factura', None)
        super().__init__(*args, **kwargs)
        if self.factura and not self.is_bound and not self.instance.pk:
            self.fields['monto'].initial = self.factura.saldo_pendiente
            self.fields['metodo_pago'].initial = self.factura.metodo_pago

    def _saldo_editable(self):
        if not self.factura:
            return None
        saldo = self.factura.saldo_pendiente
        if self.instance.pk and self.instance.estado == PagoFactura.ESTADO_ACTIVO:
            saldo += self.instance.monto
        return saldo

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is None:
            return monto
        if monto <= 0:
            raise forms.ValidationError('El monto del pago debe ser mayor a cero.')
        if self.factura:
            saldo = self._saldo_editable()
            if saldo is not None and monto > saldo:
                raise forms.ValidationError(f'El monto no puede superar el saldo disponible ({saldo:.2f}).')
        return monto

    def clean(self):
        cleaned_data = super().clean()
        if self.factura and self.factura.estado == 'ANULADA':
            raise forms.ValidationError('No se pueden registrar pagos en una factura anulada.')
        if self.instance.pk and self.instance.estado == PagoFactura.ESTADO_ANULADO:
            raise forms.ValidationError('No se puede editar un pago anulado.')
        saldo = self._saldo_editable()
        if self.factura and saldo is not None and saldo <= 0:
            raise forms.ValidationError('La factura no tiene saldo pendiente.')
        return cleaned_data
