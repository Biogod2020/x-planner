from mission_core.db import connect, initialize_database
from mission_core.repository import MissionControlRepository


def repo(tmp_path):
    conn = connect(tmp_path / "mission.sqlite3")
    initialize_database(conn)
    return MissionControlRepository(conn)


def test_saving_a_review(tmp_path):
    repository = repo(tmp_path)
    mission = repository.create_mission(title="Review mission")
    task = repository.create_task(
        mission_id=mission.id,
        title="Review task",
        next_action="Inspect evidence",
        expected_output="Decision recorded",
        evidence_required="Review notes",
    )

    review = repository.run_review(
        review_type="task",
        decision="split",
        notes="Task is too large; split into schema and server work.",
        mission_id=mission.id,
        task_id=task.id,
    )

    assert review.id is not None
    assert review.decision == "split"
    assert review.task_id == task.id
