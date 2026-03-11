from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .errors import AdapterError
from .planner import InstallOperation


GITHUB_TREE_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<ref>[^/]+)(?:/(?P<subpath>.+))?$"
)
GITHUB_REPO_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")
GITHUB_SHORTHAND_RE = re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)$")


@dataclass(slots=True)
class ResolvedSource:
    install_source: str
    display_source: str


@dataclass(slots=True)
class CloneTarget:
    clone_source: str
    subpath: str | None = None


def resolve_display_source(operation: InstallOperation) -> str:
    if not operation.version:
        return operation.source
    target = _classify_source(operation.source)
    if target is None:
        return operation.source
    suffix = f" @ {operation.version}"
    if target.subpath:
        return f"{operation.source}{suffix} ({target.subpath})"
    return f"{operation.source}{suffix}"


@contextmanager
def resolve_install_source(operation: InstallOperation):
    if not operation.version:
        yield ResolvedSource(
            install_source=operation.source,
            display_source=resolve_display_source(operation),
        )
        return

    clone_target = _classify_source(operation.source)
    if clone_target is None:
        raise AdapterError(
            f"Unsupported versioned source '{operation.source}'. "
            "Use a local git repository path, a GitHub repo URL/shorthand, or a git URL."
        )

    if shutil.which("git") is None:
        raise AdapterError("git is required to install version-pinned skills")

    with tempfile.TemporaryDirectory(prefix="skillsible-source-") as temp_dir:
        checkout_dir = Path(temp_dir) / "repo"
        _clone_and_checkout(clone_target.clone_source, operation.version, checkout_dir)

        install_path = checkout_dir
        if clone_target.subpath:
            install_path = checkout_dir / clone_target.subpath
            if not install_path.exists():
                raise AdapterError(
                    f"Resolved source path '{clone_target.subpath}' does not exist in "
                    f"{clone_target.clone_source} @ {operation.version}"
                )

        yield ResolvedSource(
            install_source=str(install_path),
            display_source=resolve_display_source(operation),
        )


def _clone_and_checkout(source: str, version: str, checkout_dir: Path) -> None:
    clone_result = subprocess.run(
        ["git", "clone", "--quiet", source, str(checkout_dir)],
        check=False,
        capture_output=True,
        text=True,
    )
    if clone_result.returncode != 0:
        raise AdapterError(_format_git_error("clone", source, version, clone_result.stderr))

    checkout_result = subprocess.run(
        ["git", "-C", str(checkout_dir), "checkout", "--quiet", "--detach", version],
        check=False,
        capture_output=True,
        text=True,
    )
    if checkout_result.returncode != 0:
        raise AdapterError(
            _format_git_error("checkout", source, version, checkout_result.stderr)
        )


def _format_git_error(action: str, source: str, version: str, stderr: str) -> str:
    detail = stderr.strip() or "no additional details"
    return f"Failed to {action} {source} at {version}: {detail}"


def _classify_source(source: str) -> CloneTarget | None:
    local_path = Path(source).expanduser()
    if local_path.exists():
        return CloneTarget(clone_source=str(local_path.resolve()))

    github_tree = GITHUB_TREE_RE.match(source)
    if github_tree:
        owner = github_tree.group("owner")
        repo = github_tree.group("repo")
        subpath = github_tree.group("subpath")
        return CloneTarget(
            clone_source=f"https://github.com/{owner}/{repo}.git",
            subpath=subpath,
        )

    github_repo = GITHUB_REPO_RE.match(source)
    if github_repo:
        owner = github_repo.group("owner")
        repo = github_repo.group("repo")
        return CloneTarget(clone_source=f"https://github.com/{owner}/{repo}.git")

    shorthand = GITHUB_SHORTHAND_RE.match(source)
    if shorthand:
        owner = shorthand.group("owner")
        repo = shorthand.group("repo")
        return CloneTarget(clone_source=f"https://github.com/{owner}/{repo}.git")

    parsed = urlparse(source)
    if parsed.scheme in {"https", "http", "ssh", "git"}:
        return CloneTarget(clone_source=source)

    if source.startswith("git@"):
        return CloneTarget(clone_source=source)

    return None
