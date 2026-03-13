from __future__ import annotations

import subprocess
from dataclasses import dataclass
from dataclasses import replace
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


@dataclass(slots=True)
class LockedManifest:
    version: int
    generated_by: dict[str, object]
    source_manifest: str
    manifest_version: int
    skills: list[dict[str, object]]
    tools: list[dict[str, object]]
    mcps: list[dict[str, object]]


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


def load_lockfile(path: str | Path) -> LockedManifest:
    raw_path = Path(path)
    raw = yaml.safe_load(raw_path.read_text()) or {}
    if not isinstance(raw, dict):
        raise AdapterError(f"Lockfile root must be a mapping: {raw_path}")

    version = int(raw.get("version", 0))
    if version != LOCKFILE_VERSION:
        raise AdapterError(f"Unsupported lockfile version: {version}")

    return LockedManifest(
        version=version,
        generated_by=dict(raw.get("generated_by", {})),
        source_manifest=str(raw.get("source_manifest", "")),
        manifest_version=int(raw.get("manifest_version", 0)),
        skills=list(raw.get("skills", [])),
        tools=list(raw.get("tools", [])),
        mcps=list(raw.get("mcps", [])),
    )


def apply_lockfile_to_manifest(manifest: Manifest, lockfile: LockedManifest) -> Manifest:
    locked_skills = {
        _skill_key_from_payload(item): item
        for item in lockfile.skills
        if isinstance(item, dict)
    }

    skills: list[SkillSpec] = []
    for spec in manifest.skills:
        locked = locked_skills.get(_skill_key(spec))
        if locked is None:
            raise AdapterError(
                f"Manifest skill '{spec.skill}' is missing from lockfile; regenerate the lockfile"
            )

        locked_source = str(locked.get("resolved_source") or spec.source)
        locked_version = locked.get("resolved_version") or locked.get("requested_version") or spec.version
        skills.append(
            replace(
                spec,
                source=locked_source,
                version=str(locked_version) if locked_version is not None else None,
            )
        )

    return Manifest(
        version=manifest.version,
        agents=manifest.agents,
        defaults=manifest.defaults,
        skills=skills,
        tools=manifest.tools,
        mcps=manifest.mcps,
    )


def diff_lockfile(manifest: Manifest, source_file: str, lockfile: LockedManifest, skillsible_version: str) -> list[str]:
    current = build_lockfile(manifest, source_file, skillsible_version)
    baseline = {
        "version": lockfile.version,
        "generated_by": lockfile.generated_by,
        "source_manifest": lockfile.source_manifest,
        "manifest_version": lockfile.manifest_version,
        "skills": lockfile.skills,
        "tools": lockfile.tools,
        "mcps": lockfile.mcps,
    }
    return _diff_values(current, baseline)


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
    if spec.source is not None:
        payload["source"] = {
            spec.source.type: {
                "package": spec.source.package,
                **({"version": spec.source.version} if spec.source.version is not None else {}),
            }
        }
    if spec.verify is not None:
        payload["verify"] = {
            "command": spec.verify.command,
            "args": spec.verify.args,
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


def _skill_key(spec: SkillSpec) -> tuple[object, ...]:
    return (
        spec.source,
        spec.skill,
        tuple(spec.agents),
        spec.scope,
        spec.version,
    )


def _skill_key_from_payload(item: dict[str, object]) -> tuple[object, ...]:
    return (
        item.get("source"),
        item.get("skill"),
        tuple(item.get("agents", [])),
        item.get("scope"),
        item.get("requested_version"),
    )


def _diff_values(current: object, baseline: object, prefix: str = "") -> list[str]:
    if type(current) is not type(baseline):
        return [f"{prefix or 'root'}: {baseline!r} -> {current!r}"]

    if isinstance(current, dict):
        diffs: list[str] = []
        keys = sorted(set(current) | set(baseline))
        for key in keys:
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in baseline:
                diffs.append(f"{path}: <missing> -> {current[key]!r}")
            elif key not in current:
                diffs.append(f"{path}: {baseline[key]!r} -> <missing>")
            else:
                diffs.extend(_diff_values(current[key], baseline[key], path))
        return diffs

    if isinstance(current, list):
        if current == baseline:
            return []
        return [f"{prefix or 'root'}: {baseline!r} -> {current!r}"]

    if current != baseline:
        return [f"{prefix or 'root'}: {baseline!r} -> {current!r}"]
    return []
