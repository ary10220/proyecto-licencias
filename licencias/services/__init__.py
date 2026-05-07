"""
Servicios (capa application) del modulo `licencias`.

Re-exporta funciones para imports cortos:

    from licencias.services import enviar_token_desbloqueo
"""

from .desbloqueo import enviar_token_desbloqueo  # noqa: F401

__all__ = [
    "enviar_token_desbloqueo",
]
