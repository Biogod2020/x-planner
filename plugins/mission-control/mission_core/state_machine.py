from __future__ import annotations

from mission_core.models import MissionStatus, TaskStatus


def require_task_ready_fields(next_action: str, expected_output: str, evidence_required: str) -> None:
    missing = []
    if not next_action.strip():
        missing.append("next_action")
    if not expected_output.strip():
        missing.append("expected_output")
    if not evidence_required.strip():
        missing.append("evidence_required")
    if missing:
        raise ValueError("ready task requires " + ", ".join(missing))


def require_accepted_evidence_for_terminal_task(status: TaskStatus, accepted_evidence_count: int) -> None:
    if status in {TaskStatus.COMPLETED, TaskStatus.ACCEPTED} and accepted_evidence_count < 1:
        raise ValueError("task cannot be completed or accepted without accepted evidence audit")


def require_review_for_terminal_mission(status: MissionStatus, review_count: int) -> None:
    if status in {MissionStatus.COMPLETED, MissionStatus.KILLED} and review_count < 1:
        raise ValueError("completed or killed mission requires a review record")


def needs_failure_review(failure_count: int) -> bool:
    return failure_count >= 2
