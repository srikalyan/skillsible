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
class InspectionResult:
    title: str
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    unavailable_reason: str | None = None


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
            "-y",
        ]
        if operation.scope == "global":
            command.append("-g")
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
        if operation.source_type == "uv":
            package = operation.package
            if operation.version:
                package = f"{package}=={operation.version}"
            return ["uv", "tool", "install", package]
        if operation.source_type == "npm":
            package = operation.package
            if operation.version:
                package = f"{package}@{operation.version}"
            return ["npm", "install", "-g", package]
        if operation.source_type == "go":
            version = operation.version or "latest"
            return ["go", "install", f"{operation.package}@{version}"]
        if operation.source_type == "cargo":
            command = ["cargo", "install", operation.package]
            if operation.version:
                command.extend(["--version", operation.version])
            return command
        raise AdapterError(f"Tool '{operation.name}' uses unsupported source '{operation.source_type}'")

    def build_verify_command(self, operation: ToolOperation) -> list[str]:
        if not operation.verify_command:
            raise AdapterError(f"Tool '{operation.name}' does not define a verification command")
        return [operation.verify_command, *(operation.verify_args or [])]

    def apply(self, operation: ToolOperation, dry_run: bool = False) -> list[CommandResult]:
        install_command = self.build_install_command(operation)
        verify_command = self.build_verify_command(operation)
        if dry_run:
            return [
                CommandResult(command=install_command, returncode=0),
                CommandResult(command=verify_command, returncode=0),
            ]

        install_binary = install_command[0]
        if shutil.which(install_binary) is None:
            raise AdapterError(
                f"Tool '{operation.name}' requires {install_binary}, but {install_binary} is not available on PATH"
            )

        install_result = subprocess.run(install_command, check=False)
        results = [CommandResult(command=install_command, returncode=install_result.returncode)]
        if install_result.returncode != 0:
            return results

        verify_binary = verify_command[0]
        if shutil.which(verify_binary) is None:
            results.append(CommandResult(command=verify_command, returncode=127))
            return results

        verify_result = subprocess.run(verify_command, check=False)
        results.append(CommandResult(command=verify_command, returncode=verify_result.returncode))
        return results


class McpAdapter:
    """Adapter that configures MCP servers for supported agent CLIs."""

    name = "mcps"

    def apply(self, operation, dry_run: bool = False) -> list[CommandResult]:
        command = self.build_add_command(operation)
        if dry_run:
            return [CommandResult(command=command, returncode=0)]

        self._reconcile_existing(operation)

        binary = command[0]
        if shutil.which(binary) is None:
            raise AdapterError(
                f"MCP '{operation.name}' for {operation.agent} requires {binary}, but {binary} is not available on PATH"
            )

        result = subprocess.run(command, check=False)
        return [CommandResult(command=command, returncode=result.returncode)]

    def build_add_command(self, operation) -> list[str]:
        if operation.agent == "codex":
            return self._build_codex_add(operation)
        if operation.agent == "claude-code":
            return self._build_claude_add(operation)
        raise AdapterError(f"Unsupported MCP target '{operation.agent}'")

    def _build_codex_add(self, operation) -> list[str]:
        if operation.headers:
            raise AdapterError(
                f"MCP '{operation.name}' uses headers, which Codex does not support via `codex mcp add`"
            )

        command = ["codex", "mcp", "add", operation.name]
        if operation.url:
            command.extend(["--url", operation.url])
            if operation.bearer_token_env_var:
                command.extend(["--bearer-token-env-var", operation.bearer_token_env_var])
            return command

        for key, value in sorted((operation.env or {}).items()):
            command.extend(["--env", f"{key}={value}"])
        command.append("--")
        command.append(operation.command)
        command.extend(operation.args or [])
        return command

    def _build_claude_add(self, operation) -> list[str]:
        command = ["claude", "mcp", "add"]
        if operation.transport:
            command.extend(["--transport", operation.transport])
        for key, value in sorted((operation.env or {}).items()):
            command.extend(["--env", f"{key}={value}"])
        for key, value in sorted((operation.headers or {}).items()):
            command.extend(["--header", f"{key}: {value}"])
        if operation.bearer_token_env_var:
            token = os.environ.get(operation.bearer_token_env_var)
            if token is None:
                raise AdapterError(
                    f"MCP '{operation.name}' requires env var {operation.bearer_token_env_var} for bearer auth"
                )
            command.extend(["--header", f"Authorization: Bearer {token}"])
        command.append(operation.name)
        if operation.url:
            command.append(operation.url)
        else:
            command.append("--")
            command.append(operation.command)
            command.extend(operation.args or [])
        return command

    def _reconcile_existing(self, operation) -> None:
        if operation.agent == "codex":
            exists = subprocess.run(
                ["codex", "mcp", "get", operation.name, "--json"],
                check=False,
                capture_output=True,
                text=True,
            )
            if exists.returncode == 0:
                remove = subprocess.run(["codex", "mcp", "remove", operation.name], check=False)
                if remove.returncode != 0:
                    raise AdapterError(f"Failed to remove existing Codex MCP '{operation.name}'")
            return

        if operation.agent == "claude-code":
            listing = subprocess.run(
                ["claude", "mcp", "list"],
                check=False,
                capture_output=True,
                text=True,
            )
            if listing.returncode != 0:
                raise AdapterError("Failed to inspect existing Claude MCP servers")
            lines = [line.strip() for line in listing.stdout.splitlines() if line.strip()]
            if any(line.startswith(f"{operation.name}:") for line in lines):
                remove = subprocess.run(["claude", "mcp", "remove", operation.name], check=False)
                if remove.returncode != 0:
                    raise AdapterError(f"Failed to remove existing Claude MCP '{operation.name}'")
            return

        raise AdapterError(f"Unsupported MCP target '{operation.agent}'")


class AgentInspector:
    """Inspect what supported agent CLIs currently discover."""

    def inspect(self, agent: str) -> list[InspectionResult]:
        if agent == "codex":
            return self._inspect_codex()
        if agent == "claude-code":
            return self._inspect_claude()
        raise AdapterError(f"Unsupported inspect target '{agent}'")

    def _inspect_codex(self) -> list[InspectionResult]:
        return [
            self._run(["npx", "skills", "ls", "-a", "codex"], title="Project skills"),
            self._run(["npx", "skills", "ls", "-g", "-a", "codex"], title="Global skills"),
            self._run(["codex", "mcp", "list"], title="MCPs"),
        ]

    def _inspect_claude(self) -> list[InspectionResult]:
        return [
            self._run(["npx", "skills", "ls", "-a", "claude-code"], title="Project skills"),
            self._run(["npx", "skills", "ls", "-g", "-a", "claude-code"], title="Global skills"),
            self._run(["claude", "plugins", "list"], title="Plugins"),
            self._run(["claude", "mcp", "list"], title="MCPs"),
        ]

    def _run(self, command: list[str], title: str) -> InspectionResult:
        binary = command[0]
        if shutil.which(binary) is None:
            return InspectionResult(
                title=title,
                command=command,
                returncode=127,
                unavailable_reason=f"{binary} is not available on PATH",
            )

        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        return InspectionResult(
            title=title,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
        )
