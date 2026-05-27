from __future__ import annotations

from mission_core.models import Evidence, EvidenceAuditStatus
from mission_core.repository import MissionControlRepository


def submit_evidence(
    repository: MissionControlRepository,
    task_id: int,
    description: str,
    uri: str | None = None,
) -> Evidence:
    return repository.submit_evidence(task_id=task_id, description=description, uri=uri)


def record_evidence_audit(
    repository: MissionControlRepository,
    evidence_id: int,
    audit_status: EvidenceAuditStatus | str,
    audit_notes: str | None = None,
) -> Evidence:
    return repository.record_evidence_audit(
        evidence_id=evidence_id,
        audit_status=audit_status,
        audit_notes=audit_notes,
    )
