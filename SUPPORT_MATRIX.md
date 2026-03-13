# Support Matrix

This matrix describes what `skillsible` supports today, grouped by manifest layer and agent.

## Layers

| Layer | `plan` | `apply` | `inspect` | Notes |
| --- | --- | --- | --- | --- |
| `skills` | Yes | Yes | Yes | Installed through `skills.sh`; per-skill `version` is resolved by `skillsible` before install. |
| `tools` | Yes | Yes | Partial | `apply` supports `source.uv`, `source.npm`, `source.go`, and `source.cargo`, then runs explicit verification commands. `inspect` does not yet provide a dedicated aggregated tool inventory. |
| `mcps` | Yes | Yes | Partial | `apply` supports stdio and URL-based MCPs for Codex and Claude Code. `inspect` queries current Codex and Claude MCP state. |
| `lockfile` | N/A | Partial | N/A | `skillsible lock` writes `skillsible.lock`; `plan`, `apply`, and `validate` can consume locked skill revisions via `-l/--lockfile`. |

## Agents

| Agent | Skills via `apply` | Skills via `inspect` | MCPs via `inspect` | Notes |
| --- | --- | --- | --- | --- |
| `codex` | Yes | Yes | Yes | Real-agent Docker validation confirms released Codex CLI can be installed and queried without auth. `skills.sh` currently lists Codex global skills with `Agents: not linked`. |
| `claude-code` | Yes | Yes | Yes | Real-agent Docker validation confirms released Claude Code CLI can be installed and queried without auth for plugin/MCP inventory surfaces. |

## MCP Backends

| MCP shape | `apply` | Notes |
| --- | --- | --- |
| `transport=stdio` | Yes | Supports `command`, `args`, and `env` for Codex and Claude Code. |
| `transport=http` | Yes | Supports `url` for Codex and Claude Code. |
| `transport=sse` | Yes | Passed through to Claude Code and treated as URL-based for Codex. |
| `headers` | Partial | Applied for Claude Code. Stored in manifests and lockfiles but ignored during Codex apply because the Codex CLI does not expose arbitrary header flags. |
| `bearer_token_env_var` | Yes | Passed directly to Codex and converted into an `Authorization` header for Claude Code at apply time. |

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

- Lockfile consumption currently applies only to skill revisions/source resolution.
- `tools` do not yet have a unified post-install inventory command.
- `doctor` does not yet expose JSON output.
