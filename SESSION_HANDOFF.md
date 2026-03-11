# Session Handoff

## Project

- Name: `skillsible`
- GitHub repo: `git@github.com:srikalyan/skillsible.git`
- Goal: declarative multi-agent skill management across machines, similar in spirit to Ansible for skills

## Core Idea

Manage skills as code:

- define desired skills in a manifest
- target multiple agent CLIs such as Codex and Claude Code
- run `plan` before changes
- run `apply` to install
- keep machine setup reproducible

## Naming Decision

Chosen name: `skillsible`

Suggested positioning:

- repo: `skillsible`
- CLI: `skillsible`
- package: `skillsible`
- tagline: `Ansible-style skill management for Codex, Claude Code, and agent CLIs`

## User Preferences

Saved in [AGENTS.md](/home/srikalyan.swayampakula/workspaceGithub/skillsible/AGENTS.md):

- always use `uv` for Python environments, installs, and commands unless explicitly told otherwise
- for this repo, do not stop to ask for permission for non-privileged repo-local actions if the environment already allows them
- ask for permission for `sudo`, privileged system changes, or writes outside approved paths

Important limitation:

- repo instructions do not override the sandbox/harness
- to avoid prompts for normal repo work, start the next session with `/home/srikalyan.swayampakula/workspaceGithub/skillsible` or `/home/srikalyan.swayampakula/workspaceGithub` as a writable root

## Files Created

- [README.md](/home/srikalyan.swayampakula/workspaceGithub/skillsible/README.md)
- [pyproject.toml](/home/srikalyan.swayampakula/workspaceGithub/skillsible/pyproject.toml)
- [.gitignore](/home/srikalyan.swayampakula/workspaceGithub/skillsible/.gitignore)
- [AGENTS.md](/home/srikalyan.swayampakula/workspaceGithub/skillsible/AGENTS.md)
- [examples/skills.yml](/home/srikalyan.swayampakula/workspaceGithub/skillsible/examples/skills.yml)
- [src/skillsible/__init__.py](/home/srikalyan.swayampakula/workspaceGithub/skillsible/src/skillsible/__init__.py)
- [src/skillsible/manifest.py](/home/srikalyan.swayampakula/workspaceGithub/skillsible/src/skillsible/manifest.py)
- [src/skillsible/planner.py](/home/srikalyan.swayampakula/workspaceGithub/skillsible/src/skillsible/planner.py)
- [src/skillsible/cli.py](/home/srikalyan.swayampakula/workspaceGithub/skillsible/src/skillsible/cli.py)

## Current Status

The repo is now a working `uv`-managed Python package.

Implemented:

- package metadata in [pyproject.toml](/home/srikalyan.swayampakula/workspaceGithub/skillsible/pyproject.toml)
- `uv` workflow with [uv.lock](/home/srikalyan.swayampakula/workspaceGithub/skillsible/uv.lock)
- `.python-version` pinned to Python 3.11
- YAML manifest loading with validation
- install plan generation
- adapter boundary via [src/skillsible/adapters.py](/home/srikalyan.swayampakula/workspaceGithub/skillsible/src/skillsible/adapters.py)
- CLI commands:
  - `skillsible plan`
  - `skillsible apply`
  - `skillsible doctor`
- module execution via `uv run python -m skillsible ...`
- tests for manifest parsing, planning, and CLI
- built artifacts in `dist/` via `uv build`

Verified in this session:

- `uv sync --dev`
- `uv run pytest`
- `uv run skillsible plan -f examples/skills.yml`
- `uv run skillsible doctor`
- `uv run python -m skillsible doctor`
- `uv build`
- isolated wheel execution:
  - `uv run --no-project --with ./dist/skillsible-0.1.0-py3-none-any.whl skillsible doctor`

Still missing:

- idempotency and state tracking
- lockfile semantics for installed skills, not just Python deps
- richer adapter model per agent
- export/import of installed skills
- drift detection
- version pinning behavior in apply logic
- integration tests against a real `npx skills` invocation

## Important Conversation Context

The user asked:

- whether Claude-style skills and marketplaces are supported
- how to install a skill from `skills.sh`
- whether a Terraform/Ansible-like framework for cross-machine skill installation is a good idea
- to create a new project in the parent folder for that idea

Conclusions:

- a declarative multi-machine skills manager is worth building
- this should be closer to Ansible/Home Manager than Terraform
- a YAML manifest plus agent adapters is the right initial design
- `skillsible` is the chosen name

## Recommended Next Steps

1. Add real idempotency logic before apply
2. Introduce richer adapter support:
   - `skills.sh` backend first
   - later `codex`, `claude-code`, and filesystem-based adapters
3. Add export/import and drift detection
4. Add manifest schema validation beyond current basic checks
5. Commit and push to `git@github.com:srikalyan/skillsible.git`

## Suggested Resume Prompt

Use this in the next session:

```text
Continue building skillsible. Read AGENTS.md and SESSION_HANDOFF.md, use uv for everything Python-related, then finish the uv-based project setup, add tests, and move the CLI toward a real adapter-based MVP.
```
