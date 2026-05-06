from __future__ import annotations

from django import forms


class BitacoraFiltroForm(forms.Form):
    usuario = forms.CharField(required=False)
    accion = forms.CharField(required=False)
    fecha_inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    fecha_fin = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

