# Mission Control Core

Mission Control Core is a local-first SpaceX-style project management core for AI agents. It is not a todo app, web app, notification system, calendar integration, or cloud service.

The v0.1 product is:

1. A SQLite-backed Mission Core database and deterministic business logic.
2. A local MCP server exposing tools and read-only resources.
3. A mission-control skill pack that teaches external agents how to manage goals through Mission Briefs, evidence, reviews, and explicit decisions.

## Requirements

- Python 3.11+
- `uv`

## Setup

```bash
uv sync
```

## Run Tests

```bash
uv run pytest
```

## User Tutorial

See [PLANNER_TUTORIAL.md](PLANNER_TUTORIAL.md) for the end-to-end planner workflow, agent prompts, evidence rules, and live trial steps.

## Initialize a Local Database

```bash
uv run python -c "from mission_core.db import connect, initialize_database; c = connect('.mission-control.sqlite3'); initialize_database(c)"
```

## Start the MCP Server

```bash
uv run python -m mcp_server.server
```

Set `MISSION_CONTROL_DB=/path/to/mission.sqlite3` to choose a database file. If unset, the MCP server uses `.mission-control.sqlite3` in the current directory.

## Core Flow

Goal -> Mission -> Task -> Evidence -> Review -> Decision

A task cannot become ready unless `next_action`, `expected_output`, and `evidence_required` are present. A task cannot become completed or accepted unless it has an accepted evidence audit. Completed or killed missions require a review record.
