# AGENTS.md

## Project Identity

This repository implements Mission Control Core: a local-first SpaceX-style project management core for AI agents.

It is not a todo app, not a UI product, and not a notification system.

The product consists of:

1. Mission Core database and deterministic business logic.
2. MCP server exposing tools/resources/prompts.
3. Mission-control skill pack that teaches external agents how to manage goals using SpaceX-style execution principles.

## Non-Negotiable Principles

1. No evidence, no done.
2. Clarify before planning.
3. One daily mainline task.
4. Failure must escalate.
5. Database is the source of truth.
6. Skills guide behavior; MCP tools mutate state.
7. Do not build UI, notifications, email, calendar, or cloud sync in v0.1.

## Engineering Rules

- Prefer simple deterministic Python code over agentic complexity.
- Use SQLite for v0.1.
- Use typed models with Pydantic or SQLModel.
- Use pytest.
- Use `uv` for environment management, dependency installation, and test commands.
- Do not use `pip install --user`; add dependencies with `uv add` or `uv add --dev`.
- Keep business logic separate from MCP transport code.
- Every state transition should be explicit and testable.
- Do not silently mark tasks complete.
- Do not create a completed task without evidence.
- Do not introduce external service dependencies unless required for MCP itself.

## Required Structure

Use this root-level structure for v0.1:

mission_core/
  models.py
  db.py
  repository.py
  state_machine.py
  evidence.py
  review.py
  capacity.py

mcp_server/
  server.py
  tools.py
  resources.py
  prompts.py

skills/
  mission-control/
    SKILL.md
    examples.md

tests/
  test_missions.py
  test_tasks.py
  test_evidence.py
  test_reviews.py
  test_mcp_tools.py

README.md
MISSION.md
SCHEMA.md
MCP_TOOLS.md
AGENTS.md

## Definition of Done

A change is done only when:

- Tests pass.
- Core rules are enforced by tests.
- Documentation is updated.
- Scope has not expanded beyond v0.1.
- The implementation can be explained in terms of:
  Goal → Mission → Task → Evidence → Review → Decision.

## v0.1 Do Not Build

Do not build:

- web app
- mobile app
- Telegram bot
- email sending
- calendar sync
- notifications
- OAuth
- multi-user auth
- cloud sync
- automatic scheduling
- complex multi-agent orchestration
