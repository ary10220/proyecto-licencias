from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BitacoraEvent:
    """Entidad de dominio (no ORM) para representar un evento de bitácora."""

    username: Optional[str]
    accion: str
    modulo: str
    descripcion: str
    ip: Optional[str] = None

