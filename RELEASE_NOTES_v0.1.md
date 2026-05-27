# Release Notes v0.1

Mission Control Core v0.1 is a local-first database core, MCP server, and agent skill pack for evidence-backed mission execution. It is not a todo app, UI product, notification system, calendar integration, email integration, or cloud service.

## Implemented

- Python project managed with `uv`.
- SQLite database initialization for Mission, Task, Evidence, Review, Risk, CapacityLog, and Commitment entities.
- Pydantic typed models for core records and status enums.
- Deterministic repository and state-machine logic for task readiness, evidence-gated completion, failure escalation, daily mainline selection, and mission terminal review requirements.
- Local MCP server exposing the v0.1 tools, resources, and prompts documented in `MCP_TOOLS.md`.
- Mission-control skill pack in `skills/mission-control/` with workflow guidance and behavior test scenarios.
- Documentation for mission scope, schema, MCP surface, agent rules, and acceptance status.

## Verified

- `uv run pytest -q` passes with 28 tests.
- Ready tasks require `next_action`, `expected_output`, and `evidence_required`.
- Tasks cannot be completed or accepted before evidence exists.
- Evidence can be submitted and audited.
- Repeated failures increment `failure_count`; tasks require failure review at `failure_count >= 2`.
- Daily mainline selection is unique per day.
- Completed and killed missions require a review record.
- MCP tools are registered and cannot bypass the core evidence gate in the tested paths.
- MCP stdio smoke coverage demonstrates create mission, save brief, create task, reject premature completion, submit evidence, audit evidence, complete task, run review, and read status.

## Remains Unverified

- Compatibility with external MCP clients beyond the Python MCP stdio client used in tests.
- Long-running server lifecycle behavior under sustained use.
- Concurrent writes from multiple processes.
- Data migrations from earlier schema versions.
- Real-agent dogfood trials from `REAL_AGENT_TRIAL.md`; the protocol is defined but not executed in this release freeze.
- Out-of-scope product areas: web UI, mobile app, Telegram, email, calendar, notifications, multi-user authentication, cloud sync, full GitHub integration, and automatic scheduling.

## Run Tests

```bash
uv run pytest -q
```

## Start the MCP Server

```bash
uv run python -m mcp_server.server
```

Set `MISSION_CONTROL_DB=/path/to/mission.sqlite3` to choose the SQLite database file. If unset, the server uses `.mission-control.sqlite3` in the current directory.
