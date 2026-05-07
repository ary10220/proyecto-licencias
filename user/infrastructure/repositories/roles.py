from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.db.models import QuerySet


def list_roles() -> QuerySet[Group]:
    return Group.objects.prefetch_related('permissions').order_by('id')


def get_rol(group_id: int) -> Group:
    return Group.objects.get(id=group_id)


def get_rol_with_permissions(group_id: int) -> Group:
    return Group.objects.prefetch_related('permissions__content_type').get(id=group_id)


def count_permisos_rol(rol: Group) -> int:
    return rol.permissions.count()


def list_permissions_for_codes(codes: list[str]) -> QuerySet[Permission]:
    """
    `codes`: lista como ["app.codename", ...]
    """
    qs = Permission.objects.none()
    for code in codes:
        app_label, codename = code.split('.', 1)
        qs = qs | Permission.objects.filter(content_type__app_label=app_label, codename=codename)
    return qs.select_related('content_type').order_by('content_type__model', 'codename')
