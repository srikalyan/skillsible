from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .planner import InstallOperation


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
