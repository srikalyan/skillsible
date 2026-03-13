#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

SKILL_REPO="$TMP_DIR/demo-skill-repo"
MANIFEST="$TMP_DIR/skills.yml"
LOCKFILE="$TMP_DIR/skillsible.lock"

mkdir -p "$SKILL_REPO"

git init -b main "$SKILL_REPO" >/dev/null
git -C "$SKILL_REPO" config user.name "Demo User"
git -C "$SKILL_REPO" config user.email "demo@example.com"
cat > "$SKILL_REPO/SKILL.md" <<'EOF'
# Writing Clearly And Concisely

Keep responses concrete, short, and easy to scan.
EOF
git -C "$SKILL_REPO" add SKILL.md
git -C "$SKILL_REPO" commit -m "Initial demo skill" >/dev/null

cat > "$MANIFEST" <<EOF
version: 1
agents:
  - codex
  - claude-code

skills:
  - source: $SKILL_REPO
    skill: writing-clearly-and-concisely

tools:
  - name: gh
    kind: cli
    binary: gh
EOF

run() {
  printf '\n$ %s\n' "$*"
  "$@"
}

cd "$ROOT_DIR"

run uv run skillsible validate -f "$MANIFEST"
run uv run skillsible lock -f "$MANIFEST" -o "$LOCKFILE"
run uv run skillsible diff -f "$MANIFEST" -l "$LOCKFILE"
run uv run skillsible plan -f "$MANIFEST" -l "$LOCKFILE"
run uv run skillsible apply --dry-run -f "$MANIFEST" -l "$LOCKFILE"
