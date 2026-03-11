from __future__ import annotations

from dataclasses import dataclass

from .manifest import Manifest


@dataclass(slots=True)
class InstallOperation:
    agent: str
    source: str
    skill: str
    scope: str
    version: str | None = None

    def describe(self) -> str:
        version_suffix = f" @ {self.version}" if self.version else ""
        return (
            f"install {self.skill} for {self.agent} "
            f"from {self.source}{version_suffix} [{self.scope}]"
        )


@dataclass(slots=True)
class ToolOperation:
    agent: str
    name: str
    kind: str
    package: str | None = None
    binary: str | None = None
    uv_tool: str | None = None
    npm: str | None = None

    def describe(self) -> str:
        details: list[str] = []
        if self.package:
            details.append(f"package={self.package}")
        if self.binary:
            details.append(f"binary={self.binary}")
        if self.uv_tool:
            details.append(f"uv_tool={self.uv_tool}")
        if self.npm:
            details.append(f"npm={self.npm}")
        suffix = f" ({', '.join(details)})" if details else ""
        return f"tool {self.name} for {self.agent} [{self.kind}]{suffix}"


@dataclass(slots=True)
class McpOperation:
    agent: str
    name: str
    transport: str | None = None
    command: str | None = None
    url: str | None = None

    def describe(self) -> str:
        details: list[str] = []
        if self.transport:
            details.append(f"transport={self.transport}")
        if self.command:
            details.append(f"command={self.command}")
        if self.url:
            details.append(f"url={self.url}")
        suffix = f" ({', '.join(details)})" if details else ""
        return f"mcp {self.name} for {self.agent}{suffix}"


@dataclass(slots=True)
class Plan:
    skills: list[InstallOperation]
    tools: list[ToolOperation]
    mcps: list[McpOperation]

    def is_empty(self) -> bool:
        return not self.skills and not self.tools and not self.mcps


def build_plan(manifest: Manifest) -> Plan:
    skill_operations: list[InstallOperation] = []
    for spec in manifest.skills:
        for agent in spec.agents:
            skill_operations.append(
                InstallOperation(
                    agent=agent,
                    source=spec.source,
                    skill=spec.skill,
                    scope=spec.scope,
                    version=spec.version,
                )
            )

    tool_operations: list[ToolOperation] = []
    for spec in manifest.tools:
        for agent in spec.agents:
            tool_operations.append(
                ToolOperation(
                    agent=agent,
                    name=spec.name,
                    kind=spec.kind,
                    package=spec.package,
                    binary=spec.binary,
                    uv_tool=spec.install.uv_tool if spec.install else None,
                    npm=spec.install.npm if spec.install else None,
                )
            )

    mcp_operations: list[McpOperation] = []
    for spec in manifest.mcps:
        for agent in spec.agents:
            mcp_operations.append(
                McpOperation(
                    agent=agent,
                    name=spec.name,
                    transport=spec.transport,
                    command=spec.command,
                    url=spec.url,
                )
            )

    return Plan(
        skills=skill_operations,
        tools=tool_operations,
        mcps=mcp_operations,
    )
