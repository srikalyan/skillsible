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


def build_plan(manifest: Manifest) -> list[InstallOperation]:
    operations: list[InstallOperation] = []
    for spec in manifest.skills:
        for agent in spec.agents:
            operations.append(
                InstallOperation(
                    agent=agent,
                    source=spec.source,
                    skill=spec.skill,
                    scope=spec.scope,
                    version=spec.version,
                )
            )
    return operations
