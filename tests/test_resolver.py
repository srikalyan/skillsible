from __future__ import annotations

from pathlib import Path

import pytest

from skillsible.adapters import SkillsShAdapter
from skillsible.errors import AdapterError
from skillsible.planner import InstallOperation
from skillsible.resolver import resolve_display_source, resolve_install_source


def test_resolve_display_source_includes_version_for_github_shorthand():
    operation = InstallOperation(
        agent="codex",
        source="obra/the-elements-of-style",
        skill="writing-clearly-and-concisely",
        scope="global",
        version="v1.2.0",
    )

    assert resolve_display_source(operation) == "obra/the-elements-of-style @ v1.2.0"


def test_resolve_install_source_rejects_unsupported_versioned_source():
    operation = InstallOperation(
        agent="codex",
        source="not a valid source",
        skill="writing-clearly-and-concisely",
        scope="global",
        version="main",
    )

    with pytest.raises(AdapterError, match="Unsupported versioned source"):
        with resolve_install_source(operation):
            pass


def test_resolve_install_source_checks_out_local_repo_at_requested_version(tmp_path: Path):
    repo_path = tmp_path / "skill-repo"
    repo_path.mkdir()
    subprocess_run(["git", "init", "-b", "main", str(repo_path)])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.name", "Test User"])
    subprocess_run(["git", "-C", str(repo_path), "config", "user.email", "test@example.com"])
    (repo_path / "SKILL.md").write_text("version one\n")
    subprocess_run(["git", "-C", str(repo_path), "add", "SKILL.md"])
    subprocess_run(["git", "-C", str(repo_path), "commit", "-m", "v1"])
    subprocess_run(["git", "-C", str(repo_path), "tag", "v1.0.0"])

    (repo_path / "SKILL.md").write_text("version two\n")
    subprocess_run(["git", "-C", str(repo_path), "commit", "-am", "v2"])

    operation = InstallOperation(
        agent="codex",
        source=str(repo_path),
        skill="writing-clearly-and-concisely",
        scope="global",
        version="v1.0.0",
    )

    with resolve_install_source(operation) as resolved:
        assert Path(resolved.install_source, "SKILL.md").read_text() == "version one\n"


def test_doctor_scans_nvm_paths_without_crashing(monkeypatch, tmp_path: Path):
    nvm_dir = tmp_path / ".nvm"
    npx_path = nvm_dir / "versions/node/v20.0.0/bin/npx"
    npx_path.parent.mkdir(parents=True)
    npx_path.write_text("")

    monkeypatch.setenv("NVM_DIR", str(nvm_dir))
    monkeypatch.setattr("skillsible.adapters.shutil.which", lambda _name: None)

    doctor = SkillsShAdapter().doctor()

    assert doctor.npx_found is False
    assert str(npx_path) in (doctor.nvm_candidates or [])


def subprocess_run(command: list[str]) -> None:
    import subprocess

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
