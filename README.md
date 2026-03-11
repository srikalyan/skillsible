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
  Shared machine tools such as LSPs or CLIs. These are parsed and shown in `plan`, but not installed yet.
- `mcps`
  MCP server definitions. These are parsed and shown in `plan`, but not installed yet.

This split is intentional. Skills are the cleanest cross-agent abstraction. Tools and MCPs vary more by agent and runtime, so `skillsible` tracks them explicitly without pretending parity that does not exist.

## Example

```yaml
version: 1  # Manifest format version

agents:
  - codex       # Default target agent
  - claude-code # Also receives any skill that does not override `agents`

defaults:
  scope: global # Default scope: install for the current user across projects

skills:
  - source: obra/the-elements-of-style
    skill: writing-clearly-and-concisely
    version: v1.2.0 # Pin this skill to a specific source revision, such as a tag
    # No `agents` field here, so this inherits both top-level agents:
    #   - codex
    #   - claude-code
    # No `scope` field here, so this inherits `defaults.scope = global`

  - source: https://github.com/obra/the-elements-of-style
    skill: writing-clearly-and-concisely
    version: main # A skill version can also be a branch, tag, or commit SHA
    agents:
      - codex   # Override: only install this one for codex
    scope: project # Override: install only for the current project

tools:
  - name: pyright
    kind: lsp
    package: pyright
    agents:
      - codex
      - claude-code

mcps:
  - name: github
    transport: stdio
    command: github-mcp
    agents:
      - claude-code
```

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

## Current Support

- `skills`
  Fully supported in `plan` and `apply`
- `tools`
  Supported in `plan`; `apply` reports them as not yet applied
- `mcps`
  Supported in `plan`; `apply` reports them as not yet applied

## CLI

```bash
uv run skillsible plan -f skills.yml
uv run skillsible apply -f skills.yml
uv run skillsible doctor
```

## Install

From PyPI:

```bash
uv tool install skillsible
skillsible doctor
```

For a specific version:

```bash
uv tool install skillsible==1.0.0
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
uv tool install dist/skillsible-1.0.0-py3-none-any.whl
skillsible doctor
```

## CI And Release

This repo includes GitHub Actions for:

- CI on pushes to `main` and pull requests
- building distributions with `uv build`
- publishing to PyPI when a tag like `v1.0.0` is pushed

### PyPI Trusted Publishing Setup

Before publishing will work, configure `skillsible` on PyPI to trust this repository's publish workflow:

- PyPI project: `skillsible`
- GitHub owner: `srikalyan`
- GitHub repository: `skillsible`
- Workflow file: `.github/workflows/publish.yml`
- Environment name: `pypi`

After that, pushing a tag such as `v1.0.0` will trigger the publish workflow.

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

- manifest validation
- agent adapters
- drift detection
- lockfile support
- export current installed skills
- lockfile support for exact resolved commits
- tool installers and bootstrap support
- MCP adapter support per agent

## Development

```bash
uv sync --dev
uv run pytest
uv run skillsible plan -f examples/skills.yml
```
