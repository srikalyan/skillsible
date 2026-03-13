# skillsible

Ansible-style skill management for Codex, Claude Code, and agent CLIs.

## What It Does

`skillsible` manages agent setup declaratively across machines and agents.

- define desired skills, tools, and MCPs in a manifest
- target multiple agent CLIs
- preview changes with `plan`
- apply supported installs idempotently
- make workstation setup reproducible

## MVP

The current version has three manifest layers:

- `skills`
  Portable `SKILL.md`-style agent skills. This is the most mature layer and the one `apply` supports today.
- `tools`
  Shared machine tools such as LSPs or CLIs. These are parsed and shown in `plan`, and selected installers are supported in `apply`.
- `mcps`
  MCP server definitions. These are parsed and shown in `plan`, but not installed yet.

This split is intentional. Skills are the cleanest cross-agent abstraction. Tools and MCPs vary more by agent and runtime, so `skillsible` tracks them explicitly without pretending parity that does not exist.

## Complete Schema Example

```yaml
version: 1  # Manifest format version

agents:
  - codex       # Default target agent
  - claude-code # Also receives any skill that does not override `agents`

defaults:
  scope: global # Default scope: install for the current user across projects

skills:
  - source: obra/the-elements-of-style
    skill: writing-clearly-and-concisely # Required: skill directory name
    version: v1.2.0 # Optional: branch, tag, or commit SHA
    # No `agents` field here, so this inherits both top-level agents:
    #   - codex
    #   - claude-code
    # No `scope` field here, so this inherits `defaults.scope = global`

  - source: obra/the-elements-of-style
    skill: writing-clearly-and-concisely
    version: main # A skill version can be a branch, tag, or commit SHA
    agents:
      - codex # Optional override: target only codex
    scope: project # Optional override: install only for the current project

tools:
  - name: pyright
    kind: lsp # Required: free-form category like lsp or cli
    package: pyright # Optional: descriptive package name
    install:
      npm: pyright # Optional: install via npm install -g
    agents:
      - codex
      - claude-code

  - name: gh
    kind: cli
    binary: gh # Optional: expected binary name on PATH

  - name: ruff
    kind: cli
    install:
      uv_tool: ruff # Optional: install via uv tool install

mcps:
  - name: github
    transport: stdio # Optional: transport hint such as stdio or http
    command: github-mcp # Optional: command to run for stdio-based MCPs
    agents:
      - claude-code

  - name: linear
    transport: http
    url: http://localhost:8765/mcp # Optional: server URL for HTTP MCPs
```

## Schema Reference

Top-level `version` and per-skill `version` mean different things:

- top-level `version`
  The manifest schema version. This tells `skillsible` how to interpret the playbook itself.

- per-skill `version`
  The source revision to install for that skill. This is used for reproducibility and can be:
  - a semantic tag like `v1.2.0`
  - a git tag like `release-2026-03`
  - a branch like `main`
  - a commit SHA like `8c1f2d4`

When a per-skill `version` is set, `skillsible` resolves that source to a concrete git checkout before
calling `npx skills add ...`. This keeps `apply` reproducible even though `skills.sh` does not expose its
own documented `--ref` flag.

Recommended usage:

- use a branch for moving development targets
- use a tag for readable pinned versions
- use a commit SHA for exact replayability

### Top-level fields

- `version`
  Required. Manifest schema version. Current value: `1`.
- `agents`
  Required. Default target agents used by `skills`, `tools`, and `mcps` when an item does not define its own `agents`.
- `defaults`
  Optional. Currently only `defaults.scope` is supported.

### `skills`

Each `skills` entry supports:

- `source`
  Required. GitHub shorthand, GitHub URL, git URL, or local path containing the skill.
  Preferred GitHub form: `owner/repo` instead of `https://github.com/owner/repo`.
- `skill`
  Required. Skill directory name to install from that source.
- `agents`
  Optional. Overrides top-level `agents` for this skill only.
- `scope`
  Optional. `global` or `project`. Defaults to `defaults.scope` or `global`.
- `version`
  Optional. Branch, tag, or commit SHA. When set, `apply` resolves the source to that exact revision before installation.

### `tools`

Each `tools` entry supports:

- `name`
  Required. Human-readable tool name.
- `kind`
  Required. Free-form category such as `lsp` or `cli`.
- `agents`
  Optional. Overrides top-level `agents` for this tool only.
- `package`
  Optional. Descriptive package name.
- `binary`
  Optional. Expected binary name on `PATH`.
- `install`
  Optional. Explicit installer backend. Supported forms today:
  - `uv_tool: <package>`
  - `npm: <package>`

Tool behavior in `apply`:

- `install.uv_tool`
  Runs `uv tool install <package>`
- `install.npm`
  Runs `npm install -g <package>`
- `binary` without `install`
  Verifies the binary is present on `PATH`

### `mcps`

Each `mcps` entry supports:

- `name`
  Required. MCP server name.
- `agents`
  Optional. Overrides top-level `agents` for this MCP only.
- `transport`
  Optional. Transport hint such as `stdio` or `http`.
- `command`
  Optional. Command used to launch the MCP server.
- `url`
  Optional. URL for an already-running MCP server.

`mcps` are currently planning metadata only. They are parsed and shown in `plan`, but `apply` does not configure or install them yet.

## Current Support

- `skills`
  Fully supported in `plan` and `apply`
- `tools`
  Supported in `plan` and `apply` for `uv_tool`, `npm`, and binary verification
- `mcps`
  Supported in `plan`; `apply` reports them as not yet applied

## Example Patterns

Some repos can participate in more than one layer.

For example, `googleworkspace/cli` can already be used directly as a `skills` source:

```yaml
version: 1

agents:
  - codex
  - claude-code

skills:
  - source: googleworkspace/cli
    skill: gws-drive
```

That is the minimal setup.

If you also want the CLI binary installed and an MCP endpoint tracked, use the fuller layered version shown in [google-workspace.yml](/home/srikalyan.swayampakula/workspaceGithub/skillsible/examples/google-workspace.yml).

## CLI

```bash
uv run skillsible validate -f skills.yml
uv run skillsible lock -f skills.yml
uv run skillsible diff -f skills.yml -l skillsible.lock
uv run skillsible plan -f skills.yml
uv run skillsible plan -f skills.yml -l skillsible.lock
uv run skillsible apply -f skills.yml
uv run skillsible apply -f skills.yml -l skillsible.lock
uv run skillsible doctor
uv run skillsible inspect
```

Machine-readable output is available for validation and inspection workflows:

```bash
uv run skillsible validate --json -f skills.yml
uv run skillsible lock --json -f skills.yml
uv run skillsible diff --json -f skills.yml -l skillsible.lock
uv run skillsible plan --json -f skills.yml
uv run skillsible inspect --json
```

`skillsible lock` writes a normalized `skillsible.lock` file with:

- the source manifest path
- the current `skillsible` version
- resolved skill revisions when the source can be resolved through git
- normalized snapshots of `tools` and `mcps`

This is groundwork for reproducibility. The lockfile is generated today, but `apply` does not yet
consume every field. Current lockfile support includes:

- `plan -l skillsible.lock`
- `apply -l skillsible.lock`
- `validate -l skillsible.lock`
- `diff -l skillsible.lock`

When a lockfile is applied, `skillsible` prefers the locked skill revision and resolved source when
present.

`inspect` is the current post-install verification command for supported agents. It queries real
local CLIs instead of guessing from manifest state:

- `npx skills ls ...` for Codex and Claude skill discovery
- `codex mcp list` for Codex MCP discovery
- `claude plugins list` and `claude mcp list` for Claude discovery

This is stronger than a dry-run or command log because it asks the agent surfaces what they
currently see after installation. It still has a support boundary:

- `skills`
  Verified through `skills.sh` discovery
- `tools`
  Verified separately through their installed binaries
- `mcps`
  Only inspectable once a future `apply` implementation configures them
- `lockfile`
  Generated by `skillsible lock`; consumed for skill planning/apply via `-l/--lockfile`

See [SUPPORT_MATRIX.md](/home/srikalyan.swayampakula/workspaceGithub/skillsible/SUPPORT_MATRIX.md) for the explicit feature-by-feature support table.

## Install

From PyPI:

```bash
uv tool install skillsible
skillsible doctor
```

For a specific version:

```bash
uv tool install skillsible==1.1.0
skillsible doctor
```

From a checkout:

```bash
uv tool install .
skillsible doctor
```

From a built wheel:

```bash
uv build
uv tool install dist/skillsible-1.1.0-py3-none-any.whl
skillsible doctor
```

## CI And Release

This repo includes GitHub Actions for:

- CI on pushes to `main` and pull requests
- building distributions with `uv build`
- publishing to PyPI when a tag like `v1.1.0` is pushed

### PyPI Trusted Publishing Setup

Before publishing will work, configure `skillsible` on PyPI to trust this repository's publish workflow:

- PyPI project: `skillsible`
- GitHub owner: `srikalyan`
- GitHub repository: `skillsible`
- Workflow file: `.github/workflows/publish.yml`
- Environment name: `pypi`

After that, pushing a tag such as `v1.1.0` will trigger the publish workflow.

## Workflow

The default branch is `main` and it is protected.

Expected flow:

1. Create a feature branch.
2. Open a pull request to `main`.
3. Let CI pass.
4. Merge to `main`.
5. Tag the merge commit with `vX.Y.Z`.
6. Push the tag to publish to PyPI.

See [CONTRIBUTING.md](/home/srikalyan.swayampakula/workspaceGithub/skillsible/CONTRIBUTING.md) for the release workflow in more detail.

## Design Goals

- declarative desired state
- multi-agent support
- idempotent operations
- portable across machines
- extensible adapter model

## Near-Term Roadmap

- agent adapters
- drift detection
- lockfile support
- export current installed skills
- lockfile consumption for exact resolved commits
- tool installers and bootstrap support
- MCP adapter support per agent

## Development

```bash
uv sync --dev
uv run pytest
uv run skillsible validate -f examples/stack.yml
uv run skillsible plan -f examples/skills.yml
```

## Docker Integration

Run the containerized integration test locally with:

```bash
docker build -t skillsible-integration -f tests/integration/docker/Dockerfile .
docker run --rm skillsible-integration
```

There is also a slower real-agent integration path that installs released Codex and Claude CLIs
inside Docker and checks their non-interactive discovery surfaces without auth:

```bash
docker build -t skillsible-real-agents -f tests/integration/docker/Dockerfile.real-agents .
docker run --rm skillsible-real-agents
```

This second path validates:

- pinned released CLIs for Codex, Claude, and `skills`
- `skillsible inspect` against real agent binaries
- global skill discovery for `codex` and `claude-code` after `skillsible apply`

It does not validate authenticated Claude features or interactive agent behavior. It is meant to
prove that released CLIs can be installed and that their non-auth discovery surfaces work in a
clean container.

This path builds the wheel inside Docker, installs `skillsible` as a real tool, and exercises `doctor`, `plan`, and `apply` against a fixture manifest.
