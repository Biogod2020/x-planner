# Mission Control Hermes Agent Integration

This directory packages Mission Control for local Hermes Agent testing. It installs the existing `skills/mission-control/` skill and adds a Hermes MCP stdio server entry that starts this repository's local MCP server with `uv`.

It does not change Mission Core behavior and does not add product features.

## Recommended GitHub Install

For users installing from GitHub, use the bootstrap script from the repository:

```bash
curl -fsSL https://raw.githubusercontent.com/Biogod2020/x-planner/master/scripts/install_hermes_from_github.sh | bash
```

The bootstrap script clones or updates the repo at:

```text
~/.hermes/plugins/x-planner
```

Then it runs this directory's local installer. Keep that checkout in place because Hermes starts the MCP server from that path.

To install a specific ref:

```bash
curl -fsSL https://raw.githubusercontent.com/Biogod2020/x-planner/master/scripts/install_hermes_from_github.sh | bash -s -- --ref master
```

## Files

- `install_hermes.sh`: installs or updates the Hermes skill and `mcp_servers.mission_control`.
- `uninstall_hermes.sh`: removes only the Hermes skill and MCP server entry. It keeps SQLite state unless `--purge-data` is passed.
- `config-snippet.yaml`: the MCP config shape installed into `~/.hermes/config.yaml`.

## Local Checkout Install

Preview the install without changing your Hermes profile:

```bash
./integrations/hermes/install_hermes.sh --dry-run
```

Install:

```bash
./integrations/hermes/install_hermes.sh
```

The installer:

- verifies `hermes`, `uv`, and `python3` are on `PATH`;
- resolves this repo root as an absolute path;
- copies `skills/mission-control/` to `~/.hermes/skills/mission-control`;
- backs up `~/.hermes/config.yaml` before editing it;
- adds or updates only `mcp_servers.mission_control`;
- preserves unrelated Hermes config text.

This installer intentionally does not use `hermes mcp add`. Current Hermes CLI builds have rough edges for non-interactive local stdio installs:

- `--args` cannot reliably pass dash-prefixed arguments such as `-m`;
- repeated `--env` flags keep only the last group;
- successful discovery prompts for `Enable all tools?` without a `--yes` flag.

The direct config upsert avoids those issues while still using Hermes' normal MCP runtime.

The installed MCP entry is equivalent to:

```yaml
mcp_servers:
  mission_control:
    command: "bash"
    args:
      - "-lc"
      - "cd /absolute/path/to/x-planner && exec uv run python -m mcp_server.server"
    env:
      MISSION_CONTROL_DB: "~/.hermes/mission-control/mission-control.sqlite3"
```

## Verify Skill Install

Check the copied skill files:

```bash
ls ~/.hermes/skills/mission-control
sed -n '1,40p' ~/.hermes/skills/mission-control/SKILL.md
```

Then start Hermes:

```bash
hermes chat
```

Ask Hermes:

```text
Use the mission-control skill. Summarize its non-negotiables before taking action.
```

Expected result: Hermes references the Mission Control rules, including clarification before planning and no accepted evidence audit, no done.

## Verify MCP Tools

Start Hermes:

```bash
hermes chat
```

Ask Hermes:

```text
List the available mission_control MCP tools. Then call get_status_brief.
```

Expected result: Hermes can see tools such as `create_mission`, `save_mission_brief`, `create_task`, `submit_evidence`, `record_evidence_audit`, `update_task_status`, `run_review`, and `get_status_brief`.

The MCP server stores SQLite state at:

```text
~/.hermes/mission-control/mission-control.sqlite3
```

## Smoke Test

```bash
./integrations/hermes/install_hermes.sh
hermes chat
```

In Hermes, send:

```text
Use the mission-control skill. Help me plan a small repo hardening task. Follow clarify -> mission brief -> MCP save -> evidence-backed task -> accepted audit -> review.
```

Expected result: Hermes clarifies first, saves the mission brief through MCP, creates an evidence-backed task, refuses terminal task status until evidence has an accepted audit, and records a review.

## Uninstall

Preview:

```bash
./integrations/hermes/uninstall_hermes.sh --dry-run
```

Remove the skill and MCP config while keeping SQLite state:

```bash
./integrations/hermes/uninstall_hermes.sh
```

Remove the skill, MCP config, and SQLite state:

```bash
./integrations/hermes/uninstall_hermes.sh --purge-data
```
