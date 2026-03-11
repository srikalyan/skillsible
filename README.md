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
version: 1

agents:
  - codex
  - claude-code

defaults:
  scope: global

skills:
  - source: obra/the-elements-of-style
    skill: writing-clearly-and-concisely

  - source: https://github.com/obra/the-elements-of-style
    skill: writing-clearly-and-concisely
    agents:
      - codex
    scope: project
```

## CLI

```bash
uv run skillsible plan -f skills.yml
uv run skillsible apply -f skills.yml
uv run skillsible doctor
```

## Install

From a checkout:

```bash
uv tool install .
skillsible doctor
```

From a built wheel:

```bash
uv build
uv tool install dist/skillsible-0.1.0-py3-none-any.whl
skillsible doctor
```

## CI And Release

This repo includes GitHub Actions for:

- CI on pushes to `main` and pull requests
- building distributions with `uv build`
- publishing to PyPI when a tag like `v0.1.0` is pushed

### PyPI Trusted Publishing Setup

Before publishing will work, configure `skillsible` on PyPI to trust this repository's publish workflow:

- PyPI project: `skillsible`
- GitHub owner: `srikalyan`
- GitHub repository: `skillsible`
- Workflow file: `.github/workflows/publish.yml`
- Environment name: `pypi`

After that, pushing a tag such as `v0.1.0` will trigger the publish workflow.

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
