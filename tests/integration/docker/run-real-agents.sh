#!/usr/bin/env sh
set -eu

cd /workspace

rm -rf dist
uv build
wheel_path="$(find dist -maxdepth 1 -name 'skillsible-*.whl' | sort | tail -n 1)"
uv tool install --force "$wheel_path"

npm install -g \
  "@openai/codex@${CODEX_VERSION}" \
  "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
  "skills@${SKILLS_VERSION}"

codex --version | grep -F -- "${CODEX_VERSION}"
claude --version | grep -F -- "${CLAUDE_VERSION}"
npx skills --version | grep -F -- "${SKILLS_VERSION}"

preinspect_output="$(skillsible inspect)"
printf '%s\n' "$preinspect_output"
printf '%s\n' "$preinspect_output" | grep -F -- '[codex]'
printf '%s\n' "$preinspect_output" | grep -F -- 'No global skills found.'
printf '%s\n' "$preinspect_output" | grep -F -- 'No MCP servers configured yet.'
printf '%s\n' "$preinspect_output" | grep -F -- '[claude-code]'
printf '%s\n' "$preinspect_output" | grep -F -- 'No plugins installed.'
printf '%s\n' "$preinspect_output" | grep -F -- 'No MCP servers configured.'

apply_output="$(skillsible apply -f /workspace/tests/integration/docker/real-agents.yml)"
printf '%s\n' "$apply_output"
printf '%s\n' "$apply_output" | grep -F -- '$ npx skills add /workspace/tests/integration/fixtures/demo-skills --skill writing-clearly-and-concisely --agent codex -y -g'
printf '%s\n' "$apply_output" | grep -F -- '$ npx skills add /workspace/tests/integration/fixtures/demo-skills --skill writing-clearly-and-concisely --agent claude-code -y -g'

postinspect_output="$(skillsible inspect)"
printf '%s\n' "$postinspect_output"
printf '%s\n' "$postinspect_output" | grep -F -- 'writing-clearly-and-concisely'
printf '%s\n' "$postinspect_output" | grep -F -- '$ claude plugins list'
printf '%s\n' "$postinspect_output" | grep -F -- 'No plugins installed.'

npx skills ls -g -a codex | grep -F -- 'writing-clearly-and-concisely'
npx skills ls -g -a claude-code | grep -F -- 'writing-clearly-and-concisely'
