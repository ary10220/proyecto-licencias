from django.db import models
from django.contrib.auth.models import User
from empleados.models import Cargo


AREAS_USUARIO = [
    ('administracion', 'Administración'),
    ('soporte', 'Soporte'),
    ('operaciones', 'Operaciones'),
    ('auditoria', 'Auditoría'),
    ('sistemas', 'Sistemas'),
    ('cliente', 'Cliente'),
]


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    area = models.CharField(max_length=40, choices=AREAS_USUARIO, blank=True, null=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"Perfil de {self.user.username}"
