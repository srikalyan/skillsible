# Support Matrix

This matrix describes what `skillsible` supports today, grouped by manifest layer and agent.

## Layers

| Layer | `plan` | `apply` | `inspect` | Notes |
| --- | --- | --- | --- | --- |
| `skills` | Yes | Yes | Yes | Installed through `skills.sh`; per-skill `version` is resolved by `skillsible` before install. |
| `tools` | Yes | Yes | Partial | `apply` supports `install.uv_tool`, `install.npm`, and `binary` checks. `inspect` does not yet provide a dedicated aggregated tool inventory. |
| `mcps` | Yes | No | Partial | `inspect` can query existing Codex and Claude MCP state, but `skillsible apply` does not configure MCPs yet. |
| `lockfile` | N/A | No | N/A | `skillsible lock` writes `skillsible.lock` with resolved skill revisions and normalized snapshots, but `apply` does not consume it yet. |

## Agents

| Agent | Skills via `apply` | Skills via `inspect` | MCPs via `inspect` | Notes |
| --- | --- | --- | --- | --- |
| `codex` | Yes | Yes | Yes | Real-agent Docker validation confirms released Codex CLI can be installed and queried without auth. `skills.sh` currently lists Codex global skills with `Agents: not linked`. |
| `claude-code` | Yes | Yes | Yes | Real-agent Docker validation confirms released Claude Code CLI can be installed and queried without auth for plugin/MCP inventory surfaces. |

## Tool Backends

| Tool backend | `apply` | Notes |
| --- | --- | --- |
| `install.uv_tool` | Yes | Runs `uv tool install <package>`. |
| `install.npm` | Yes | Runs `npm install -g <package>`. |
| `binary` | Yes | Verifies the binary exists on `PATH`; does not install it. |

## Validation

| Command | Human output | JSON output |
| --- | --- | --- |
| `skillsible validate` | Yes | Yes |
| `skillsible lock` | Yes | Yes |
| `skillsible plan` | Yes | Yes |
| `skillsible inspect` | Yes | Yes |
| `skillsible doctor` | Yes | No |

## Current Gaps

- `mcps` are declarative only; no `apply` support yet.
- `skillsible.lock` is generated but not consumed yet.
- `tools` do not yet have a unified post-install inventory command.
- `doctor` does not yet expose JSON output.
