"""
Re-export de modelos desde infrastructure/models.py para compatibilidad
con Django (que busca <app>/models.py). Los modelos fisicos estan en
otras apps (licencias, empleados); aqui solo se exponen para uso del
modulo.
"""

from .infrastructure.models import *  # noqa: F401,F403
