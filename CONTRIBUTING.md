# Contributing

## Branching

The protected default branch is `main`.

Do not work directly on `main`. Create a feature branch and open a pull request.

Example:

```bash
git checkout -b feat/add-export-command
```

## Pull Requests

To merge into `main`, GitHub currently requires:

- a pull request
- all CI checks passing
- resolved review conversations
- linear history

Direct pushes to `main` are blocked by branch protection.

As the repository owner, you can comment `LGTM` or `looks good to me` on a PR to enable auto-merge.
If checks are already green, it will merge immediately. Otherwise it will merge as soon as required checks pass.

## Release Process

Releases are tag-driven.

1. Make code changes on a branch.
2. Update the package version in `pyproject.toml`.
3. Open a pull request to `main`.
4. Wait for CI to pass.
5. Merge the PR.
6. Create and push a version tag from `main`.

Example:

```bash
git checkout main
git pull --ff-only
git tag v1.1.0
git push origin v1.1.0
```

## Publishing

Pushing a tag matching `v*` triggers `.github/workflows/publish.yml`.

That workflow:

- builds the source distribution and wheel with `uv build`
- publishes to PyPI using Trusted Publishing

## Local Development

```bash
uv sync --dev
uv run pytest
uv run skillsible doctor
```
