from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeevaPrincipal:
    role: str
    entity_id: int
    email: str

    @property
    def is_authenticated(self) -> bool:  # DRF / Django compatibility
        return True
