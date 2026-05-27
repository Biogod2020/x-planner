from mission_core.db import connect, initialize_database
from mission_core.repository import MissionControlRepository


def repo(tmp_path):
    conn = connect(tmp_path / "mission.sqlite3")
    initialize_database(conn)
    return MissionControlRepository(conn)


def test_submit_evidence_and_record_audit(tmp_path):
    repository = repo(tmp_path)
    mission = repository.create_mission(title="Evidence mission")
    task = repository.create_task(
        mission_id=mission.id,
        title="Capture evidence",
        next_action="Run verification",
        expected_output="Verification output",
        evidence_required="Command output proving result",
    )

    evidence = repository.submit_evidence(
        task.id,
        description="pytest passed",
        uri="file://test-output.txt",
    )
    audited = repository.record_evidence_audit(
        evidence.id,
        audit_status="accepted",
        audit_notes="Output matches requirement.",
    )

    assert audited.audit_status == "accepted"
    assert audited.audit_notes == "Output matches requirement."
