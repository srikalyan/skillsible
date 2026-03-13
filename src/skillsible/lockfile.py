from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import AdapterError
from .manifest import Manifest
from .manifest import McpSpec
from .manifest import SkillSpec
from .manifest import ToolSpec
from .resolver import CloneTarget
from .resolver import classify_source
from .resolver import source_ref_hint


LOCKFILE_VERSION = 1


@dataclass(slots=True)
class LockedSkill:
    source: str
    skill: str
    agents: list[str]
    scope: str
    requested_version: str | None
    resolved_version: str | None
    resolved_source: str | None


def build_lockfile(manifest: Manifest, source_file: str, skillsible_version: str) -> dict[str, object]:
    return {
        "version": LOCKFILE_VERSION,
        "generated_by": {
            "name": "skillsible",
            "version": skillsible_version,
        },
        "source_manifest": str(Path(source_file)),
        "manifest_version": manifest.version,
        "skills": [_locked_skill_payload(spec) for spec in manifest.skills],
        "tools": [_tool_payload(spec) for spec in manifest.tools],
        "mcps": [_mcp_payload(spec) for spec in manifest.mcps],
    }


def write_lockfile(path: str | Path, payload: dict[str, object]) -> None:
    Path(path).write_text(yaml.safe_dump(payload, sort_keys=False))


def _locked_skill_payload(spec: SkillSpec) -> dict[str, object]:
    clone_target = classify_source(spec.source)
    requested_version = spec.version or source_ref_hint(spec.source)
    resolved_version = _resolve_version(clone_target, requested_version)

    locked = LockedSkill(
        source=spec.source,
        skill=spec.skill,
        agents=spec.agents,
        scope=spec.scope,
        requested_version=requested_version,
        resolved_version=resolved_version,
        resolved_source=clone_target.clone_source if clone_target else None,
    )
    return {
        "source": locked.source,
        "skill": locked.skill,
        "agents": locked.agents,
        "scope": locked.scope,
        "requested_version": locked.requested_version,
        "resolved_version": locked.resolved_version,
        "resolved_source": locked.resolved_source,
    }


def _resolve_version(target: CloneTarget | None, requested_version: str | None) -> str | None:
    if target is None:
        return None

    if _is_local_path(target.clone_source):
        return _resolve_local_version(target.clone_source, requested_version)

    return _resolve_remote_version(target.clone_source, requested_version)


def _resolve_local_version(source: str, requested_version: str | None) -> str:
    command = ["git", "-C", source, "rev-parse", requested_version or "HEAD"]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or "no additional details"
        raise AdapterError(f"Failed to resolve local git revision for {source}: {detail}")
    return result.stdout.strip()


def _resolve_remote_version(source: str, requested_version: str | None) -> str | None:
    refs = ["HEAD"]
    if requested_version:
        refs = [
            requested_version,
            f"refs/tags/{requested_version}",
            f"refs/heads/{requested_version}",
        ]

    for ref in refs:
        result = subprocess.run(
            ["git", "ls-remote", source, ref],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or "no additional details"
            raise AdapterError(f"Failed to resolve remote git revision for {source}: {detail}")

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if lines:
            return lines[0].split()[0]

    return None


def _is_local_path(source: str) -> bool:
    return Path(source).expanduser().exists()


def _tool_payload(spec: ToolSpec) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": spec.name,
        "kind": spec.kind,
        "agents": spec.agents,
    }
    if spec.package is not None:
        payload["package"] = spec.package
    if spec.binary is not None:
        payload["binary"] = spec.binary
    if spec.install is not None:
        payload["install"] = {
            key: value
            for key, value in {
                "uv_tool": spec.install.uv_tool,
                "npm": spec.install.npm,
            }.items()
            if value is not None
        }
    return payload


def _mcp_payload(spec: McpSpec) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": spec.name,
        "agents": spec.agents,
    }
    if spec.transport is not None:
        payload["transport"] = spec.transport
    if spec.command is not None:
        payload["command"] = spec.command
    if spec.url is not None:
        payload["url"] = spec.url
    return payload
