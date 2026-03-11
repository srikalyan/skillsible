# skillsible

Ansible-style skill management for Codex, Claude Code, and agent CLIs.

## What It Does

`skillsible` manages skills declaratively across machines and agents.

- define desired skills in a manifest
- target multiple agent CLIs
- preview changes with `plan`
- apply installs idempotently
- make workstation setup reproducible

## MVP

The initial version focuses on `skills.sh`-style installs driven by a YAML manifest.

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
    # No `agents` field here, so this inherits both top-level agents:
    #   - codex
    #   - claude-code
    # No `scope` field here, so this inherits `defaults.scope = global`

  - source: https://github.com/obra/the-elements-of-style
    skill: writing-clearly-and-concisely
    agents:
      - codex   # Override: only install this one for codex
    scope: project # Override: install only for the current project
```

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
uv tool install skillsible==0.2.0
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
uv tool install dist/skillsible-0.2.0-py3-none-any.whl
skillsible doctor
```

## CI And Release

This repo includes GitHub Actions for:

- CI on pushes to `main` and pull requests
- building distributions with `uv build`
- publishing to PyPI when a tag like `v0.2.0` is pushed

### PyPI Trusted Publishing Setup

Before publishing will work, configure `skillsible` on PyPI to trust this repository's publish workflow:

- PyPI project: `skillsible`
- GitHub owner: `srikalyan`
- GitHub repository: `skillsible`
- Workflow file: `.github/workflows/publish.yml`
- Environment name: `pypi`

After that, pushing a tag such as `v0.2.0` will trigger the publish workflow.

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
- version pinning by tag or commit

## Development

```bash
uv sync --dev
uv run pytest
uv run skillsible plan -f examples/skills.yml
```
