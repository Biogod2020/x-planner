# Acceptance Report

Date: 2026-05-27

## Verification Command

```bash
uv run pytest -q
```

Result observed for v0.1.1: `33 passed`.

## Verified

- Python environment is managed with `uv`; `AGENTS.md` forbids `pip install --user`.
- SQLite database initialization is covered by tests and creates all v0.1 entity tables.
- Mission creation is covered through repository tests, MCP tool-layer tests, and MCP stdio smoke tests.
- Ready task creation requires `next_action`, `expected_output`, and `evidence_required`. This is verified through repository tests and independent MCP tool-layer tests.
- Task completion and acceptance cannot bypass the accepted-audit evidence gate. Evidence rows alone, pending audits, and rejected audits do not allow `completed` or `accepted` task status. This is verified through repository tests, MCP tool-layer tests, and the MCP stdio smoke test.
- Evidence can be submitted and audited with accepted/rejected status semantics. At least one `accepted` evidence audit is required before terminal task status.
- Repeated task failure increments `failure_count`; at `failure_count >= 2`, the task requires failure review and appears in `get_status_brief()["review_due"]`.
- Daily mainline selection is unique per day: selecting a second task for the same day clears the first selection.
- Mission terminal states `completed` and `killed` require a review record.
- MCP tool invariants are checked from the registered FastMCP tool schema: required `create_task` fields are exposed, `update_task_status` requires task/status inputs, and no direct `update_mission_status` MCP bypass is registered.
- The MCP server exposes the required tools and resources.
- A real MCP stdio flow is demonstrated in `tests/test_acceptance_hardening.py`: create mission, save Mission Brief, create task, reject completion without evidence, select daily mainline, submit evidence, audit evidence, complete task, run review, and read status brief.
- Skill behavior expectations are documented in `skills/mission-control/behavior_tests.md` with three prompt/expected-behavior scenarios.

## MCP Rule Bypass Check

The hardened tests verify that MCP tools call the core repository rules rather than bypassing them:

- `update_task_status(..., "completed")` returns structured MCP guidance with `ok: false`, `reason`, and `next_required_action` before an accepted evidence audit exists.
- `create_task` rejects missing `next_action`, `expected_output`, or `evidence_required` at the MCP tool layer.
- Terminal mission status changes are not exposed as a direct MCP tool; mission completion or kill decisions are recorded through `run_review`.

## Demonstrated Flow

The MCP stdio acceptance test demonstrates the core v0.1 chain:

Goal -> Mission -> Task -> Evidence -> Review -> Decision

The flow creates a mission and task through the MCP protocol, proves the accepted-audit evidence gate blocks premature completion, submits and audits evidence, completes the task after an accepted audit, records a review, and confirms the selected daily mainline in the status brief.

## Remains Unverified

- Compatibility with external MCP clients beyond the Python MCP stdio client used in tests.
- Long-running server lifecycle behavior under sustained use.
- Concurrent writes from multiple processes. v0.1 is local-first and does not implement multi-user coordination.
- Data migrations from earlier schema versions. v0.1 initializes the current schema only.
- The original `REAL_AGENT_TRIAL.md` dogfood protocol is documented; targeted real-agent verification and v0.1.1 follow-up are documented in `REAL_AGENT_TRIAL_REPORT.md`, while broader external-agent diversity remains unverified.
- Any web, mobile, notification, email, calendar, OAuth, cloud sync, full GitHub integration, or automatic scheduling behavior. These are explicitly out of scope for v0.1.

## v0.1.1 Hardening Implications

- The dogfood finding that evidence rows alone could satisfy terminal task status has been fixed.
- MCP state-changing tool responses now include `next_required_action` and `reason` for agent routing. Blocked `update_task_status` transitions return structured guidance instead of relying on transport-level failure.
- The mission-control skill now routes vague goals, evidence-free done requests, repeated failures, and multiple-goal prioritization separately.
- This hardening does not add UI, notifications, email, calendar, GitHub integration, scheduling, or other product features.
