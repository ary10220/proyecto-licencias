from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class Bitacora(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=255)
    modulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.usuario} - {self.accion} - {self.fecha}"

