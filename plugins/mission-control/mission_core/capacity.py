from __future__ import annotations

from datetime import date

from mission_core.models import CapacityLog
from mission_core.repository import MissionControlRepository


def update_capacity_log(
    repository: MissionControlRepository,
    day: str | date | None = None,
    available_minutes: int = 0,
    energy_level: int = 3,
    notes: str | None = None,
) -> CapacityLog:
    return repository.update_capacity_log(
        day=day,
        available_minutes=available_minutes,
        energy_level=energy_level,
        notes=notes,
    )
