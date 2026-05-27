from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Iterable, Optional

from mission_core.models import (
    CapacityLog,
    Commitment,
    CommitmentStatus,
    Evidence,
    EvidenceAuditStatus,
    Mission,
    MissionStatus,
    Review,
    Risk,
    RiskStatus,
    Task,
    TaskStatus,
)
from mission_core.state_machine import (
    needs_failure_review,
    require_evidence_for_terminal_task,
    require_review_for_terminal_mission,
    require_task_ready_fields,
)


def _today() -> date:
    return date.today()


def _day_string(day: Optional[str | date]) -> str:
    if day is None:
        return _today().isoformat()
    if isinstance(day, date):
        return day.isoformat()
    date.fromisoformat(day)
    return day


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _rows(cursor: sqlite3.Cursor) -> list[sqlite3.Row]:
    return list(cursor.fetchall())


def _mission_from_row(row: sqlite3.Row) -> Mission:
    return Mission(**dict(row))


def _task_from_row(row: sqlite3.Row) -> Task:
    data = dict(row)
    data["requires_failure_review"] = bool(data["requires_failure_review"])
    return Task(**data)


def _evidence_from_row(row: sqlite3.Row) -> Evidence:
    return Evidence(**dict(row))


def _review_from_row(row: sqlite3.Row) -> Review:
    return Review(**dict(row))


def _risk_from_row(row: sqlite3.Row) -> Risk:
    return Risk(**dict(row))


def _capacity_from_row(row: sqlite3.Row) -> CapacityLog:
    return CapacityLog(**dict(row))


def _commitment_from_row(row: sqlite3.Row) -> Commitment:
    return Commitment(**dict(row))


class MissionControlRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create_mission(self, title: str, objective: Optional[str] = None) -> Mission:
        title_value = _clean(title)
        if title_value is None:
            raise ValueError("mission title is required")
        cursor = self.connection.execute(
            "INSERT INTO missions (title, objective) VALUES (?, ?)",
            (title_value, _clean(objective)),
        )
        self.connection.commit()
        return self.get_mission(cursor.lastrowid)

    def save_mission_brief(self, mission_id: int, brief: str) -> Mission:
        if _clean(brief) is None:
            raise ValueError("mission brief is required")
        self._require_mission(mission_id)
        self.connection.execute(
            "UPDATE missions SET brief = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (brief.strip(), mission_id),
        )
        self.connection.commit()
        return self.get_mission(mission_id)

    def get_mission(self, mission_id: int) -> Mission:
        row = self.connection.execute("SELECT * FROM missions WHERE id = ?", (mission_id,)).fetchone()
        if row is None:
            raise ValueError(f"mission {mission_id} not found")
        return _mission_from_row(row)

    def list_missions(self, status: Optional[MissionStatus | str] = None) -> list[Mission]:
        if status is None:
            cursor = self.connection.execute("SELECT * FROM missions ORDER BY id")
        else:
            status_value = MissionStatus(status).value
            cursor = self.connection.execute(
                "SELECT * FROM missions WHERE status = ? ORDER BY id",
                (status_value,),
            )
        return [_mission_from_row(row) for row in _rows(cursor)]

    def update_mission_status(self, mission_id: int, status: MissionStatus | str) -> Mission:
        status_value = MissionStatus(status)
        self._require_mission(mission_id)
        review_count = self._mission_review_count(mission_id)
        require_review_for_terminal_mission(status_value, review_count)
        self.connection.execute(
            "UPDATE missions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status_value.value, mission_id),
        )
        self.connection.commit()
        return self.get_mission(mission_id)

    def create_task(
        self,
        mission_id: int,
        title: str,
        next_action: str,
        expected_output: str,
        evidence_required: str,
    ) -> Task:
        self._require_mission(mission_id)
        title_value = _clean(title)
        if title_value is None:
            raise ValueError("task title is required")
        require_task_ready_fields(next_action, expected_output, evidence_required)
        cursor = self.connection.execute(
            """
            INSERT INTO tasks (mission_id, title, status, next_action, expected_output, evidence_required)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                mission_id,
                title_value,
                TaskStatus.READY.value,
                next_action.strip(),
                expected_output.strip(),
                evidence_required.strip(),
            ),
        )
        self.connection.commit()
        return self.get_task(cursor.lastrowid)

    def get_task(self, task_id: int) -> Task:
        row = self.connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"task {task_id} not found")
        return _task_from_row(row)

    def list_tasks(
        self,
        mission_id: Optional[int] = None,
        status: Optional[TaskStatus | str] = None,
    ) -> list[Task]:
        filters: list[str] = []
        args: list[Any] = []
        if mission_id is not None:
            filters.append("mission_id = ?")
            args.append(mission_id)
        if status is not None:
            filters.append("status = ?")
            args.append(TaskStatus(status).value)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        cursor = self.connection.execute(f"SELECT * FROM tasks{where} ORDER BY id", args)
        return [_task_from_row(row) for row in _rows(cursor)]

    def select_today_mainline(self, task_id: int, day: Optional[str | date] = None) -> Task:
        task = self.get_task(task_id)
        day_value = _day_string(day)
        self.connection.execute(
            "UPDATE tasks SET today_mainline_on = NULL, updated_at = CURRENT_TIMESTAMP WHERE today_mainline_on = ?",
            (day_value,),
        )
        self.connection.execute(
            "UPDATE tasks SET today_mainline_on = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (day_value, task.id),
        )
        self.connection.commit()
        return self.get_task(task.id)

    def update_task_status(self, task_id: int, status: TaskStatus | str) -> Task:
        task = self.get_task(task_id)
        status_value = TaskStatus(status)
        if status_value == TaskStatus.READY:
            require_task_ready_fields(task.next_action, task.expected_output, task.evidence_required)
        evidence_count = self._task_evidence_count(task_id)
        require_evidence_for_terminal_task(status_value, evidence_count)
        failure_count = task.failure_count
        requires_review = task.requires_failure_review
        if status_value == TaskStatus.FAILED:
            failure_count += 1
            requires_review = needs_failure_review(failure_count)
        self.connection.execute(
            """
            UPDATE tasks
            SET status = ?, failure_count = ?, requires_failure_review = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status_value.value, failure_count, int(requires_review), task_id),
        )
        self.connection.commit()
        return self.get_task(task_id)

    def submit_evidence(self, task_id: int, description: str, uri: Optional[str] = None) -> Evidence:
        self._require_task(task_id)
        description_value = _clean(description)
        if description_value is None:
            raise ValueError("evidence description is required")
        cursor = self.connection.execute(
            "INSERT INTO evidence (task_id, description, uri) VALUES (?, ?, ?)",
            (task_id, description_value, _clean(uri)),
        )
        self.connection.commit()
        return self.get_evidence(cursor.lastrowid)

    def get_evidence(self, evidence_id: int) -> Evidence:
        row = self.connection.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
        if row is None:
            raise ValueError(f"evidence {evidence_id} not found")
        return _evidence_from_row(row)

    def record_evidence_audit(
        self,
        evidence_id: int,
        audit_status: EvidenceAuditStatus | str,
        audit_notes: Optional[str] = None,
    ) -> Evidence:
        status_value = EvidenceAuditStatus(audit_status)
        self.get_evidence(evidence_id)
        self.connection.execute(
            """
            UPDATE evidence
            SET audit_status = ?, audit_notes = ?, audited_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status_value.value, _clean(audit_notes), evidence_id),
        )
        self.connection.commit()
        return self.get_evidence(evidence_id)

    def list_evidence(self, task_id: int) -> list[Evidence]:
        self._require_task(task_id)
        cursor = self.connection.execute("SELECT * FROM evidence WHERE task_id = ? ORDER BY id", (task_id,))
        return [_evidence_from_row(row) for row in _rows(cursor)]

    def run_review(
        self,
        review_type: str,
        decision: str,
        notes: str,
        mission_id: Optional[int] = None,
        task_id: Optional[int] = None,
    ) -> Review:
        if mission_id is None and task_id is None:
            raise ValueError("review requires mission_id or task_id")
        if mission_id is not None:
            self._require_mission(mission_id)
        if task_id is not None:
            self._require_task(task_id)
        if _clean(review_type) is None or _clean(decision) is None or _clean(notes) is None:
            raise ValueError("review_type, decision, and notes are required")
        cursor = self.connection.execute(
            """
            INSERT INTO reviews (mission_id, task_id, review_type, decision, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (mission_id, task_id, review_type.strip(), decision.strip(), notes.strip()),
        )
        if task_id is not None:
            self.connection.execute(
                "UPDATE tasks SET requires_failure_review = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,),
            )
        if mission_id is not None:
            normalized_decision = decision.strip().lower()
            if normalized_decision in {MissionStatus.COMPLETED.value, MissionStatus.KILLED.value}:
                self.connection.execute(
                    "UPDATE missions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (normalized_decision, mission_id),
                )
            elif normalized_decision in {MissionStatus.BLOCKED.value, MissionStatus.PAUSED.value, MissionStatus.ACTIVE.value}:
                self.connection.execute(
                    "UPDATE missions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (normalized_decision, mission_id),
                )
        self.connection.commit()
        return self.get_review(cursor.lastrowid)

    def get_review(self, review_id: int) -> Review:
        row = self.connection.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
        if row is None:
            raise ValueError(f"review {review_id} not found")
        return _review_from_row(row)

    def list_reviews_due(self) -> list[Task]:
        cursor = self.connection.execute(
            "SELECT * FROM tasks WHERE requires_failure_review = 1 ORDER BY failure_count DESC, id"
        )
        return [_task_from_row(row) for row in _rows(cursor)]

    def update_capacity_log(
        self,
        day: Optional[str | date] = None,
        available_minutes: int = 0,
        energy_level: int = 3,
        notes: Optional[str] = None,
    ) -> CapacityLog:
        day_value = _day_string(day)
        if available_minutes < 0:
            raise ValueError("available_minutes must be >= 0")
        if not 1 <= energy_level <= 5:
            raise ValueError("energy_level must be between 1 and 5")
        self.connection.execute(
            """
            INSERT INTO capacity_logs (day, available_minutes, energy_level, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(day) DO UPDATE SET
                available_minutes = excluded.available_minutes,
                energy_level = excluded.energy_level,
                notes = excluded.notes
            """,
            (day_value, available_minutes, energy_level, _clean(notes)),
        )
        self.connection.commit()
        row = self.connection.execute("SELECT * FROM capacity_logs WHERE day = ?", (day_value,)).fetchone()
        return _capacity_from_row(row)

    def list_recent_capacity(self, limit: int = 7) -> list[CapacityLog]:
        cursor = self.connection.execute(
            "SELECT * FROM capacity_logs ORDER BY day DESC LIMIT ?",
            (limit,),
        )
        return [_capacity_from_row(row) for row in _rows(cursor)]

    def create_risk(
        self,
        description: str,
        mission_id: Optional[int] = None,
        task_id: Optional[int] = None,
        mitigation: Optional[str] = None,
    ) -> Risk:
        if mission_id is not None:
            self._require_mission(mission_id)
        if task_id is not None:
            self._require_task(task_id)
        description_value = _clean(description)
        if description_value is None:
            raise ValueError("risk description is required")
        cursor = self.connection.execute(
            "INSERT INTO risks (mission_id, task_id, description, mitigation) VALUES (?, ?, ?, ?)",
            (mission_id, task_id, description_value, _clean(mitigation)),
        )
        self.connection.commit()
        return self.get_risk(cursor.lastrowid)

    def get_risk(self, risk_id: int) -> Risk:
        row = self.connection.execute("SELECT * FROM risks WHERE id = ?", (risk_id,)).fetchone()
        if row is None:
            raise ValueError(f"risk {risk_id} not found")
        return _risk_from_row(row)

    def list_open_risks(self) -> list[Risk]:
        cursor = self.connection.execute("SELECT * FROM risks WHERE status = 'open' ORDER BY id")
        return [_risk_from_row(row) for row in _rows(cursor)]

    def create_commitment(
        self,
        description: str,
        committed_on: Optional[str | date] = None,
        due_on: Optional[str | date] = None,
        mission_id: Optional[int] = None,
        task_id: Optional[int] = None,
    ) -> Commitment:
        if mission_id is not None:
            self._require_mission(mission_id)
        if task_id is not None:
            self._require_task(task_id)
        description_value = _clean(description)
        if description_value is None:
            raise ValueError("commitment description is required")
        committed_value = _day_string(committed_on)
        due_value = _day_string(due_on) if due_on is not None else None
        cursor = self.connection.execute(
            """
            INSERT INTO commitments (mission_id, task_id, description, committed_on, due_on)
            VALUES (?, ?, ?, ?, ?)
            """,
            (mission_id, task_id, description_value, committed_value, due_value),
        )
        self.connection.commit()
        return self.get_commitment(cursor.lastrowid)

    def get_commitment(self, commitment_id: int) -> Commitment:
        row = self.connection.execute("SELECT * FROM commitments WHERE id = ?", (commitment_id,)).fetchone()
        if row is None:
            raise ValueError(f"commitment {commitment_id} not found")
        return _commitment_from_row(row)

    def get_status_brief(self, day: Optional[str | date] = None) -> dict[str, Any]:
        day_value = _day_string(day)
        active_missions = self.list_missions(MissionStatus.ACTIVE)
        mainline_row = self.connection.execute(
            "SELECT * FROM tasks WHERE today_mainline_on = ? ORDER BY id LIMIT 1",
            (day_value,),
        ).fetchone()
        today_mainline = None
        if mainline_row is not None:
            task = _task_from_row(mainline_row)
            today_mainline = {
                "task_id": task.id,
                "mission_id": task.mission_id,
                "title": task.title,
                "next_action": task.next_action,
                "expected_output": task.expected_output,
                "evidence_required": task.evidence_required,
                "failure_count": task.failure_count,
                "requires_failure_review": task.requires_failure_review,
            }
        return {
            "day": day_value,
            "active_missions": [
                {"mission_id": mission.id, "title": mission.title, "status": mission.status.value}
                for mission in active_missions
            ],
            "today_mainline": today_mainline,
            "review_due": [
                {
                    "task_id": task.id,
                    "mission_id": task.mission_id,
                    "title": task.title,
                    "failure_count": task.failure_count,
                }
                for task in self.list_reviews_due()
            ],
            "risks_open": [
                {"risk_id": risk.id, "description": risk.description, "mission_id": risk.mission_id}
                for risk in self.list_open_risks()
            ],
            "capacity_recent": [
                {
                    "day": log.day.isoformat(),
                    "available_minutes": log.available_minutes,
                    "energy_level": log.energy_level,
                }
                for log in self.list_recent_capacity()
            ],
        }

    def _require_mission(self, mission_id: int) -> None:
        self.get_mission(mission_id)

    def _require_task(self, task_id: int) -> None:
        self.get_task(task_id)

    def _task_evidence_count(self, task_id: int) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM evidence WHERE task_id = ?", (task_id,)).fetchone()
        return int(row["count"])

    def _mission_review_count(self, mission_id: int) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM reviews WHERE mission_id = ?", (mission_id,)).fetchone()
        return int(row["count"])
