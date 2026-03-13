#!/usr/bin/env sh
set -eu

export PATH="/workspace/tests/integration/docker/mock-bin:/root/.local/bin:${PATH}"
chmod +x /workspace/tests/integration/docker/mock-bin/npx
chmod +x /workspace/tests/integration/docker/mock-bin/npm
chmod +x /workspace/tests/integration/docker/mock-bin/codex
chmod +x /workspace/tests/integration/docker/mock-bin/claude
chmod +x /workspace/tests/integration/docker/mock-bin/pyright
chmod +x /workspace/tests/integration/docker/mock-bin/ruff

rm -f /tmp/skillsible-tool-calls.log

cd /workspace

rm -rf dist
uv build
wheel_path="$(find dist -maxdepth 1 -name 'skillsible-*.whl' | sort | tail -n 1)"
uv tool install --force "$wheel_path"

doctor_output="$(skillsible doctor)"
printf '%s\n' "$doctor_output"
printf '%s\n' "$doctor_output" | grep -F -- "- npx: found"

plan_output="$(skillsible plan -f /workspace/tests/integration/docker/integration.yml)"
printf '%s\n' "$plan_output"
printf '%s\n' "$plan_output" | grep -F -- "install writing-clearly-and-concisely for codex"
printf '%s\n' "$plan_output" | grep -F -- "tool pyright for codex [lsp] (npm=pyright, verify=pyright --version)"
printf '%s\n' "$plan_output" | grep -F -- "tool ruff for codex [cli] (uv=ruff, verify=ruff --version)"
printf '%s\n' "$plan_output" | grep -F -- "mcp github for codex (transport=stdio, command=github-mcp --serve)"

apply_output="$(skillsible apply -f /workspace/tests/integration/docker/integration.yml)"
printf '%s\n' "$apply_output"
printf '%s\n' "$apply_output" | grep -F -- '$ npx skills add /workspace/tests/integration/fixtures/demo-skills --skill writing-clearly-and-concisely --agent codex -y -g'
printf '%s\n' "$apply_output" | grep -F -- '$ npm install -g pyright'
printf '%s\n' "$apply_output" | grep -F -- '$ pyright --version'
printf '%s\n' "$apply_output" | grep -F -- '$ uv tool install ruff'
printf '%s\n' "$apply_output" | grep -F -- '$ ruff --version'
printf '%s\n' "$apply_output" | grep -F -- '$ codex mcp add github -- github-mcp --serve'

grep -F -- 'npx skills add /workspace/tests/integration/fixtures/demo-skills --skill writing-clearly-and-concisely --agent codex -y -g' /tmp/skillsible-tool-calls.log
grep -F -- 'npm install -g pyright' /tmp/skillsible-tool-calls.log
grep -F -- 'pyright --version' /tmp/skillsible-tool-calls.log
grep -F -- 'codex mcp add github -- github-mcp --serve' /tmp/skillsible-tool-calls.log
