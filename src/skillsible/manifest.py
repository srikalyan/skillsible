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
class ToolSourceSpec:
    type: str
    package: str
    version: str | None = None


@dataclass(slots=True)
class ToolVerifySpec:
    command: str
    args: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ToolSpec:
    name: str
    kind: str
    agents: list[str] = field(default_factory=list)
    source: ToolSourceSpec | None = None
    verify: ToolVerifySpec | None = None


@dataclass(slots=True)
class McpSpec:
    name: str
    agents: list[str] = field(default_factory=list)
    transport: str | None = None
    command: str | None = None
    url: str | None = None


@dataclass(slots=True)
class Manifest:
    version: int
    agents: list[str]
    defaults: dict[str, object]
    skills: list[SkillSpec]
    tools: list[ToolSpec]
    mcps: list[McpSpec]


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

    tools: list[ToolSpec] = []
    for item in raw.get("tools", []):
        if not isinstance(item, dict):
            raise ManifestError("Each tool entry must be a mapping")
        if "name" not in item or "kind" not in item:
            raise ManifestError("Each tool entry must define both 'name' and 'kind'")
        item_agents = list(item.get("agents", agents))
        if not item_agents:
            raise ManifestError(
                f"Tool '{item.get('name', '<unknown>')}' must target at least one agent"
            )
        tools.append(
            ToolSpec(
                name=str(item["name"]),
                kind=str(item["kind"]),
                agents=item_agents,
                source=_load_tool_source(item.get("source")),
                verify=_load_tool_verify(item.get("verify")),
            )
        )

    mcps: list[McpSpec] = []
    for item in raw.get("mcps", []):
        if not isinstance(item, dict):
            raise ManifestError("Each MCP entry must be a mapping")
        if "name" not in item:
            raise ManifestError("Each MCP entry must define 'name'")
        item_agents = list(item.get("agents", agents))
        if not item_agents:
            raise ManifestError(
                f"MCP '{item.get('name', '<unknown>')}' must target at least one agent"
            )
        mcps.append(
            McpSpec(
                name=str(item["name"]),
                agents=item_agents,
                transport=str(item["transport"]) if item.get("transport") is not None else None,
                command=str(item["command"]) if item.get("command") is not None else None,
                url=str(item["url"]) if item.get("url") is not None else None,
            )
        )

    if not skills and not tools and not mcps:
        raise ManifestError("Manifest must define at least one skill, tool, or MCP")

    return Manifest(
        version=version,
        agents=agents,
        defaults=defaults,
        skills=skills,
        tools=tools,
        mcps=mcps,
    )


def _load_tool_source(raw: object) -> ToolSourceSpec | None:
    if raw is None:
        raise ManifestError("Each tool entry must define 'source'")
    if not isinstance(raw, dict):
        raise ManifestError("Tool 'source' must be a mapping")

    supported = ("uv", "npm", "go", "cargo")
    keys = [key for key in supported if raw.get(key) is not None]
    if len(keys) != 1:
        raise ManifestError("Tool 'source' must define exactly one supported backend")

    backend = keys[0]
    backend_raw = raw[backend]
    if not isinstance(backend_raw, dict):
        raise ManifestError(f"Tool source '{backend}' must be a mapping")

    package = backend_raw.get("package") or backend_raw.get("crate")
    if package is None:
        raise ManifestError(f"Tool source '{backend}' must define 'package'")

    version = backend_raw.get("version")
    return ToolSourceSpec(
        type=backend,
        package=str(package),
        version=str(version) if version is not None else None,
    )


def _load_tool_verify(raw: object) -> ToolVerifySpec | None:
    if raw is None:
        raise ManifestError("Each tool entry must define 'verify'")
    if not isinstance(raw, dict):
        raise ManifestError("Tool 'verify' must be a mapping")

    command = raw.get("command")
    if command is None:
        raise ManifestError("Tool 'verify' must define 'command'")

    args = raw.get("args", [])
    if not isinstance(args, list):
        raise ManifestError("Tool 'verify.args' must be a list")

    return ToolVerifySpec(
        command=str(command),
        args=[str(item) for item in args],
    )
