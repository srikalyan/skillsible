from __future__ import annotations

from pathlib import Path

from skillsible.adapters import DoctorResult
from skillsible.cli import main


def test_plan_command_prints_operations(capsys, tmp_path: Path):
    manifest_path = tmp_path / "skills.yml"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                "  - source: obra/the-elements-of-style",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    rc = main(["plan", "-f", str(manifest_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "Plan for" in out
    assert "writing-clearly-and-concisely" in out


def test_apply_dry_run_prints_command(capsys, tmp_path: Path):
    manifest_path = tmp_path / "skills.yml"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                "  - source: obra/the-elements-of-style",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    rc = main(["apply", "--dry-run", "-f", str(manifest_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "npx skills add obra/the-elements-of-style" in out


def test_apply_dry_run_prints_versioned_source_hint(capsys, tmp_path: Path):
    manifest_path = tmp_path / "skills.yml"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                "  - source: obra/the-elements-of-style",
                "    skill: writing-clearly-and-concisely",
                "    version: v1.2.0",
            ]
        )
    )

    rc = main(["apply", "--dry-run", "-f", str(manifest_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "npx skills add obra/the-elements-of-style @ v1.2.0" in out


def test_invalid_manifest_exits_with_error(capsys, tmp_path: Path):
    manifest_path = tmp_path / "skills.yml"
    manifest_path.write_text("version: 2\nagents:\n  - codex\nskills: []\n")

    rc = main(["plan", "-f", str(manifest_path)])
    err = capsys.readouterr().err

    assert rc == 2
    assert "Unsupported manifest version" in err


def test_plan_prints_tools_and_mcps(capsys, tmp_path: Path):
    manifest_path = tmp_path / "skills.yml"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "tools:",
                "  - name: pyright",
                "    kind: lsp",
                "    package: pyright",
                "    install:",
                "      npm: pyright",
                "mcps:",
                "  - name: github",
                "    transport: stdio",
                "    command: github-mcp",
            ]
        )
    )

    rc = main(["plan", "-f", str(manifest_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "tool pyright for codex [lsp] (package=pyright, npm=pyright)" in out
    assert "mcp github for codex (transport=stdio, command=github-mcp)" in out


def test_apply_dry_run_prints_tool_install_commands(capsys, tmp_path: Path):
    manifest_path = tmp_path / "skills.yml"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "tools:",
                "  - name: ruff",
                "    kind: cli",
                "    install:",
                "      uv_tool: ruff",
                "  - name: pyright",
                "    kind: lsp",
                "    install:",
                "      npm: pyright",
                "  - name: gh",
                "    kind: cli",
                "    binary: gh",
            ]
        )
    )

    rc = main(["apply", "--dry-run", "-f", str(manifest_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "$ uv tool install ruff" in out
    assert "$ npm install -g pyright" in out
    assert "$ command -v gh" in out


def test_doctor_shows_nvm_hint_when_npx_missing(monkeypatch, capsys):
    def _fake_doctor(self):
        return DoctorResult(
            npx_found=False,
            npx_path=None,
            nvm_candidates=["/home/test/.nvm/versions/node/v24.0.2/bin/npx"],
        )

    monkeypatch.setattr("skillsible.cli.SkillsShAdapter.doctor", _fake_doctor)

    rc = main(["doctor"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "- npx: missing" in out
    assert "found under nvm" in out


def test_doctor_shows_npx_path_when_found(monkeypatch, capsys):
    def _fake_doctor(self):
        return DoctorResult(
            npx_found=True,
            npx_path="/home/test/.nvm/versions/node/v24.0.2/bin/npx",
            nvm_candidates=["/home/test/.nvm/versions/node/v24.0.2/bin/npx"],
        )

    monkeypatch.setattr("skillsible.cli.SkillsShAdapter.doctor", _fake_doctor)

    rc = main(["doctor"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "- npx: found" in out
    assert "- npx path: /home/test/.nvm/versions/node/v24.0.2/bin/npx" in out


def test_inspect_defaults_to_codex_and_claude(monkeypatch, capsys):
    calls: list[str] = []

    class _FakeInspector:
        def inspect(self, agent: str):
            calls.append(agent)
            return []

    monkeypatch.setattr("skillsible.cli.AgentInspector", _FakeInspector)

    rc = main(["inspect"])
    out = capsys.readouterr().out

    assert rc == 0
    assert calls == ["codex", "claude-code"]
    assert "[codex]" in out
    assert "[claude-code]" in out


def test_inspect_prints_command_output_and_failure(monkeypatch, capsys):
    class _FakeResult:
        def __init__(
            self,
            command: list[str],
            returncode: int,
            stdout: str = "",
            stderr: str = "",
            unavailable_reason: str | None = None,
        ):
            self.command = command
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
            self.unavailable_reason = unavailable_reason

    class _FakeInspector:
        def inspect(self, _agent: str):
            return [
                _FakeResult(
                    command=["npx", "skills", "ls", "-a", "codex"],
                    returncode=0,
                    stdout="demo-skill",
                ),
                _FakeResult(
                    command=["codex", "mcp", "list"],
                    returncode=127,
                    unavailable_reason="codex is not available on PATH",
                ),
            ]

    monkeypatch.setattr("skillsible.cli.AgentInspector", _FakeInspector)

    rc = main(["inspect", "--agent", "codex"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "$ npx skills ls -a codex" in captured.out
    assert "demo-skill" in captured.out
    assert "codex is not available on PATH" in captured.out
