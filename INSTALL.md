# Mission Control Install

Mission Control can be installed into agent CLIs as a local skill plus MCP server. The core stays local: SQLite is the source of truth, and the MCP server runs from this checkout.

## Hermes Agent

Recommended one-line install from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/Biogod2020/x-planner/master/scripts/install_hermes_from_github.sh | bash
```

This clones or updates the repository at:

```text
~/.hermes/plugins/x-planner
```

Then it installs:

- the `mission-control` skill into `~/.hermes/skills/mission-control`;
- the `mission_control` MCP server entry into `~/.hermes/config.yaml`;
- local SQLite state at `~/.hermes/mission-control/mission-control.sqlite3`.

Manual install from an existing checkout:

```bash
./integrations/hermes/install_hermes.sh
```

Verify:

```bash
hermes doctor
hermes
```

Smoke-test prompt:

```text
Use the mission-control skill. Call get_status_brief, then explain the next required action.
```

The Hermes installer intentionally avoids `hermes mcp add` because current Hermes CLI builds have non-interactive stdio install rough edges around dash-prefixed `--args`, repeated `--env`, and tool-enable prompts.

## Claude Code Plugin

This plugin bundles:

- The `mission-control` skill at `skills/mission-control/SKILL.md`
- The local stdio MCP server at `mcp_server/server.py`
- Mission Core source used by that MCP server
- `.mcp.json` configured to store SQLite state in `${CLAUDE_PLUGIN_DATA}/mission-control.sqlite3`

Requirements:

- Claude Code with plugin support
- Python 3.11+
- `uv`

## Local Development Install

From the repository root:

```bash
./scripts/install_claude_plugin.sh
```

This validates the local marketplace and plugin when `claude plugin validate` is available, registers this repository as a local marketplace, and installs `mission-control@mission-control-core` at user scope.

For direct local testing without installing:

```bash
claude --plugin-dir ./plugins/mission-control
```

After installing or changing plugin files inside an active Claude Code session:

```text
/reload-plugins
```

## Marketplace Install

For a local marketplace checkout:

```bash
claude plugin marketplace add /path/to/x-planner
claude plugin install mission-control@mission-control-core
```

Inside Claude Code, the equivalent commands are:

```text
/plugin marketplace add /path/to/x-planner
/plugin install mission-control@mission-control-core
/reload-plugins
```

For a hosted Git marketplace, replace `/path/to/x-planner` with the GitHub shorthand or git URL that contains `.claude-plugin/marketplace.json` and `plugins/mission-control`.

## MCP Verification

Start or reload Claude Code, then run:

```text
/mcp
```

The `mission-control` MCP server should appear with tools such as:

- `create_mission`
- `save_mission_brief`
- `create_task`
- `submit_evidence`
- `record_evidence_audit`
- `update_task_status`
- `run_review`
- `get_status_brief`

The plugin MCP config starts the server with:

```text
uv run python -m mcp_server.server
```

Claude Code expands `${CLAUDE_PLUGIN_ROOT}` to the installed plugin directory and `${CLAUDE_PLUGIN_DATA}` to the plugin's persistent data directory.

## Uninstall

```bash
claude plugin uninstall mission-control@mission-control-core
```

If you registered the local marketplace only for development, remove it too:

```bash
claude plugin marketplace remove mission-control-core
```

The persistent SQLite database is stored under the plugin data directory managed by Claude Code. Remove that data manually only if you intentionally want to discard Mission Control state.
