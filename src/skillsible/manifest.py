from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .errors import ManifestError


@dataclass(slots=True)
class SkillSpec:
    source: str
    skill: str
    agents: list[str] = field(default_factory=list)
    scope: str = "global"
    version: str | None = None


@dataclass(slots=True)
class Manifest:
    version: int
    agents: list[str]
    defaults: dict[str, object]
    skills: list[SkillSpec]


def load_manifest(path: str | Path) -> Manifest:
    raw_path = Path(path)
    raw = yaml.safe_load(raw_path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ManifestError(f"Manifest root must be a mapping: {raw_path}")

    version = int(raw.get("version", 1))
    if version != 1:
        raise ManifestError(f"Unsupported manifest version: {version}")

    agents = list(raw.get("agents", []))
    if not agents:
        raise ManifestError("Manifest must define at least one agent")

    defaults = dict(raw.get("defaults", {}))
    allowed_scopes = {"global", "project"}

    skills: list[SkillSpec] = []
    for item in raw.get("skills", []):
        if not isinstance(item, dict):
            raise ManifestError("Each skill entry must be a mapping")
        if "source" not in item or "skill" not in item:
            raise ManifestError("Each skill entry must define both 'source' and 'skill'")
        scope = str(item.get("scope", defaults.get("scope", "global")))
        if scope not in allowed_scopes:
            raise ManifestError(f"Unsupported scope: {scope}")
        item_agents = list(item.get("agents", agents))
        if not item_agents:
            raise ManifestError(
                f"Skill '{item.get('skill', '<unknown>')}' must target at least one agent"
            )
        skills.append(
            SkillSpec(
                source=str(item["source"]),
                skill=str(item["skill"]),
                agents=item_agents,
                scope=scope,
                version=item.get("version"),
            )
        )

    if not skills:
        raise ManifestError("Manifest must define at least one skill")

    return Manifest(
        version=version,
        agents=agents,
        defaults=defaults,
        skills=skills,
    )
