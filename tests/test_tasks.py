import pytest

from mission_core.db import connect, initialize_database
from mission_core.models import TaskStatus
from mission_core.repository import MissionControlRepository


def repo(tmp_path):
    conn = connect(tmp_path / "mission.sqlite3")
    initialize_database(conn)
    return MissionControlRepository(conn)


def mission(repository):
    return repository.create_mission(title="Test mission")


def test_creating_a_valid_task(tmp_path):
    repository = repo(tmp_path)
    current_mission = mission(repository)

    task = repository.create_task(
        mission_id=current_mission.id,
        title="Write schema",
        next_action="Draft SQLite schema",
        expected_output="SCHEMA.md describes all tables",
        evidence_required="Committed schema doc and passing schema tests",
    )

    assert task.status == TaskStatus.READY
    assert task.evidence_required == "Committed schema doc and passing schema tests"


def test_rejecting_a_task_without_evidence_required(tmp_path):
    repository = repo(tmp_path)
    current_mission = mission(repository)

    try:
        repository.create_task(
            mission_id=current_mission.id,
            title="Vague work",
            next_action="Do work",
            expected_output="Something improved",
            evidence_required="",
        )
    except ValueError as exc:
        assert "evidence_required" in str(exc)
    else:
        raise AssertionError("task without evidence_required should be rejected")


def test_rejecting_completion_without_evidence(tmp_path):
    repository = repo(tmp_path)
    current_mission = mission(repository)
    task = repository.create_task(
        mission_id=current_mission.id,
        title="Write tests",
        next_action="Add failing tests",
        expected_output="Tests describe required rules",
        evidence_required="pytest output showing red tests",
    )

    try:
        repository.update_task_status(task.id, TaskStatus.COMPLETED)
    except ValueError as exc:
        assert "evidence" in str(exc).lower()
    else:
        raise AssertionError("completion without evidence should be rejected")


def test_accepting_completion_with_evidence(tmp_path):
    repository = repo(tmp_path)
    current_mission = mission(repository)
    task = repository.create_task(
        mission_id=current_mission.id,
        title="Write docs",
        next_action="Draft README",
        expected_output="README explains test and server commands",
        evidence_required="README.md committed with commands",
    )
    repository.submit_evidence(task.id, description="README includes commands", uri="file://README.md")

    completed = repository.update_task_status(task.id, TaskStatus.COMPLETED)
    accepted = repository.update_task_status(task.id, TaskStatus.ACCEPTED)

    assert completed.status == TaskStatus.COMPLETED
    assert accepted.status == TaskStatus.ACCEPTED


def test_failure_count_escalation(tmp_path):
    repository = repo(tmp_path)
    current_mission = mission(repository)
    task = repository.create_task(
        mission_id=current_mission.id,
        title="Integrate MCP",
        next_action="Wire tool registry",
        expected_output="MCP tools callable in tests",
        evidence_required="MCP tool test output",
    )

    once = repository.update_task_status(task.id, TaskStatus.FAILED)
    twice = repository.update_task_status(task.id, TaskStatus.FAILED)

    assert once.failure_count == 1
    assert once.requires_failure_review is False
    assert twice.failure_count == 2
    assert twice.requires_failure_review is True


def test_selecting_one_daily_mainline_task(tmp_path):
    repository = repo(tmp_path)
    current_mission = mission(repository)
    first = repository.create_task(
        mission_id=current_mission.id,
        title="First",
        next_action="Do first",
        expected_output="First output",
        evidence_required="First evidence",
    )
    second = repository.create_task(
        mission_id=current_mission.id,
        title="Second",
        next_action="Do second",
        expected_output="Second output",
        evidence_required="Second evidence",
    )

    repository.select_today_mainline(first.id, day="2026-05-27")
    selected = repository.select_today_mainline(second.id, day="2026-05-27")

    tasks = repository.list_tasks(mission_id=current_mission.id)
    first_after = next(task for task in tasks if task.id == first.id)
    second_after = next(task for task in tasks if task.id == second.id)
    assert selected.id == second.id
    assert first_after.today_mainline_on is None
    assert second_after.today_mainline_on.isoformat() == "2026-05-27"

@pytest.mark.parametrize(
    ("field", "values"),
    [
        ("next_action", {"next_action": "", "expected_output": "Output", "evidence_required": "Evidence"}),
        ("expected_output", {"next_action": "Action", "expected_output": "", "evidence_required": "Evidence"}),
        ("evidence_required", {"next_action": "Action", "expected_output": "Output", "evidence_required": ""}),
    ],
)
def test_rejecting_ready_task_without_required_ready_fields(tmp_path, field, values):
    repository = repo(tmp_path)
    current_mission = mission(repository)

    with pytest.raises(ValueError, match=field):
        repository.create_task(
            mission_id=current_mission.id,
            title="Incomplete ready task",
            **values,
        )


def test_rejecting_acceptance_without_evidence(tmp_path):
    repository = repo(tmp_path)
    current_mission = mission(repository)
    task = repository.create_task(
        mission_id=current_mission.id,
        title="Accept task",
        next_action="Produce evidence",
        expected_output="Evidence exists",
        evidence_required="Evidence URI",
    )

    with pytest.raises(ValueError, match="evidence"):
        repository.update_task_status(task.id, TaskStatus.ACCEPTED)

