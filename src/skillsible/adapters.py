from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import AdapterError
from .planner import InstallOperation
from .planner import ToolOperation
from .resolver import resolve_display_source, resolve_install_source


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    returncode: int


@dataclass(slots=True)
class DoctorResult:
    npx_found: bool
    npx_path: str | None = None
    nvm_candidates: list[str] | None = None


class SkillsShAdapter:
    """Adapter that installs skills via the external `skills` CLI."""

    name = "skills.sh"

    def doctor(self) -> DoctorResult:
        npx_path = shutil.which("npx")
        candidates = self._find_nvm_npx_candidates()
        return DoctorResult(
            npx_found=npx_path is not None,
            npx_path=npx_path,
            nvm_candidates=candidates,
        )

    def _find_nvm_npx_candidates(self) -> list[str]:
        candidates: list[str] = []

        nvm_dir = os.environ.get("NVM_DIR")
        roots: list[Path] = []
        if nvm_dir:
            roots.append(Path(nvm_dir))
        roots.append(Path.home() / ".nvm")

        seen: set[str] = set()
        for root in roots:
            if not root.exists():
                continue
            for path in sorted(root.glob("versions/node/*/bin/npx")):
                resolved = str(path)
                if resolved not in seen:
                    seen.add(resolved)
                    candidates.append(resolved)

        return candidates

    def build_install_command(self, operation: InstallOperation, source: str | None = None) -> list[str]:
        command = [
            "npx",
            "skills",
            "add",
            source or operation.source,
            "--skill",
            operation.skill,
            "--agent",
            operation.agent,
        ]
        if operation.scope:
            command.extend(["--scope", operation.scope])
        return command

    def apply(self, operation: InstallOperation, dry_run: bool = False) -> CommandResult:
        if dry_run:
            display_source = resolve_display_source(operation)
            command = self.build_install_command(operation, source=display_source)
            return CommandResult(command=command, returncode=0)

        with resolve_install_source(operation) as resolved:
            command = self.build_install_command(operation, source=resolved.install_source)
            result = subprocess.run(command, check=False)
            return CommandResult(command=command, returncode=result.returncode)


class ToolAdapter:
    """Adapter that installs or verifies shared tool dependencies."""

    name = "tools"

    def build_install_command(self, operation: ToolOperation) -> list[str]:
        if operation.uv_tool:
            return ["uv", "tool", "install", operation.uv_tool]
        if operation.npm:
            return ["npm", "install", "-g", operation.npm]
        if operation.binary:
            return ["command", "-v", operation.binary]
        raise AdapterError(
            f"Tool '{operation.name}' does not define a supported installer or binary check"
        )

    def apply(self, operation: ToolOperation, dry_run: bool = False) -> CommandResult:
        command = self.build_install_command(operation)
        if dry_run:
            return CommandResult(command=command, returncode=0)

        if operation.uv_tool:
            result = subprocess.run(command, check=False)
            return CommandResult(command=command, returncode=result.returncode)

        if operation.npm:
            if shutil.which("npm") is None:
                raise AdapterError(
                    f"Tool '{operation.name}' requires npm, but npm is not available on PATH"
                )
            result = subprocess.run(command, check=False)
            return CommandResult(command=command, returncode=result.returncode)

        if operation.binary:
            returncode = 0 if shutil.which(operation.binary) is not None else 1
            return CommandResult(command=command, returncode=returncode)

        raise AdapterError(
            f"Tool '{operation.name}' does not define a supported installer or binary check"
        )
