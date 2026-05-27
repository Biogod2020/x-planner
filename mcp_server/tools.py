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


def create_mission(title: str, objective: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    return _dump(repository_for(db_path).create_mission(title=title, objective=objective))


def save_mission_brief(mission_id: int, brief: str, db_path: str | None = None) -> dict[str, Any]:
    return _dump(repository_for(db_path).save_mission_brief(mission_id=mission_id, brief=brief))


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
    return _dump(task)


def list_tasks(
    mission_id: int | None = None,
    status: str | None = None,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    return [_dump(task) for task in repository_for(db_path).list_tasks(mission_id=mission_id, status=status)]


def select_today_mainline(task_id: int, day: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    return _dump(repository_for(db_path).select_today_mainline(task_id=task_id, day=day))


def submit_evidence(
    task_id: int,
    description: str,
    uri: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    return _dump(repository_for(db_path).submit_evidence(task_id=task_id, description=description, uri=uri))


def record_evidence_audit(
    evidence_id: int,
    audit_status: str,
    audit_notes: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    return _dump(
        repository_for(db_path).record_evidence_audit(
            evidence_id=evidence_id,
            audit_status=audit_status,
            audit_notes=audit_notes,
        )
    )


def run_review(
    review_type: str,
    decision: str,
    notes: str,
    mission_id: int | None = None,
    task_id: int | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    return _dump(
        repository_for(db_path).run_review(
            review_type=review_type,
            decision=decision,
            notes=notes,
            mission_id=mission_id,
            task_id=task_id,
        )
    )


def update_task_status(task_id: int, status: str, db_path: str | None = None) -> dict[str, Any]:
    return _dump(repository_for(db_path).update_task_status(task_id=task_id, status=status))


def update_capacity_log(
    day: str | None = None,
    available_minutes: int = 0,
    energy_level: int = 3,
    notes: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    return _dump(
        repository_for(db_path).update_capacity_log(
            day=day,
            available_minutes=available_minutes,
            energy_level=energy_level,
            notes=notes,
        )
    )


def get_status_brief(day: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    return repository_for(db_path).get_status_brief(day=day)
