from __future__ import annotations

import json
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
    assert " -y" in out


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
    assert " -y" in out


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
                "    source:",
                "      npm:",
                "        package: pyright",
                "    verify:",
                "      command: pyright",
                "      args:",
                "        - --version",
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
    assert "tool pyright for codex [lsp] (npm=pyright, verify=pyright --version)" in out
    assert "mcp github for codex (transport=stdio, command=github-mcp)" in out


def test_plan_json_prints_manifest_and_plan(capsys, tmp_path: Path):
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

    rc = main(["plan", "--json", "-f", str(manifest_path)])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == 0
    assert payload["manifest"]["agents"] == ["codex"]
    assert payload["plan"]["skills"][0]["skill"] == "writing-clearly-and-concisely"


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
                "    source:",
                "      uv:",
                "        package: ruff",
                "    verify:",
                "      command: ruff",
                "      args:",
                "        - --version",
                "  - name: pyright",
                "    kind: lsp",
                "    source:",
                "      npm:",
                "        package: pyright",
                "    verify:",
                "      command: pyright",
                "      args:",
                "        - --version",
            ]
        )
    )

    rc = main(["apply", "--dry-run", "-f", str(manifest_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "$ uv tool install ruff" in out
    assert "$ ruff --version" in out
    assert "$ npm install -g pyright" in out
    assert "$ pyright --version" in out


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


def test_validate_prints_summary(capsys, tmp_path: Path):
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

    rc = main(["validate", "-f", str(manifest_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert f"Valid manifest: {manifest_path}" in out
    assert "- skills: 1" in out


def test_validate_json_prints_details(capsys, tmp_path: Path):
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
                "    source:",
                "      npm:",
                "        package: pyright",
                "    verify:",
                "      command: pyright",
                "      args:",
                "        - --version",
            ]
        )
    )

    rc = main(["validate", "--json", "-f", str(manifest_path)])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == 0
    assert payload["valid"] is True
    assert payload["plan"]["tools"][0]["source_type"] == "npm"
    assert payload["plan"]["tools"][0]["package"] == "pyright"


def test_lock_writes_lockfile_and_prints_summary(capsys, tmp_path: Path):
    repo_path = tmp_path / "skill-repo"
    repo_path.mkdir()
    subprocess_run(["git", "init", "-b", "main", str(repo_path)])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.name", "Test User"])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.email", "test@example.com"])
    (repo_path / "SKILL.md").write_text("demo\n")
    subprocess_run(["git", "-C", str(repo_path), "add", "SKILL.md"])
    subprocess_run(["git", "-C", str(repo_path), "commit", "-m", "initial"])

    manifest_path = tmp_path / "skills.yml"
    lock_path = tmp_path / "skillsible.lock"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                f"  - source: {repo_path}",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    rc = main(["lock", "-f", str(manifest_path), "-o", str(lock_path)])
    out = capsys.readouterr().out
    contents = lock_path.read_text()

    assert rc == 0
    assert f"Wrote lockfile: {lock_path}" in out
    assert "resolved_version:" in contents
    assert "generated_by:" in contents


def test_lock_json_prints_payload(capsys, tmp_path: Path):
    repo_path = tmp_path / "skill-repo"
    repo_path.mkdir()
    subprocess_run(["git", "init", "-b", "main", str(repo_path)])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.name", "Test User"])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.email", "test@example.com"])
    (repo_path / "SKILL.md").write_text("demo\n")
    subprocess_run(["git", "-C", str(repo_path), "add", "SKILL.md"])
    subprocess_run(["git", "-C", str(repo_path), "commit", "-m", "initial"])

    manifest_path = tmp_path / "skills.yml"
    lock_path = tmp_path / "skillsible.lock"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                f"  - source: {repo_path}",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    rc = main(["lock", "--json", "-f", str(manifest_path), "-o", str(lock_path)])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == 0
    assert payload["version"] == 1
    assert payload["skills"][0]["skill"] == "writing-clearly-and-concisely"
    assert payload["skills"][0]["resolved_version"]


def test_plan_with_lockfile_uses_locked_revision(capsys, tmp_path: Path):
    repo_path = tmp_path / "skill-repo"
    repo_path.mkdir()
    subprocess_run(["git", "init", "-b", "main", str(repo_path)])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.name", "Test User"])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.email", "test@example.com"])
    (repo_path / "SKILL.md").write_text("demo\n")
    subprocess_run(["git", "-C", str(repo_path), "add", "SKILL.md"])
    subprocess_run(["git", "-C", str(repo_path), "commit", "-m", "initial"])
    resolved = subprocess_output(["git", "-C", str(repo_path), "rev-parse", "HEAD"]).strip()

    manifest_path = tmp_path / "skills.yml"
    lock_path = tmp_path / "skillsible.lock"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                f"  - source: {repo_path}",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    main(["lock", "-f", str(manifest_path), "-o", str(lock_path)])
    rc = main(["plan", "-f", str(manifest_path), "-l", str(lock_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert resolved in out


def test_diff_reports_no_drift_for_matching_lockfile(capsys, tmp_path: Path):
    repo_path = tmp_path / "skill-repo"
    repo_path.mkdir()
    subprocess_run(["git", "init", "-b", "main", str(repo_path)])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.name", "Test User"])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.email", "test@example.com"])
    (repo_path / "SKILL.md").write_text("demo\n")
    subprocess_run(["git", "-C", str(repo_path), "add", "SKILL.md"])
    subprocess_run(["git", "-C", str(repo_path), "commit", "-m", "initial"])

    manifest_path = tmp_path / "skills.yml"
    lock_path = tmp_path / "skillsible.lock"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                f"  - source: {repo_path}",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    main(["lock", "-f", str(manifest_path), "-o", str(lock_path)])
    rc = main(["diff", "-f", str(manifest_path), "-l", str(lock_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "No drift" in out


def test_diff_reports_drift_when_manifest_changes(capsys, tmp_path: Path):
    repo_path = tmp_path / "skill-repo"
    repo_path.mkdir()
    subprocess_run(["git", "init", "-b", "main", str(repo_path)])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.name", "Test User"])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.email", "test@example.com"])
    (repo_path / "SKILL.md").write_text("demo\n")
    subprocess_run(["git", "-C", str(repo_path), "add", "SKILL.md"])
    subprocess_run(["git", "-C", str(repo_path), "commit", "-m", "initial"])

    manifest_path = tmp_path / "skills.yml"
    lock_path = tmp_path / "skillsible.lock"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                f"  - source: {repo_path}",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    main(["lock", "-f", str(manifest_path), "-o", str(lock_path)])
    capsys.readouterr()
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                f"  - source: {repo_path}",
                "    skill: writing-clearly-and-concisely",
                "tools:",
                "  - name: ruff",
                "    kind: cli",
                "    source:",
                "      uv:",
                "        package: ruff",
                "    verify:",
                "      command: ruff",
                "      args:",
                "        - --version",
            ]
        )
    )

    rc = main(["diff", "-f", str(manifest_path), "-l", str(lock_path)])
    out = capsys.readouterr().out

    assert rc == 1
    assert "Drift detected" in out
    assert "tools" in out


def test_diff_json_prints_drift_payload(capsys, tmp_path: Path):
    repo_path = tmp_path / "skill-repo"
    repo_path.mkdir()
    subprocess_run(["git", "init", "-b", "main", str(repo_path)])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.name", "Test User"])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.email", "test@example.com"])
    (repo_path / "SKILL.md").write_text("demo\n")
    subprocess_run(["git", "-C", str(repo_path), "add", "SKILL.md"])
    subprocess_run(["git", "-C", str(repo_path), "commit", "-m", "initial"])

    manifest_path = tmp_path / "skills.yml"
    lock_path = tmp_path / "skillsible.lock"
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                f"  - source: {repo_path}",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    main(["lock", "-f", str(manifest_path), "-o", str(lock_path)])
    capsys.readouterr()
    manifest_path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "tools:",
                "  - name: ruff",
                "    kind: cli",
                "    source:",
                "      uv:",
                "        package: ruff",
                "    verify:",
                "      command: ruff",
                "      args:",
                "        - --version",
            ]
        )
    )

    rc = main(["diff", "--json", "-f", str(manifest_path), "-l", str(lock_path)])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == 1
    assert payload["drift"] is True
    assert payload["diffs"]


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


def test_inspect_json_prints_results(monkeypatch, capsys):
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
                    command=["codex", "mcp", "list"],
                    returncode=0,
                    stdout="No MCP servers configured yet.",
                )
            ]

    monkeypatch.setattr("skillsible.cli.AgentInspector", _FakeInspector)

    rc = main(["inspect", "--json", "--agent", "codex"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == 0
    assert payload["agents"]["codex"][0]["command"] == ["codex", "mcp", "list"]
    assert payload["agents"]["codex"][0]["stdout"] == "No MCP servers configured yet."


def subprocess_run(command: list[str]) -> None:
    import subprocess

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def subprocess_output(command: list[str]) -> str:
    import subprocess

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout
