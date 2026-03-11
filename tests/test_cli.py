from __future__ import annotations

from pathlib import Path

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


def test_invalid_manifest_exits_with_error(capsys, tmp_path: Path):
    manifest_path = tmp_path / "skills.yml"
    manifest_path.write_text("version: 2\nagents:\n  - codex\nskills: []\n")

    rc = main(["plan", "-f", str(manifest_path)])
    err = capsys.readouterr().err

    assert rc == 2
    assert "Unsupported manifest version" in err
