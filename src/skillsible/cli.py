from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .adapters import SkillsShAdapter, ToolAdapter
from .errors import AdapterError, ManifestError
from .manifest import load_manifest
from .planner import build_plan


def cmd_plan(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.file)
    plan = build_plan(manifest)

    if plan.is_empty():
        print("No operations.")
        return 0

    print(f"Plan for {Path(args.file)}")
    for op in plan.skills:
        print(f"- {op.describe()}")
    for op in plan.tools:
        print(f"- {op.describe()}")
    for op in plan.mcps:
        print(f"- {op.describe()}")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.file)
    plan = build_plan(manifest)
    adapter = SkillsShAdapter()
    tool_adapter = ToolAdapter()

    if plan.is_empty():
        print("No operations.")
        return 0

    failures = 0
    for op in plan.skills:
        result = adapter.apply(op, dry_run=args.dry_run)
        print(f"$ {' '.join(result.command)}")
        if result.returncode != 0:
            failures += 1

    for op in plan.tools:
        result = tool_adapter.apply(op, dry_run=args.dry_run)
        print(f"$ {' '.join(result.command)}")
        if result.returncode != 0:
            failures += 1

    for op in plan.mcps:
        print(f"# not yet applied: {op.describe()}")

    return 1 if failures else 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    adapter = SkillsShAdapter()
    doctor = adapter.doctor()
    print("Doctor")
    print(f"- python: {sys.executable}")
    print(f"- npx: {'found' if doctor.npx_found else 'missing'}")
    if doctor.npx_path:
        print(f"- npx path: {doctor.npx_path}")
    elif doctor.nvm_candidates:
        print("- npx hint: found under nvm, but not on current PATH")
        print(f"- nvm candidate: {doctor.nvm_candidates[0]}")
        print("- suggestion: ensure your shell initializes nvm before running skillsible")
    print("- expected external installer: `npx skills`")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillsible",
        description="Ansible-style skill management for agent CLIs",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Show planned operations")
    plan_parser.add_argument("-f", "--file", default="skills.yml")
    plan_parser.set_defaults(func=cmd_plan)

    apply_parser = subparsers.add_parser("apply", help="Apply manifest operations")
    apply_parser.add_argument("-f", "--file", default="skills.yml")
    apply_parser.add_argument("--dry-run", action="store_true")
    apply_parser.set_defaults(func=cmd_apply)

    doctor_parser = subparsers.add_parser("doctor", help="Check prerequisites")
    doctor_parser.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ManifestError, AdapterError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
