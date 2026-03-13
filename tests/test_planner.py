from __future__ import annotations

from skillsible.manifest import Manifest, McpSpec, SkillSpec, ToolSourceSpec, ToolSpec, ToolVerifySpec
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
        tools=[],
        mcps=[],
    )

    plan = build_plan(manifest)

    assert len(plan.skills) == 2
    assert [op.agent for op in plan.skills] == ["codex", "claude-code"]


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
        tools=[],
        mcps=[],
    )

    operation = build_plan(manifest).skills[0]

    assert operation.describe() == (
        "install writing-clearly-and-concisely for codex "
        "from obra/the-elements-of-style @ main [project]"
    )


def test_build_plan_includes_tools_and_mcps():
    manifest = Manifest(
        version=1,
        agents=["codex", "claude-code"],
        defaults={},
        skills=[],
        tools=[
            ToolSpec(
                name="pyright",
                kind="lsp",
                agents=["codex", "claude-code"],
                source=ToolSourceSpec(type="npm", package="pyright"),
                verify=ToolVerifySpec(command="pyright", args=["--version"]),
            )
        ],
        mcps=[
            McpSpec(
                name="github",
                agents=["claude-code"],
                transport="stdio",
                command="github-mcp",
                args=["--serve"],
            )
        ],
    )

    plan = build_plan(manifest)

    assert len(plan.tools) == 2
    assert (
        plan.tools[0].describe()
        == "tool pyright for codex [lsp] (npm=pyright, verify=pyright --version)"
    )
    assert (
        plan.mcps[0].describe()
        == "mcp github for claude-code (transport=stdio, command=github-mcp --serve)"
    )
