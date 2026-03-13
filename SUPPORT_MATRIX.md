# Support Matrix

This matrix describes what `skillsible` supports today, grouped by manifest layer and agent.

## Layers

| Layer | `plan` | `apply` | `inspect` | Notes |
| --- | --- | --- | --- | --- |
| `skills` | Yes | Yes | Yes | Installed through `skills.sh`; per-skill `version` is resolved by `skillsible` before install. |
| `tools` | Yes | Yes | Partial | `apply` supports `source.uv`, `source.npm`, `source.go`, and `source.cargo`, then runs explicit verification commands. `inspect` does not yet provide a dedicated aggregated tool inventory. |
| `mcps` | Yes | No | Partial | `inspect` can query existing Codex and Claude MCP state, but `skillsible apply` does not configure MCPs yet. |
| `lockfile` | N/A | Partial | N/A | `skillsible lock` writes `skillsible.lock`; `plan`, `apply`, and `validate` can consume locked skill revisions via `-l/--lockfile`. |

## Agents

| Agent | Skills via `apply` | Skills via `inspect` | MCPs via `inspect` | Notes |
| --- | --- | --- | --- | --- |
| `codex` | Yes | Yes | Yes | Real-agent Docker validation confirms released Codex CLI can be installed and queried without auth. `skills.sh` currently lists Codex global skills with `Agents: not linked`. |
| `claude-code` | Yes | Yes | Yes | Real-agent Docker validation confirms released Claude Code CLI can be installed and queried without auth for plugin/MCP inventory surfaces. |

## Tool Backends

| Tool backend | `apply` | Notes |
| --- | --- | --- |
| `source.uv` | Yes | Runs `uv tool install <package>` and then the configured verification command. |
| `source.npm` | Yes | Runs `npm install -g <package>` and then the configured verification command. |
| `source.go` | Yes | Runs `go install <package>@<version-or-latest>` and then the configured verification command. |
| `source.cargo` | Yes | Runs `cargo install <package>` with optional `--version`, then the configured verification command. |

## Validation

| Command | Human output | JSON output |
| --- | --- | --- |
| `skillsible validate` | Yes | Yes |
| `skillsible lock` | Yes | Yes |
| `skillsible diff` | Yes | Yes |
| `skillsible plan` | Yes | Yes |
| `skillsible inspect` | Yes | Yes |
| `skillsible doctor` | Yes | No |

## Current Gaps

- `mcps` are declarative only; no `apply` support yet.
- Lockfile consumption currently applies only to skill revisions/source resolution.
- `tools` do not yet have a unified post-install inventory command.
- `doctor` does not yet expose JSON output.
