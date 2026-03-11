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
