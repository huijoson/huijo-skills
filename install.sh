#!/usr/bin/env bash
# Install the skills in this repo into the skills directory of every agent
# detected on this machine. Personal (home directory) scope only.
#
#   ./install.sh              install into every detected agent
#   ./install.sh --list       show what would be installed, change nothing
#   ./install.sh claude-code  install into one specific agent
#
# Agent skills are an open standard, so a plain directory copy is enough for
# any conforming agent. `gh skill install` is an alternative that also handles
# agents not listed here.

set -euo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# agent id -> personal skills directory
AGENT_IDS=(codex claude-code github-copilot kiro-cli antigravity)
AGENT_DIRS=("$HOME/.codex/skills" "$HOME/.claude/skills" "$HOME/.copilot/skills" "$HOME/.kiro/skills" "$HOME/.gemini/config/skills")

# A directory containing SKILL.md is a skill.
find_skills() {
  local skill
  for skill in "$REPO_DIR"/*/; do
    [ -f "${skill}SKILL.md" ] && printf '%s\n' "${skill%/}"
  done
}

dir_for_agent() {
  local want=$1 i
  for i in "${!AGENT_IDS[@]}"; do
    if [ "${AGENT_IDS[$i]}" = "$want" ]; then
      printf '%s\n' "${AGENT_DIRS[$i]}"
      return 0
    fi
  done
  return 1
}

# An agent counts as present if its config root exists, so skills can be
# installed before the agent has created a skills directory of its own.
agent_present() {
  local dir="$1"
  [ -d "$(dirname -- "$dir")" ] || { [ "$dir" = "$HOME/.gemini/config/skills" ] && [ -d "$HOME/.gemini" ]; }
}

list_only=0
requested=()

for arg in "$@"; do
  case "$arg" in
    --list|-l) list_only=1 ;;
    -h|--help) sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) printf 'unknown option: %s\n' "$arg" >&2; exit 2 ;;
    *)
      if ! dir_for_agent "$arg" >/dev/null; then
        printf 'unknown agent: %s (known: %s)\n' "$arg" "${AGENT_IDS[*]}" >&2
        exit 2
      fi
      requested+=("$arg")
      ;;
  esac
done

mapfile -t skills < <(find_skills)
if [ "${#skills[@]}" -eq 0 ]; then
  printf 'no skills found in %s\n' "$REPO_DIR" >&2
  exit 1
fi

targets=("${requested[@]:-${AGENT_IDS[@]}}")
installed=0

for agent in "${targets[@]}"; do
  dest="$(dir_for_agent "$agent")"

  # An explicitly requested agent is installed even if not detected.
  if [ "${#requested[@]}" -eq 0 ] && ! agent_present "$dest"; then
    printf 'skip  %-16s (not detected)\n' "$agent"
    continue
  fi

  for skill in "${skills[@]}"; do
    name="$(basename -- "$skill")"
    if [ "$list_only" -eq 1 ]; then
      printf 'would install %-20s -> %s/%s\n' "$name" "$dest" "$name"
      continue
    fi
    mkdir -p "$dest"
    rm -rf -- "$dest/$name"
    cp -R -- "$skill" "$dest/$name"
    printf 'ok    %-16s %-20s -> %s/%s\n' "$agent" "$name" "$dest" "$name"
  done
  installed=1
done

if [ "$installed" -eq 0 ] && [ "$list_only" -eq 0 ]; then
  printf '\nNo agents detected. Pass an agent explicitly, e.g. ./install.sh claude-code\n' >&2
  exit 1
fi
