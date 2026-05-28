from __future__ import annotations

from mission_core.models import Review
from mission_core.repository import MissionControlRepository


def run_review(
    repository: MissionControlRepository,
    review_type: str,
    decision: str,
    notes: str,
    mission_id: int | None = None,
    task_id: int | None = None,
) -> Review:
    return repository.run_review(
        review_type=review_type,
        decision=decision,
        notes=notes,
        mission_id=mission_id,
        task_id=task_id,
    )
