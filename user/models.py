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


class AreaUsuario(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Area de usuario"
        verbose_name_plural = "Areas de usuario"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    area = models.CharField(max_length=40, choices=AREAS_USUARIO, blank=True, null=True)
    area_usuario = models.ForeignKey(AreaUsuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='perfiles')
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)
    foto = models.FileField(upload_to='perfiles/', blank=True, null=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"Perfil de {self.user.username}"
