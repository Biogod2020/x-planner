#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: install_hermes.sh [--dry-run]

Installs the Mission Control skill and MCP server config into Hermes Agent.

Options:
  --dry-run   Print planned changes without modifying ~/.hermes.
  -h, --help  Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"
HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes}"
CONFIG_PATH="${HERMES_CONFIG:-${HERMES_HOME}/config.yaml}"
SKILL_SOURCE="${REPO_ROOT}/skills/mission-control"
SKILL_PARENT="${HERMES_HOME}/skills"
SKILL_TARGET="${SKILL_PARENT}/mission-control"
DB_PATH="~/.hermes/mission-control/mission-control.sqlite3"
COMMAND_LINE="cd $(printf '%q' "${REPO_ROOT}") && exec uv run python -m mcp_server.server"

check_command() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    echo "Found ${name}: $(command -v "${name}")"
    return 0
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "DRY RUN: ${name} is not on PATH; a real install would fail before editing config." >&2
    return 0
  fi

  echo "${name} is required but was not found on PATH." >&2
  exit 1
}

backup_config() {
  local timestamp
  local backup_path
  local suffix

  timestamp="$(date +%Y%m%d%H%M%S)"
  backup_path="${CONFIG_PATH}.bak.${timestamp}"
  suffix=1

  while [[ -e "${backup_path}" ]]; do
    backup_path="${CONFIG_PATH}.bak.${timestamp}.${suffix}"
    suffix=$((suffix + 1))
  done

  cp "${CONFIG_PATH}" "${backup_path}"
  echo "Backed up existing Hermes config to ${backup_path}"
}

render_or_write_config() {
  local mode="$1"
  python3 - "${CONFIG_PATH}" "${COMMAND_LINE}" "${DB_PATH}" "${mode}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
command_line = sys.argv[2]
db_path = sys.argv[3]
mode = sys.argv[4]


def indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def is_top_level_key(line: str) -> bool:
    return bool(line.strip()) and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#")


def server_block(child_indent: int = 2) -> list[str]:
    base = " " * child_indent
    return [
        f"{base}mission_control:\n",
        f"{base}  command: {json.dumps('bash')}\n",
        f"{base}  args:\n",
        f"{base}    - {json.dumps('-lc')}\n",
        f"{base}    - {json.dumps(command_line)}\n",
        f"{base}  env:\n",
        f"{base}    MISSION_CONTROL_DB: {json.dumps(db_path)}\n",
    ]


def find_mcp_servers(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if re.match(r"^mcp_servers:\s*(?:\{\}\s*)?(?:#.*)?$", line):
            return index
    return None


def top_level_block_end(lines: list[str], start: int) -> int:
    for index in range(start + 1, len(lines)):
        if is_top_level_key(lines[index]):
            return index
    return len(lines)


def child_indent_for(lines: list[str], start: int, end: int) -> int:
    for line in lines[start + 1 : end]:
        if line.strip() and not line.lstrip().startswith("#"):
            width = indent_width(line)
            if width > 0:
                return width
    return 2


def find_server_block(lines: list[str], start: int, end: int, child_indent: int, server_name: str) -> tuple[int, int] | None:
    prefix = " " * child_indent + f"{server_name}:"
    for index in range(start + 1, end):
        if lines[index].startswith(prefix):
            remove_end = index + 1
            while remove_end < end:
                line = lines[remove_end]
                if line.strip() == "":
                    remove_end += 1
                    continue
                width = indent_width(line)
                if width <= child_indent and not line.lstrip().startswith("#"):
                    break
                remove_end += 1
            return index, remove_end
    return None


def remove_server_block(lines: list[str], start: int, end: int, child_indent: int, server_name: str) -> tuple[list[str], int]:
    existing = find_server_block(lines, start, end, child_indent, server_name)
    if existing is None:
        return lines, end
    remove_start, remove_end = existing
    removed = remove_end - remove_start
    return lines[:remove_start] + lines[remove_end:], end - removed


def upsert_config(existing: str) -> str:
    lines = existing.splitlines(keepends=True)
    if not lines:
        return "mcp_servers:\n" + "".join(server_block())

    mcp_index = find_mcp_servers(lines)
    if mcp_index is None:
        if lines[-1] and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        if any(line.strip() for line in lines):
            lines.append("\n")
        lines.append("mcp_servers:\n")
        lines.extend(server_block())
        return "".join(lines)

    if re.match(r"^mcp_servers:\s*\{\}\s*(?:#.*)?$", lines[mcp_index]):
        lines[mcp_index] = "mcp_servers:\n"

    block_end = top_level_block_end(lines, mcp_index)
    child_indent = child_indent_for(lines, mcp_index, block_end)

    # Remove legacy installs that used a hyphenated MCP server key. Hermes turns
    # both keys into similar tool prefixes, so keeping both creates duplicate
    # or confusing Mission Control toolsets after reinstall.
    lines, block_end = remove_server_block(lines, mcp_index, block_end, child_indent, "mission-control")
    existing_server = find_server_block(lines, mcp_index, block_end, child_indent, "mission_control")
    new_block = server_block(child_indent)

    if existing_server is not None:
        start, end = existing_server
        return "".join(lines[:start] + new_block + lines[end:])

    insert_at = mcp_index + 1
    return "".join(lines[:insert_at] + new_block + lines[insert_at:])


original = config_path.read_text() if config_path.exists() else ""
updated = upsert_config(original)

if mode == "dry-run":
    print(updated, end="")
else:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated)
PY
}

check_command "hermes"
check_command "uv"
check_command "python3"

if [[ ! -d "${SKILL_SOURCE}" ]]; then
  echo "Mission Control skill source does not exist: ${SKILL_SOURCE}" >&2
  exit 1
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  cat <<EOF
DRY RUN: would install Mission Control for Hermes Agent.

Repository root:
  ${REPO_ROOT}

Skill copy:
  ${SKILL_SOURCE}
  -> ${SKILL_TARGET}

Hermes config:
  ${CONFIG_PATH}

Config after install:
EOF
  render_or_write_config "dry-run"
  exit 0
fi

mkdir -p "${SKILL_PARENT}" "${HERMES_HOME}/mission-control"
rm -rf "${SKILL_TARGET}"
cp -R "${SKILL_SOURCE}" "${SKILL_TARGET}"

if [[ -f "${CONFIG_PATH}" ]]; then
  backup_config
fi

render_or_write_config "write"

cat <<EOF
Installed Mission Control Hermes integration.

Skill:
  ${SKILL_TARGET}

Config:
  ${CONFIG_PATH}

Verify in Hermes:
  hermes --help
  hermes chat

Then ask Hermes to use the mission-control skill and list mission_control MCP tools.
EOF
