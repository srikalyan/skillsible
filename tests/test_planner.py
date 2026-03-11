from __future__ import annotations

from skillsible.manifest import Manifest, SkillSpec
from skillsible.planner import build_plan


def test_build_plan_expands_skill_per_agent():
    manifest = Manifest(
        version=1,
        agents=["codex", "claude-code"],
        defaults={"scope": "global"},
        skills=[
            SkillSpec(
                source="obra/the-elements-of-style",
                skill="writing-clearly-and-concisely",
                agents=["codex", "claude-code"],
                scope="global",
            )
        ],
    )

    plan = build_plan(manifest)

    assert len(plan) == 2
    assert [op.agent for op in plan] == ["codex", "claude-code"]


def test_operation_describe_includes_scope():
    manifest = Manifest(
        version=1,
        agents=["codex"],
        defaults={},
        skills=[
            SkillSpec(
                source="obra/the-elements-of-style",
                skill="writing-clearly-and-concisely",
                agents=["codex"],
                scope="project",
                version="main",
            )
        ],
    )

    operation = build_plan(manifest)[0]

    assert operation.describe() == (
        "install writing-clearly-and-concisely for codex "
        "from obra/the-elements-of-style @ main [project]"
    )
