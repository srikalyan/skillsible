# AGENTS.md

## Repo Preferences

- Always use `uv` for Python environments, dependency installation, and Python command execution unless the user explicitly says otherwise.
- Prefer `uv run ...` over direct `python ...`.
- Prefer `uv sync` for dependency installation.

## Permission Policy

- For work inside this repository, do not stop to ask for permission for non-privileged actions if the execution environment already allows them.
- For actions that require `sudo`, privileged system changes, or writes outside approved repository paths, ask for permission first.

## Important Limitation

- These instructions do not override the execution harness or sandbox.
- If the environment blocks a command or path, approval may still be required even for non-privileged repo-local work.
