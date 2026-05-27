from mission_core.db import connect, initialize_database
from mission_core.repository import MissionControlRepository
from mcp_server.resources import RESOURCE_URIS, get_status_brief_resource
from mcp_server.tools import TOOL_NAMES


def repo(tmp_path):
    conn = connect(tmp_path / "mission.sqlite3")
    initialize_database(conn)
    return MissionControlRepository(conn)


def test_mcp_server_exposes_required_tools():
    assert set(TOOL_NAMES) == {
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
    }


def test_mcp_server_exposes_required_resources():
    assert set(RESOURCE_URIS) == {
        "mission://today",
        "mission://missions/active",
        "mission://mission/{id}",
        "mission://capacity/recent",
        "mission://review/due",
        "mission://risks/open",
    }


def test_get_status_brief_output(tmp_path):
    repository = repo(tmp_path)
    mission = repository.create_mission(title="Status mission")
    task = repository.create_task(
        mission_id=mission.id,
        title="Mainline",
        next_action="Build core",
        expected_output="Core passes tests",
        evidence_required="pytest output",
    )
    repository.select_today_mainline(task.id, day="2026-05-27")

    brief = repository.get_status_brief(day="2026-05-27")

    assert brief["today_mainline"]["task_id"] == task.id
    assert brief["active_missions"][0]["mission_id"] == mission.id
    assert brief["review_due"] == []


def test_get_status_brief_resource_returns_json(tmp_path):
    db_path = tmp_path / "mission.sqlite3"
    repository = repo(tmp_path)
    mission = repository.create_mission(title="Resource mission")
    repository.create_task(
        mission_id=mission.id,
        title="Resource task",
        next_action="Call resource",
        expected_output="JSON status",
        evidence_required="Resource test assertion",
    )

    payload = get_status_brief_resource(db_path=str(db_path), day="2026-05-27")

    assert "Resource mission" in payload

def test_fastmcp_server_registers_required_tools_and_resources():
    import asyncio

    from mcp_server import server

    async def inspect_server():
        tools = await server.mcp.list_tools()
        resources = await server.mcp.list_resources()
        templates = await server.mcp.list_resource_templates()
        return (
            {tool.name for tool in tools},
            {str(resource.uri) for resource in resources},
            {str(template.uriTemplate) for template in templates},
        )

    tool_names, resource_uris, resource_templates = asyncio.run(inspect_server())

    assert tool_names == set(TOOL_NAMES)
    assert resource_uris | resource_templates == set(RESOURCE_URIS)

