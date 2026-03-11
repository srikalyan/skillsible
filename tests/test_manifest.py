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
                "    version: v1.2.0",
            ]
        )
    )

    manifest = load_manifest(path)

    assert manifest.version == 1
    assert manifest.agents == ["codex"]
    assert manifest.skills[0].agents == ["codex"]
    assert manifest.skills[0].scope == "global"
    assert manifest.skills[0].version == "v1.2.0"


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


def test_load_manifest_accepts_branch_tag_or_commit_as_skill_version(tmp_path: Path):
    path = tmp_path / "skills.yml"
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "skills:",
                "  - source: org/repo",
                "    skill: branch-skill",
                "    version: main",
                "  - source: org/repo",
                "    skill: tag-skill",
                "    version: v2.0.0",
                "  - source: org/repo",
                "    skill: commit-skill",
                "    version: 8c1f2d4",
            ]
        )
    )

    manifest = load_manifest(path)

    assert [skill.version for skill in manifest.skills] == ["main", "v2.0.0", "8c1f2d4"]


def test_load_manifest_accepts_tools_and_mcps(tmp_path: Path):
    path = tmp_path / "skills.yml"
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "agents:",
                "  - codex",
                "tools:",
                "  - name: pyright",
                "    kind: lsp",
                "    package: pyright",
                "mcps:",
                "  - name: github",
                "    transport: stdio",
                "    command: github-mcp",
            ]
        )
    )

    manifest = load_manifest(path)

    assert manifest.tools[0].name == "pyright"
    assert manifest.tools[0].kind == "lsp"
    assert manifest.mcps[0].name == "github"
    assert manifest.mcps[0].command == "github-mcp"
