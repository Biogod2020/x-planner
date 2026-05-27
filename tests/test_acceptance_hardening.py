import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from mcp_server import tools
from mission_core.db import connect, initialize_database
from mission_core.models import MissionStatus
from mission_core.repository import MissionControlRepository


def repo(tmp_path):
    conn = connect(tmp_path / "mission.sqlite3")
    initialize_database(conn)
    return MissionControlRepository(conn)


def create_ready_task_via_tools(db_path, title="Acceptance task"):
    mission = tools.create_mission(
        title="Acceptance mission",
        objective="Validate Mission Control Core hardening",
        db_path=str(db_path),
    )
    task = tools.create_task(
        mission_id=mission["id"],
        title=title,
        next_action="Run independent acceptance test",
        expected_output="Acceptance evidence is recorded",
        evidence_required="pytest output from acceptance hardening test",
        db_path=str(db_path),
    )
    return mission, task


def parse_tool_result(result):
    assert result.content, "MCP tool result should include text content"
    return json.loads(result.content[0].text)


def test_mcp_tool_layer_enforces_evidence_gate(tmp_path):
    db_path = tmp_path / "mission.sqlite3"
    _mission, task = create_ready_task_via_tools(db_path)

    with pytest.raises(ValueError, match="evidence"):
        tools.update_task_status(task_id=task["id"], status="completed", db_path=str(db_path))

    evidence = tools.submit_evidence(
        task_id=task["id"],
        description="Acceptance test output proves the task result.",
        uri="file://pytest-output.txt",
        db_path=str(db_path),
    )
    audit = tools.record_evidence_audit(
        evidence_id=evidence["id"],
        audit_status="accepted",
        audit_notes="Evidence matches evidence_required.",
        db_path=str(db_path),
    )

    completed = tools.update_task_status(task_id=task["id"], status="completed", db_path=str(db_path))
    accepted = tools.update_task_status(task_id=task["id"], status="accepted", db_path=str(db_path))

    assert audit["audit_status"] == "accepted"
    assert completed["status"] == "completed"
    assert accepted["status"] == "accepted"


def test_mcp_tool_layer_rejects_ready_task_without_required_fields(tmp_path):
    db_path = tmp_path / "mission.sqlite3"
    mission = tools.create_mission(title="Task gate mission", db_path=str(db_path))

    for field, values in {
        "next_action": {"next_action": "", "expected_output": "output", "evidence_required": "evidence"},
        "expected_output": {"next_action": "action", "expected_output": "", "evidence_required": "evidence"},
        "evidence_required": {"next_action": "action", "expected_output": "output", "evidence_required": ""},
    }.items():
        with pytest.raises(ValueError, match=field):
            tools.create_task(
                mission_id=mission["id"],
                title=f"Missing {field}",
                db_path=str(db_path),
                **values,
            )


def test_status_transitions_and_failure_review_due_are_visible_from_status_brief(tmp_path):
    db_path = tmp_path / "mission.sqlite3"
    _mission, task = create_ready_task_via_tools(db_path)

    first_failure = tools.update_task_status(task_id=task["id"], status="failed", db_path=str(db_path))
    second_failure = tools.update_task_status(task_id=task["id"], status="failed", db_path=str(db_path))
    brief = tools.get_status_brief(day="2026-05-27", db_path=str(db_path))

    assert first_failure["failure_count"] == 1
    assert first_failure["requires_failure_review"] is False
    assert second_failure["failure_count"] == 2
    assert second_failure["requires_failure_review"] is True
    assert brief["review_due"] == [
        {
            "task_id": task["id"],
            "mission_id": task["mission_id"],
            "title": task["title"],
            "failure_count": 2,
        }
    ]


def test_daily_mainline_selection_is_unique_per_day_through_mcp_tools(tmp_path):
    db_path = tmp_path / "mission.sqlite3"
    mission = tools.create_mission(title="Mainline mission", db_path=str(db_path))
    first = tools.create_task(
        mission_id=mission["id"],
        title="First mainline",
        next_action="Do first",
        expected_output="First output",
        evidence_required="First evidence",
        db_path=str(db_path),
    )
    second = tools.create_task(
        mission_id=mission["id"],
        title="Second mainline",
        next_action="Do second",
        expected_output="Second output",
        evidence_required="Second evidence",
        db_path=str(db_path),
    )

    tools.select_today_mainline(first["id"], day="2026-05-27", db_path=str(db_path))
    selected = tools.select_today_mainline(second["id"], day="2026-05-27", db_path=str(db_path))
    tasks = tools.list_tasks(mission_id=mission["id"], db_path=str(db_path))

    by_id = {task["id"]: task for task in tasks}
    assert selected["id"] == second["id"]
    assert by_id[first["id"]]["today_mainline_on"] is None
    assert by_id[second["id"]]["today_mainline_on"] == "2026-05-27"


def test_terminal_mission_status_requires_review_record(tmp_path):
    repository = repo(tmp_path)
    completed = repository.create_mission(title="Terminal completed")
    killed = repository.create_mission(title="Terminal killed")

    with pytest.raises(ValueError, match="review"):
        repository.update_mission_status(completed.id, MissionStatus.COMPLETED)
    with pytest.raises(ValueError, match="review"):
        repository.update_mission_status(killed.id, MissionStatus.KILLED)

    completed_review = repository.run_review(
        review_type="mission",
        decision="completed",
        notes="Mission acceptance criteria met.",
        mission_id=completed.id,
    )
    killed_review = repository.run_review(
        review_type="mission",
        decision="killed",
        notes="Mission deliberately terminated after review.",
        mission_id=killed.id,
    )

    assert completed_review.id is not None
    assert killed_review.id is not None
    assert repository.get_mission(completed.id).status == MissionStatus.COMPLETED
    assert repository.get_mission(killed.id).status == MissionStatus.KILLED


def test_mcp_tool_schema_preserves_required_inputs_for_invariants():
    from mcp_server import server

    async def list_registered_tools():
        return {tool.name: tool for tool in await server.mcp.list_tools()}

    registered = asyncio.run(list_registered_tools())

    assert set(registered) == set(tools.TOOL_NAMES)
    assert set(registered["create_task"].inputSchema["required"]) == {
        "mission_id",
        "title",
        "next_action",
        "expected_output",
        "evidence_required",
    }
    assert set(registered["update_task_status"].inputSchema["required"]) == {"task_id", "status"}
    assert "update_mission_status" not in registered


def test_actual_mcp_stdio_server_demonstrates_mission_task_evidence_review_flow(tmp_path):
    async def scenario():
        env = os.environ.copy()
        env["MISSION_CONTROL_DB"] = str(tmp_path / "mcp-e2e.sqlite3")
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server.server"],
            cwd=Path.cwd(),
            env=env,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert {tool.name for tool in listed.tools} == set(tools.TOOL_NAMES)

                mission = parse_tool_result(
                    await session.call_tool(
                        "create_mission",
                        {
                            "title": "MCP E2E mission",
                            "objective": "Demonstrate mission/task/evidence/review over MCP stdio",
                        },
                    )
                )
                brief = parse_tool_result(
                    await session.call_tool(
                        "save_mission_brief",
                        {
                            "mission_id": mission["id"],
                            "brief": "Goal -> Mission -> Task -> Evidence -> Review -> Decision",
                        },
                    )
                )
                task = parse_tool_result(
                    await session.call_tool(
                        "create_task",
                        {
                            "mission_id": mission["id"],
                            "title": "E2E task",
                            "next_action": "Run MCP stdio smoke test",
                            "expected_output": "Smoke test records evidence and review",
                            "evidence_required": "MCP call_tool output",
                        },
                    )
                )

                rejected_completion = await session.call_tool(
                    "update_task_status",
                    {"task_id": task["id"], "status": "completed"},
                )
                assert rejected_completion.isError is True
                assert "evidence" in rejected_completion.content[0].text

                selected = parse_tool_result(
                    await session.call_tool(
                        "select_today_mainline",
                        {"task_id": task["id"], "day": "2026-05-27"},
                    )
                )
                evidence = parse_tool_result(
                    await session.call_tool(
                        "submit_evidence",
                        {
                            "task_id": task["id"],
                            "description": "MCP stdio smoke test produced call_tool output.",
                            "uri": "mcp://stdio-smoke",
                        },
                    )
                )
                audit = parse_tool_result(
                    await session.call_tool(
                        "record_evidence_audit",
                        {
                            "evidence_id": evidence["id"],
                            "audit_status": "accepted",
                            "audit_notes": "Evidence matches the expected MCP smoke result.",
                        },
                    )
                )
                completed = parse_tool_result(
                    await session.call_tool(
                        "update_task_status",
                        {"task_id": task["id"], "status": "completed"},
                    )
                )
                review = parse_tool_result(
                    await session.call_tool(
                        "run_review",
                        {
                            "review_type": "task",
                            "decision": "accepted",
                            "notes": "MCP stdio flow demonstrated mission/task/evidence/review.",
                            "mission_id": mission["id"],
                            "task_id": task["id"],
                        },
                    )
                )
                status = parse_tool_result(
                    await session.call_tool(
                        "get_status_brief",
                        {"day": "2026-05-27"},
                    )
                )

                return mission, brief, task, selected, evidence, audit, completed, review, status

    mission, brief, task, selected, evidence, audit, completed, review, status = asyncio.run(scenario())

    assert mission["title"] == "MCP E2E mission"
    assert brief["brief"].startswith("Goal -> Mission")
    assert selected["today_mainline_on"] == "2026-05-27"
    assert evidence["task_id"] == task["id"]
    assert audit["audit_status"] == "accepted"
    assert completed["status"] == "completed"
    assert review["decision"] == "accepted"
    assert status["today_mainline"]["task_id"] == task["id"]
