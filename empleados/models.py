from django.db import models

class GerenciaDivision(models.Model):
    """
    Nivel 1 de la jerarquía organizacional: División.
    """
    empresa = models.ForeignKey('licencias.Empresa', on_delete=models.CASCADE, related_name='divisiones')
    codigo = models.CharField(max_length=10, help_text="Código identificador de la división. Ej: GDO")
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Gerencia de División"
        verbose_name_plural = "Gerencias de División"
        unique_together = ('empresa', 'codigo')

    def __str__(self):
        return f"{self.empresa.nombre} | {self.codigo} - {self.nombre}"


class GerenciaArea(models.Model):
    """
    Nivel 2 de la jerarquía organizacional: Área.
    """
    empresa = models.ForeignKey('licencias.Empresa', on_delete=models.CASCADE, related_name='areas')
    division = models.ForeignKey(GerenciaDivision, on_delete=models.CASCADE, related_name='areas', null=True, blank=True)
    codigo = models.CharField(max_length=10, help_text="Código identificador del área. Ej: GHC", blank=True, null=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Gerencia de Área"
        verbose_name_plural = "Gerencias de Área"

    def __str__(self):
        codigo_str = self.codigo if self.codigo else "S/C"
        return f"{codigo_str} - {self.nombre}"


class Unidad(models.Model):
    """
    Nivel 3 de la jerarquía organizacional: Unidad operativa dependiente de un Área.
    """
    area = models.ForeignKey(GerenciaArea, on_delete=models.CASCADE, related_name='unidades')
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} ({self.area.codigo})"


class Cargo(models.Model):
    """
    Catálogo de cargos que pueden asignarse a usuarios del sistema.
    """
    area_usuario = models.ForeignKey('user.AreaUsuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='cargos')
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['nombre']

    def __str__(self):
        if self.area_usuario:
            return f"{self.nombre} ({self.area_usuario.nombre})"
        return self.nombre


class Empleado(models.Model):
    """
    Entidad central que representa a un colaborador dentro del ecosistema corporativo.
    """
    nombre_completo = models.CharField(max_length=200)
    ci = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    email_principal = models.EmailField(unique=True, verbose_name="Correo Electrónico Principal")
    empresa = models.ForeignKey('licencias.Empresa', on_delete=models.PROTECT, verbose_name="Empresa")

    division = models.ForeignKey(GerenciaDivision, on_delete=models.SET_NULL, verbose_name="Gerencia de División", null=True, blank=True)
    area = models.ForeignKey(GerenciaArea, on_delete=models.PROTECT, verbose_name="Gerencia de Área") 
    unidad = models.ForeignKey(Unidad, on_delete=models.SET_NULL, null=True, blank=True)
    
    centro_de_costos = models.CharField(max_length=20, blank=True, null=True, help_text="Código del centro de costos asignado")
    puesto = models.CharField(max_length=100, blank=True, null=True)
    
    pais = models.CharField(max_length=30, default="Bolivia")
    ciudad = models.CharField(max_length=80, default="Santa Cruz de la Sierra")
    oficina = models.CharField(max_length=80, blank=True, null=True, help_text="Ubicación física operativa")
    
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre_completo}"
