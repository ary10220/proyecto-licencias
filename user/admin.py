from django.contrib import admin
from .models import AreaUsuario, PerfilUsuario


@admin.register(AreaUsuario)
class AreaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'area_usuario', 'cargo')
    search_fields = ('user__username', 'user__email', 'cargo__nombre', 'area_usuario__nombre')
    list_filter = ('area_usuario',)
