from django.db.models import QuerySet

from licencias.models import Tenant


def list_tenants() -> QuerySet[Tenant]:
    return Tenant.objects.all()

