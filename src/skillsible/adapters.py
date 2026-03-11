from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from .planner import InstallOperation


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    returncode: int


class SkillsShAdapter:
    """Adapter that installs skills via the external `skills` CLI."""

    name = "skills.sh"

    def doctor(self) -> dict[str, bool]:
        return {
            "npx": shutil.which("npx") is not None,
        }

    def build_install_command(self, operation: InstallOperation) -> list[str]:
        command = [
            "npx",
            "skills",
            "add",
            operation.source,
            "--skill",
            operation.skill,
            "--agent",
            operation.agent,
        ]
        if operation.scope:
            command.extend(["--scope", operation.scope])
        return command

    def apply(self, operation: InstallOperation, dry_run: bool = False) -> CommandResult:
        command = self.build_install_command(operation)
        if dry_run:
            return CommandResult(command=command, returncode=0)
        result = subprocess.run(command, check=False)
        return CommandResult(command=command, returncode=result.returncode)
