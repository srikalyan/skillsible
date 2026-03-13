from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .adapters import AgentInspector, SkillsShAdapter, ToolAdapter
from .errors import AdapterError, ManifestError
from .lockfile import apply_lockfile_to_manifest
from .lockfile import build_lockfile
from .lockfile import diff_lockfile
from .lockfile import load_lockfile
from .lockfile import write_lockfile
from .manifest import load_manifest
from .planner import build_plan
from . import __version__


def _dump_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _manifest_payload(file: str, manifest, plan) -> dict[str, object]:
    return {
        "file": str(Path(file)),
        "manifest": asdict(manifest),
        "plan": {
            "skills": [asdict(op) for op in plan.skills],
            "tools": [asdict(op) for op in plan.tools],
            "mcps": [asdict(op) for op in plan.mcps],
        },
    }


def _inspection_result_payload(result: object) -> dict[str, object]:
    return {
        "title": getattr(result, "title", ""),
        "command": getattr(result, "command"),
        "returncode": getattr(result, "returncode"),
        "stdout": getattr(result, "stdout", ""),
        "stderr": getattr(result, "stderr", ""),
        "unavailable_reason": getattr(result, "unavailable_reason", None),
    }


def cmd_plan(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.file)
    if args.lockfile:
        manifest = apply_lockfile_to_manifest(manifest, load_lockfile(args.lockfile))
    plan = build_plan(manifest)

    if plan.is_empty():
        if args.json:
            _dump_json(_manifest_payload(args.file, manifest, plan))
        else:
            print("No operations.")
        return 0

    if args.json:
        _dump_json(_manifest_payload(args.file, manifest, plan))
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
    if args.lockfile:
        manifest = apply_lockfile_to_manifest(manifest, load_lockfile(args.lockfile))
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
        results = tool_adapter.apply(op, dry_run=args.dry_run)
        for result in results:
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


def cmd_validate(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.file)
    if args.lockfile:
        manifest = apply_lockfile_to_manifest(manifest, load_lockfile(args.lockfile))
    plan = build_plan(manifest)

    if args.json:
        _dump_json(
            {
                "valid": True,
                **_manifest_payload(args.file, manifest, plan),
            }
        )
    else:
        print(f"Valid manifest: {Path(args.file)}")
        print(f"- agents: {', '.join(manifest.agents)}")
        print(f"- skills: {len(manifest.skills)}")
        print(f"- tools: {len(manifest.tools)}")
        print(f"- mcps: {len(manifest.mcps)}")
    return 0


def cmd_lock(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.file)
    payload = build_lockfile(manifest, args.file, __version__)
    write_lockfile(args.output, payload)

    if args.json:
        _dump_json(payload)
    else:
        print(f"Wrote lockfile: {Path(args.output)}")
        print(f"- skills: {len(payload['skills'])}")
        print(f"- tools: {len(payload['tools'])}")
        print(f"- mcps: {len(payload['mcps'])}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.file)
    lockfile = load_lockfile(args.lockfile)
    diffs = diff_lockfile(manifest, args.file, lockfile, __version__)

    if args.json:
        _dump_json({"drift": bool(diffs), "diffs": diffs})
    elif diffs:
        print(f"Drift detected between {Path(args.file)} and {Path(args.lockfile)}")
        for item in diffs:
            print(f"- {item}")
    else:
        print(f"No drift: {Path(args.file)} matches {Path(args.lockfile)}")

    return 1 if diffs else 0


def cmd_inspect(args: argparse.Namespace) -> int:
    inspector = AgentInspector()
    failures = 0
    payload: dict[str, object] = {"agents": {}}

    for agent in args.agent:
        results = inspector.inspect(agent)
        payload["agents"][agent] = [_inspection_result_payload(result) for result in results]
        if args.json:
            for result in results:
                if result.unavailable_reason or result.returncode != 0:
                    failures += 1
            continue

        print(f"[{agent}]")
        for result in results:
            print(f"$ {' '.join(result.command)}")
            if result.unavailable_reason:
                failures += 1
                print(f"! unavailable: {result.unavailable_reason}")
                continue
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            if result.returncode != 0:
                failures += 1
                print(f"! command exited with status {result.returncode}")

    if args.json:
        _dump_json(payload)
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillsible",
        description="Ansible-style skill management for agent CLIs",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Show planned operations")
    plan_parser.add_argument("-f", "--file", default="skills.yml")
    plan_parser.add_argument("-l", "--lockfile", help="Apply a lockfile before planning")
    plan_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    plan_parser.set_defaults(func=cmd_plan)

    apply_parser = subparsers.add_parser("apply", help="Apply manifest operations")
    apply_parser.add_argument("-f", "--file", default="skills.yml")
    apply_parser.add_argument("-l", "--lockfile", help="Apply a lockfile before applying")
    apply_parser.add_argument("--dry-run", action="store_true")
    apply_parser.set_defaults(func=cmd_apply)

    doctor_parser = subparsers.add_parser("doctor", help="Check prerequisites")
    doctor_parser.set_defaults(func=cmd_doctor)

    validate_parser = subparsers.add_parser("validate", help="Validate a manifest")
    validate_parser.add_argument("-f", "--file", default="skills.yml")
    validate_parser.add_argument("-l", "--lockfile", help="Validate against a lockfile")
    validate_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    validate_parser.set_defaults(func=cmd_validate)

    lock_parser = subparsers.add_parser("lock", help="Generate a lockfile from a manifest")
    lock_parser.add_argument("-f", "--file", default="skills.yml")
    lock_parser.add_argument(
        "-o",
        "--output",
        default="skillsible.lock",
        help="Lockfile output path (default: skillsible.lock)",
    )
    lock_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    lock_parser.set_defaults(func=cmd_lock)

    diff_parser = subparsers.add_parser("diff", help="Compare a manifest against a lockfile")
    diff_parser.add_argument("-f", "--file", default="skills.yml")
    diff_parser.add_argument(
        "-l",
        "--lockfile",
        default="skillsible.lock",
        help="Lockfile path to compare against",
    )
    diff_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    diff_parser.set_defaults(func=cmd_diff)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect what Codex and Claude currently discover",
    )
    inspect_parser.add_argument(
        "--agent",
        action="append",
        choices=["codex", "claude-code"],
        help="Agent to inspect (default: inspect both codex and claude-code)",
    )
    inspect_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    inspect_parser.set_defaults(func=cmd_inspect)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "inspect" and not args.agent:
        args.agent = ["codex", "claude-code"]
    try:
        return args.func(args)
    except (ManifestError, AdapterError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
