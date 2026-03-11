from __future__ import annotations

from pathlib import Path

import pytest

from skillsible.errors import ManifestError
from skillsible.manifest import load_manifest


def test_load_manifest_applies_default_agents_and_scope(tmp_path: Path):
    path = tmp_path / "skills.yml"
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "defaults:",
                "  scope: global",
                "skills:",
                "  - source: obra/the-elements-of-style",
                "    skill: writing-clearly-and-concisely",
            ]
        )
    )

    manifest = load_manifest(path)

    assert manifest.version == 1
    assert manifest.agents == ["codex"]
    assert manifest.skills[0].agents == ["codex"]
    assert manifest.skills[0].scope == "global"


def test_load_manifest_rejects_missing_agents(tmp_path: Path):
    path = tmp_path / "skills.yml"
    path.write_text("version: 1\nskills: []\n")

    with pytest.raises(ManifestError, match="at least one agent"):
        load_manifest(path)


def test_load_manifest_rejects_invalid_scope(tmp_path: Path):
    path = tmp_path / "skills.yml"
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                "  - source: obra/the-elements-of-style",
                "    skill: writing-clearly-and-concisely",
                "    scope: machine",
            ]
        )
    )

    with pytest.raises(ManifestError, match="Unsupported scope"):
        load_manifest(path)
