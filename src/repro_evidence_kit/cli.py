from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .evidence import load_evidence, validate_evidence_bundle, validate_evidence_bundle_schema
from .manifest import create_manifest, diff_manifests, load_json, write_json, write_text
from .verify import verify_sandbox_output


def _csv_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def _csv_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [part.strip() for value in values for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repro-evidence", description="Reproducible artifact manifest and evidence-bundle tools.")
    parser.add_argument("--version", action="version", version="repro-evidence 0.1.1")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="Create or compare file manifests")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    create = manifest_sub.add_parser("create", help="Create a JSON manifest for a file or directory")
    create.add_argument("path", type=Path)
    create.add_argument("-o", "--output", type=Path)
    create.add_argument("--include-mtime", action="store_true")
    create.add_argument("--include", action="append", help="Manifest-relative glob or subtree path to include; may be repeated or comma-separated")
    create.add_argument("--exclude", action="append", help="Manifest-relative glob or subtree path to exclude after includes; may be repeated or comma-separated")

    diff = manifest_sub.add_parser("diff", help="Compare two JSON manifests")
    diff.add_argument("before", type=Path)
    diff.add_argument("after", type=Path)
    diff.add_argument("--format", choices=("json", "markdown"), default="json")
    diff.add_argument("-o", "--output", type=Path)

    verify = sub.add_parser("verify", help="Verify experiment/sandbox outputs")
    verify_sub = verify.add_subparsers(dest="verify_command", required=True)
    sandbox = verify_sub.add_parser("sandbox-run", help="Verify that only allowed paths changed between two manifests")
    sandbox.add_argument("before", type=Path)
    sandbox.add_argument("after", type=Path)
    sandbox.add_argument("--allow-added", help="Comma-separated path allowlist")
    sandbox.add_argument("--allow-changed", help="Comma-separated path allowlist")
    sandbox.add_argument("--allow-removed", help="Comma-separated path allowlist")
    sandbox.add_argument("-o", "--output", type=Path)

    evidence = sub.add_parser("evidence", help="Validate evidence bundles")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    val = evidence_sub.add_parser("validate", help="Validate an evidence bundle YAML/JSON file")
    val.add_argument("bundle", type=Path)
    val.add_argument("--schema", action="store_true", help="Validate with schemas/evidence-bundle.schema.json using the optional jsonschema dependency")
    val.add_argument("--schema-path", type=Path, help="Use a custom JSON Schema path with --schema")
    val.add_argument("-o", "--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "manifest" and args.manifest_command == "create":
            write_json(
                create_manifest(
                    args.path,
                    include_mtime=args.include_mtime,
                    include=_csv_list(args.include),
                    exclude=_csv_list(args.exclude),
                ),
                args.output,
            )
            return 0
        if args.command == "manifest" and args.manifest_command == "diff":
            result = diff_manifests(load_json(args.before), load_json(args.after))
            if args.format == "markdown":
                write_text(result.as_markdown(), args.output)
            else:
                write_json(result.as_dict(), args.output)
            return 0
        if args.command == "verify" and args.verify_command == "sandbox-run":
            result = verify_sandbox_output(
                load_json(args.before),
                load_json(args.after),
                allow_added=_csv_set(args.allow_added),
                allow_changed=_csv_set(args.allow_changed),
                allow_removed=_csv_set(args.allow_removed),
            )
            write_json(result, args.output)
            return 0 if result["ok"] else 1
        if args.command == "evidence" and args.evidence_command == "validate":
            bundle = load_evidence(args.bundle)
            result = validate_evidence_bundle_schema(bundle, args.schema_path) if args.schema else validate_evidence_bundle(bundle)
            write_json(result, args.output)
            return 0 if result["ok"] else 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
