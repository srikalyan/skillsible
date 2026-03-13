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
    source_type: str
    package: str
    version: str | None = None
    verify_command: str | None = None
    verify_args: list[str] | None = None

    def describe(self) -> str:
        details: list[str] = []
        details.append(f"{self.source_type}={self.package}")
        if self.version:
            details.append(f"version={self.version}")
        if self.verify_command:
            verify = self.verify_command
            if self.verify_args:
                verify = f"{verify} {' '.join(self.verify_args)}"
            details.append(f"verify={verify}")
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
                    source_type=spec.source.type,
                    package=spec.source.package,
                    version=spec.source.version,
                    verify_command=spec.verify.command if spec.verify else None,
                    verify_args=spec.verify.args if spec.verify else None,
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
