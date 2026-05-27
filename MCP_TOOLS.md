# MCP Tools and Resources

The local MCP server starts with:

```bash
uv run python -m mcp_server.server
```

Set `MISSION_CONTROL_DB` to choose the SQLite database path.

## Tools

- `create_mission(title, objective=None)`
- `save_mission_brief(mission_id, brief)`
- `list_missions(status=None)`
- `create_task(mission_id, title, next_action, expected_output, evidence_required)`
- `list_tasks(mission_id=None, status=None)`
- `select_today_mainline(task_id, day=None)`
- `submit_evidence(task_id, description, uri=None)`
- `record_evidence_audit(evidence_id, audit_status, audit_notes=None)`
- `run_review(review_type, decision, notes, mission_id=None, task_id=None)`
- `update_task_status(task_id, status)`
- `update_capacity_log(day=None, available_minutes=0, energy_level=3, notes=None)`
- `get_status_brief(day=None)`

## Resources

- `mission://today`
- `mission://missions/active`
- `mission://mission/{id}`
- `mission://capacity/recent`
- `mission://review/due`
- `mission://risks/open`

## Prompts

- `mission_brief_prompt`
- `failure_review_prompt`
