#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${X_PLANNER_REPO_URL:-https://github.com/Biogod2020/x-planner.git}"
REF="${X_PLANNER_REF:-master}"
HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes}"
INSTALL_DIR="${X_PLANNER_INSTALL_DIR:-${HERMES_HOME}/plugins/x-planner}"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: install_hermes_from_github.sh [options]

Clone or update x-planner from GitHub, then install its Hermes integration.

Options:
  --repo-url URL     Git repository URL. Defaults to Biogod2020/x-planner.
  --ref REF          Branch, tag, or commit to install. Defaults to master.
  --install-dir DIR  Persistent checkout path. Defaults to ~/.hermes/plugins/x-planner.
  --dry-run          Print planned actions without changing files.
  -h, --help         Show this help.

Environment overrides:
  X_PLANNER_REPO_URL
  X_PLANNER_REF
  X_PLANNER_INSTALL_DIR
  HERMES_HOME
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url)
      REPO_URL="${2:?--repo-url requires a value}"
      shift
      ;;
    --ref)
      REF="${2:?--ref requires a value}"
      shift
      ;;
    --install-dir)
      INSTALL_DIR="${2:?--install-dir requires a value}"
      shift
      ;;
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

check_command() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    return 0
  fi

  echo "${name} is required but was not found on PATH." >&2
  exit 1
}

run() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

checkout_ref() {
  local ref="$1"

  run git -C "${INSTALL_DIR}" fetch --tags origin

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "DRY RUN: would check out ${ref} in ${INSTALL_DIR}"
    return 0
  fi

  if git -C "${INSTALL_DIR}" rev-parse --verify --quiet "origin/${ref}" >/dev/null; then
    if git -C "${INSTALL_DIR}" show-ref --verify --quiet "refs/heads/${ref}"; then
      git -C "${INSTALL_DIR}" checkout "${ref}"
    else
      git -C "${INSTALL_DIR}" checkout -B "${ref}" "origin/${ref}"
    fi
    git -C "${INSTALL_DIR}" pull --ff-only origin "${ref}"
    return 0
  fi

  git -C "${INSTALL_DIR}" checkout "${ref}"
}

check_command git
check_command bash

echo "Installing x-planner Hermes integration"
echo
echo "Repository:  ${REPO_URL}"
echo "Ref:         ${REF}"
echo "Checkout:    ${INSTALL_DIR}"
echo "Hermes home: ${HERMES_HOME}"
echo

if [[ -e "${INSTALL_DIR}" && ! -d "${INSTALL_DIR}/.git" ]]; then
  echo "Install directory exists but is not a git checkout: ${INSTALL_DIR}" >&2
  echo "Choose a different --install-dir or move the existing directory first." >&2
  exit 1
fi

if [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  run mkdir -p "$(dirname "${INSTALL_DIR}")"
  run git clone "${REPO_URL}" "${INSTALL_DIR}"
else
  run git -C "${INSTALL_DIR}" remote set-url origin "${REPO_URL}"
fi

checkout_ref "${REF}"

INSTALLER="${INSTALL_DIR}/integrations/hermes/install_hermes.sh"
if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "DRY RUN: would run ${INSTALLER}"
  exit 0
fi

if [[ ! -f "${INSTALLER}" ]]; then
  echo "Hermes installer not found after checkout: ${INSTALLER}" >&2
  exit 1
fi

chmod +x "${INSTALLER}"
"${INSTALLER}"

cat <<EOF

Next checks:
  hermes doctor
  hermes

Smoke-test prompt:
  Use the mission-control skill. Call get_status_brief, then explain the next required action.
EOF
