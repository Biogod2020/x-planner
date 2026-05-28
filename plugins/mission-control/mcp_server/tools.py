from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from mission_core.db import connect, initialize_database
from mission_core.repository import MissionControlRepository

TOOL_NAMES = [
    "create_mission",
    "save_mission_brief",
    "list_missions",
    "create_task",
    "list_tasks",
    "select_today_mainline",
    "submit_evidence",
    "record_evidence_audit",
    "run_review",
    "update_task_status",
    "update_capacity_log",
    "get_status_brief",
]


def default_db_path() -> str:
    return os.environ.get("MISSION_CONTROL_DB", ".mission-control.sqlite3")


def repository_for(db_path: Optional[str] = None) -> MissionControlRepository:
    connection = connect(Path(db_path or default_db_path()))
    initialize_database(connection)
    return MissionControlRepository(connection)


def _dump(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _with_guidance(payload: dict[str, Any], next_required_action: str, reason: str) -> dict[str, Any]:
    payload.setdefault("ok", True)
    payload["next_required_action"] = next_required_action
    payload["reason"] = reason
    return payload


def _blocked_transition(error: ValueError) -> dict[str, Any]:
    reason = str(error)
    if "accepted evidence audit" in reason or "evidence" in reason:
        next_action = "submit_or_accept_evidence"
    elif "review" in reason:
        next_action = "run_review"
    else:
        next_action = "inspect_status_brief"
    return {
        "ok": False,
        "error": reason,
        "reason": reason,
        "next_required_action": next_action,
    }


def create_mission(title: str, objective: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    mission = _dump(repository_for(db_path).create_mission(title=title, objective=objective))
    return _with_guidance(mission, "save_mission_brief", "mission exists; persist a Mission Brief before creating ready tasks")


def save_mission_brief(mission_id: int, brief: str, db_path: str | None = None) -> dict[str, Any]:
    mission = _dump(repository_for(db_path).save_mission_brief(mission_id=mission_id, brief=brief))
    return _with_guidance(mission, "create_task", "Mission Brief is saved; create only tasks with next_action, expected_output, and evidence_required")


def list_missions(status: str | None = None, db_path: str | None = None) -> list[dict[str, Any]]:
    return [_dump(mission) for mission in repository_for(db_path).list_missions(status=status)]


def create_task(
    mission_id: int,
    title: str,
    next_action: str,
    expected_output: str,
    evidence_required: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    task = repository_for(db_path).create_task(
        mission_id=mission_id,
        title=title,
        next_action=next_action,
        expected_output=expected_output,
        evidence_required=evidence_required,
    )
    return _with_guidance(_dump(task), "select_today_mainline", "ready task created; choose exactly one daily mainline before execution")


def list_tasks(
    mission_id: int | None = None,
    status: str | None = None,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    return [_dump(task) for task in repository_for(db_path).list_tasks(mission_id=mission_id, status=status)]


def select_today_mainline(task_id: int, day: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    task = _dump(repository_for(db_path).select_today_mainline(task_id=task_id, day=day))
    return _with_guidance(task, "submit_evidence", "mainline selected; execute the next_action and submit inspectable evidence before completion")


def submit_evidence(
    task_id: int,
    description: str,
    uri: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    evidence = _dump(repository_for(db_path).submit_evidence(task_id=task_id, description=description, uri=uri))
    return _with_guidance(evidence, "record_evidence_audit", "evidence submitted; audit it as accepted or rejected before terminal task status")


def record_evidence_audit(
    evidence_id: int,
    audit_status: str,
    audit_notes: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    evidence = _dump(
        repository_for(db_path).record_evidence_audit(
            evidence_id=evidence_id,
            audit_status=audit_status,
            audit_notes=audit_notes,
        )
    )
    if evidence["audit_status"] == "accepted":
        return _with_guidance(evidence, "update_task_status", "accepted evidence audit exists; terminal task status is now allowed")
    return _with_guidance(evidence, "submit_evidence", "evidence was not accepted; submit stronger evidence before terminal task status")


def run_review(
    review_type: str,
    decision: str,
    notes: str,
    mission_id: int | None = None,
    task_id: int | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    review = _dump(
        repository_for(db_path).run_review(
            review_type=review_type,
            decision=decision,
            notes=notes,
            mission_id=mission_id,
            task_id=task_id,
        )
    )
    return _with_guidance(review, "get_status_brief", "review recorded; inspect status before choosing the next action")


def update_task_status(task_id: int, status: str, db_path: str | None = None) -> dict[str, Any]:
    try:
        task = _dump(repository_for(db_path).update_task_status(task_id=task_id, status=status))
    except ValueError as error:
        return _blocked_transition(error)
    if task["status"] in {"completed", "accepted"}:
        return _with_guidance(task, "run_review", "terminal task status recorded after accepted evidence audit; record or inspect review decision")
    if task["status"] == "failed" and task.get("requires_failure_review"):
        return _with_guidance(task, "run_review", "failure_count is at least 2; choose shrink, split, block, pause, or kill")
    return _with_guidance(task, "get_status_brief", "status updated; inspect current mission state before continuing")


def update_capacity_log(
    day: str | None = None,
    available_minutes: int = 0,
    energy_level: int = 3,
    notes: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    capacity = _dump(
        repository_for(db_path).update_capacity_log(
            day=day,
            available_minutes=available_minutes,
            energy_level=energy_level,
            notes=notes,
        )
    )
    return _with_guidance(capacity, "select_today_mainline", "capacity recorded; select exactly one daily mainline task")


def get_status_brief(day: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    return repository_for(db_path).get_status_brief(day=day)
