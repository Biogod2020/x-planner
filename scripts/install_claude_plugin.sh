#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="${ROOT_DIR}/plugins/mission-control"
MARKETPLACE_NAME="mission-control-core"
PLUGIN_REF="mission-control@${MARKETPLACE_NAME}"

if ! command -v claude >/dev/null 2>&1; then
  echo "claude CLI was not found on PATH." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv was not found on PATH." >&2
  exit 1
fi

if claude plugin validate --help >/dev/null 2>&1; then
  claude plugin validate "${ROOT_DIR}"
  claude plugin validate "${PLUGIN_DIR}"
fi

if claude plugin marketplace list --json 2>/dev/null | grep -q "\"name\"[[:space:]]*:[[:space:]]*\"${MARKETPLACE_NAME}\""; then
  claude plugin marketplace update "${MARKETPLACE_NAME}" || true
else
  claude plugin marketplace add "${ROOT_DIR}" --scope user
fi

claude plugin install "${PLUGIN_REF}" --scope user

cat <<EOF
Installed ${PLUGIN_REF}.

Open or reload Claude Code, then run:
  /reload-plugins
  /mcp

The mission-control MCP server should expose Mission Control tools.
EOF
