from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MissionStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    PAUSED = "paused"
    COMPLETED = "completed"
    KILLED = "killed"


class TaskStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"
    ACCEPTED = "accepted"


class RiskStatus(StrEnum):
    OPEN = "open"
    MITIGATED = "mitigated"
    CLOSED = "closed"


class CommitmentStatus(StrEnum):
    ACTIVE = "active"
    MET = "met"
    MISSED = "missed"
    CANCELED = "canceled"


class EvidenceAuditStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Mission(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: int
    title: str
    objective: Optional[str] = None
    status: MissionStatus = MissionStatus.ACTIVE
    brief: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Task(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: int
    mission_id: int
    title: str
    status: TaskStatus
    next_action: str
    expected_output: str
    evidence_required: str
    failure_count: int = 0
    requires_failure_review: bool = False
    today_mainline_on: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class Evidence(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: int
    task_id: int
    description: str
    uri: Optional[str] = None
    audit_status: EvidenceAuditStatus = EvidenceAuditStatus.PENDING
    audit_notes: Optional[str] = None
    created_at: datetime
    audited_at: Optional[datetime] = None


class Review(BaseModel):
    id: int
    mission_id: Optional[int] = None
    task_id: Optional[int] = None
    review_type: str
    decision: str
    notes: str
    created_at: datetime


class Risk(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: int
    mission_id: Optional[int] = None
    task_id: Optional[int] = None
    description: str
    status: RiskStatus = RiskStatus.OPEN
    mitigation: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CapacityLog(BaseModel):
    id: int
    day: date
    available_minutes: int = Field(ge=0)
    energy_level: int = Field(ge=1, le=5)
    notes: Optional[str] = None
    created_at: datetime


class Commitment(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: int
    mission_id: Optional[int] = None
    task_id: Optional[int] = None
    description: str
    committed_on: date
    due_on: Optional[date] = None
    status: CommitmentStatus = CommitmentStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
