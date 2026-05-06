from __future__ import annotations

from django.db.models import QuerySet

from ...models import Bitacora


def query_eventos() -> QuerySet[Bitacora]:
    return Bitacora.objects.select_related("usuario")


def distinct_usernames() -> QuerySet[str]:
    return Bitacora.objects.values_list("usuario__username", flat=True).distinct()

