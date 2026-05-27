from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server import resources, tools
from mcp_server.prompts import FAILURE_REVIEW_PROMPT, MISSION_BRIEF_PROMPT

mcp = FastMCP("mission-control-core")


@mcp.tool()
def create_mission(title: str, objective: str | None = None) -> dict:
    return tools.create_mission(title=title, objective=objective)


@mcp.tool()
def save_mission_brief(mission_id: int, brief: str) -> dict:
    return tools.save_mission_brief(mission_id=mission_id, brief=brief)


@mcp.tool()
def list_missions(status: str | None = None) -> list[dict]:
    return tools.list_missions(status=status)


@mcp.tool()
def create_task(
    mission_id: int,
    title: str,
    next_action: str,
    expected_output: str,
    evidence_required: str,
) -> dict:
    return tools.create_task(
        mission_id=mission_id,
        title=title,
        next_action=next_action,
        expected_output=expected_output,
        evidence_required=evidence_required,
    )


@mcp.tool()
def list_tasks(mission_id: int | None = None, status: str | None = None) -> list[dict]:
    return tools.list_tasks(mission_id=mission_id, status=status)


@mcp.tool()
def select_today_mainline(task_id: int, day: str | None = None) -> dict:
    return tools.select_today_mainline(task_id=task_id, day=day)


@mcp.tool()
def submit_evidence(task_id: int, description: str, uri: str | None = None) -> dict:
    return tools.submit_evidence(task_id=task_id, description=description, uri=uri)


@mcp.tool()
def record_evidence_audit(evidence_id: int, audit_status: str, audit_notes: str | None = None) -> dict:
    return tools.record_evidence_audit(
        evidence_id=evidence_id,
        audit_status=audit_status,
        audit_notes=audit_notes,
    )


@mcp.tool()
def run_review(
    review_type: str,
    decision: str,
    notes: str,
    mission_id: int | None = None,
    task_id: int | None = None,
) -> dict:
    return tools.run_review(
        review_type=review_type,
        decision=decision,
        notes=notes,
        mission_id=mission_id,
        task_id=task_id,
    )


@mcp.tool()
def update_task_status(task_id: int, status: str) -> dict:
    return tools.update_task_status(task_id=task_id, status=status)


@mcp.tool()
def update_capacity_log(
    day: str | None = None,
    available_minutes: int = 0,
    energy_level: int = 3,
    notes: str | None = None,
) -> dict:
    return tools.update_capacity_log(
        day=day,
        available_minutes=available_minutes,
        energy_level=energy_level,
        notes=notes,
    )


@mcp.tool()
def get_status_brief(day: str | None = None) -> dict:
    return tools.get_status_brief(day=day)


@mcp.resource("mission://today")
def mission_today() -> str:
    return resources.get_status_brief_resource()


@mcp.resource("mission://missions/active")
def active_missions() -> str:
    return resources.get_active_missions_resource()


@mcp.resource("mission://mission/{id}")
def mission_by_id(id: int) -> str:
    return resources.get_mission_resource(id=id)


@mcp.resource("mission://capacity/recent")
def capacity_recent() -> str:
    return resources.get_capacity_recent_resource()


@mcp.resource("mission://review/due")
def review_due() -> str:
    return resources.get_review_due_resource()


@mcp.resource("mission://risks/open")
def risks_open() -> str:
    return resources.get_open_risks_resource()


@mcp.prompt()
def mission_brief_prompt() -> str:
    return MISSION_BRIEF_PROMPT


@mcp.prompt()
def failure_review_prompt() -> str:
    return FAILURE_REVIEW_PROMPT


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
