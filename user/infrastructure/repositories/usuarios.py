from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import QuerySet

from ...models import PerfilUsuario


def list_usuarios() -> QuerySet[User]:
    return (
        User.objects
        .select_related('perfil', 'perfil__area_usuario', 'perfil__cargo')
        .prefetch_related('groups')
        .order_by('id')
    )


def get_usuario(user_id: int) -> User:
    return User.objects.get(id=user_id)


def toggle_usuario_activo(usuario: User) -> User:
    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])
    return usuario


def get_or_create_perfil(user: User) -> PerfilUsuario:
    try:
        return user.perfil
    except Exception:
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        return perfil
