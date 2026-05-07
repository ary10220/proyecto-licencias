"""
Django expects `bitacora.models` to exist for migrations/admin autodiscovery.

We keep the ORM models in `bitacora.infrastructure.models` and re-export them here
to preserve a clean architecture without breaking imports.
"""

from .infrastructure.models import *  # noqa: F401,F403

