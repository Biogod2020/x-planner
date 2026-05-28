#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
PURGE_DATA=0

usage() {
  cat <<'EOF'
Usage: uninstall_hermes.sh [--dry-run] [--purge-data]

Removes the Mission Control Hermes skill and MCP server config.

Options:
  --dry-run     Print planned changes without modifying ~/.hermes.
  --purge-data  Also remove ~/.hermes/mission-control, including SQLite state.
  -h, --help    Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --purge-data)
      PURGE_DATA=1
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

HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes}"
CONFIG_PATH="${HERMES_CONFIG:-${HERMES_HOME}/config.yaml}"
SKILL_TARGET="${HERMES_HOME}/skills/mission-control"
DATA_DIR="${HERMES_HOME}/mission-control"

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

remove_config_entry() {
  local mode="$1"
  python3 - "${CONFIG_PATH}" "${mode}" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
mode = sys.argv[2]


def indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def is_top_level_key(line: str) -> bool:
    return bool(line.strip()) and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#")


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


def remove_server_block(lines: list[str], mcp_index: int, block_end: int, child_indent: int, server_name: str) -> tuple[list[str], int]:
    prefix = " " * child_indent + f"{server_name}:"
    for index in range(mcp_index + 1, block_end):
        if lines[index].startswith(prefix):
            remove_end = index + 1
            while remove_end < block_end:
                line = lines[remove_end]
                if line.strip() == "":
                    remove_end += 1
                    continue
                width = indent_width(line)
                if width <= child_indent and not line.lstrip().startswith("#"):
                    break
                remove_end += 1
            removed = remove_end - index
            return lines[:index] + lines[remove_end:], block_end - removed
    return lines, block_end


def remove_mission_control(existing: str) -> str:
    lines = existing.splitlines(keepends=True)
    mcp_index = find_mcp_servers(lines)
    if mcp_index is None:
        return existing

    block_end = top_level_block_end(lines, mcp_index)
    child_indent = child_indent_for(lines, mcp_index, block_end)

    for server_name in ("mission_control", "mission-control"):
        lines, block_end = remove_server_block(lines, mcp_index, block_end, child_indent, server_name)

    return "".join(lines)


original = config_path.read_text() if config_path.exists() else ""
updated = remove_mission_control(original)

if mode == "dry-run":
    print(updated, end="")
elif config_path.exists():
    config_path.write_text(updated)
PY
}

if [[ "${DRY_RUN}" -eq 1 ]]; then
  cat <<EOF
DRY RUN: would uninstall Mission Control from Hermes Agent.

Would remove skill:
  ${SKILL_TARGET}

Would remove mcp_servers.mission_control and legacy mcp_servers.mission-control from:
  ${CONFIG_PATH}

EOF
  if [[ "${PURGE_DATA}" -eq 1 ]]; then
    echo "Would remove data directory:"
    echo "  ${DATA_DIR}"
  else
    echo "Would keep data directory:"
    echo "  ${DATA_DIR}"
  fi
  echo
  echo "Config after uninstall:"
  remove_config_entry "dry-run"
  exit 0
fi

rm -rf "${SKILL_TARGET}"

if [[ -f "${CONFIG_PATH}" ]]; then
  backup_config
  remove_config_entry "write"
fi

if [[ "${PURGE_DATA}" -eq 1 ]]; then
  rm -rf "${DATA_DIR}"
  echo "Removed Hermes Mission Control data directory: ${DATA_DIR}"
else
  echo "Kept Hermes Mission Control data directory: ${DATA_DIR}"
fi

echo "Removed Mission Control Hermes integration."
