from mission_core.db import connect, initialize_database
from mission_core.models import MissionStatus
from mission_core.repository import MissionControlRepository


def repo(tmp_path):
    conn = connect(tmp_path / "mission.sqlite3")
    initialize_database(conn)
    return MissionControlRepository(conn)


def test_creating_a_mission(tmp_path):
    repository = repo(tmp_path)

    mission = repository.create_mission(
        title="Ship Mission Control Core",
        objective="Build local-first core for agent-managed missions",
    )

    assert mission.id is not None
    assert mission.title == "Ship Mission Control Core"
    assert mission.objective == "Build local-first core for agent-managed missions"
    assert mission.status == MissionStatus.ACTIVE


def test_completed_or_killed_mission_requires_review(tmp_path):
    repository = repo(tmp_path)
    mission = repository.create_mission(title="Review gate")

    try:
        repository.update_mission_status(mission.id, MissionStatus.COMPLETED)
    except ValueError as exc:
        assert "review" in str(exc).lower()
    else:
        raise AssertionError("completed mission without review should be rejected")

    review = repository.run_review(
        review_type="mission",
        decision="completed",
        notes="Evidence accepted; mission can close.",
        mission_id=mission.id,
    )

    closed = repository.get_mission(mission.id)
    assert review.id is not None
    assert closed.status == MissionStatus.COMPLETED

def test_mission_supports_blocked_paused_completed_and_killed_states(tmp_path):
    repository = repo(tmp_path)
    blocked = repository.create_mission(title="Blocked mission")
    paused = repository.create_mission(title="Paused mission")
    completed = repository.create_mission(title="Completed mission")
    killed = repository.create_mission(title="Killed mission")

    assert repository.update_mission_status(blocked.id, MissionStatus.BLOCKED).status == MissionStatus.BLOCKED
    assert repository.update_mission_status(paused.id, MissionStatus.PAUSED).status == MissionStatus.PAUSED

    repository.run_review(
        review_type="mission",
        decision="completed",
        notes="Completion evidence accepted.",
        mission_id=completed.id,
    )
    repository.run_review(
        review_type="mission",
        decision="killed",
        notes="Mission no longer worth pursuing.",
        mission_id=killed.id,
    )

    assert repository.get_mission(completed.id).status == MissionStatus.COMPLETED
    assert repository.get_mission(killed.id).status == MissionStatus.KILLED


def test_database_initializes_required_entity_tables(tmp_path):
    conn = connect(tmp_path / "mission.sqlite3")
    initialize_database(conn)

    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    table_names = {row["name"] for row in rows}

    assert {
        "missions",
        "tasks",
        "evidence",
        "reviews",
        "risks",
        "capacity_logs",
        "commitments",
    }.issubset(table_names)

