from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .evidence import evidence_result_as_junit, load_evidence, validate_evidence_bundle, validate_evidence_bundle_schema, validate_signature_sidecar_schema
from .manifest import create_manifest, diff_manifests, load_manifest, write_json, write_text
from .signing import load_signature_sidecar, sign_bundle, signature_verification_as_text, verify_bundle_signature
from .verify import sandbox_result_as_junit, sandbox_result_as_sarif, verify_sandbox_output


def _csv_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def _csv_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [part.strip() for value in values for part in value.split(",") if part.strip()]


def _ensure_output_does_not_overwrite_input(output: Path | None, *inputs: Path | None) -> None:
    if output is None:
        return
    output_path = output.resolve()
    for input_path in inputs:
        if input_path is not None and output_path == input_path.resolve():
            raise ValueError(f"output must not overwrite input file: {input_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repro-evidence", description="Reproducible artifact manifest and evidence-bundle tools.")
    parser.add_argument("--version", action="version", version=f"repro-evidence {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="Create or compare file manifests")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    create = manifest_sub.add_parser("create", help="Create a JSON manifest for a file or directory")
    create.add_argument("path", type=Path)
    create.add_argument("-o", "--output", type=Path)
    create.add_argument("--include-mtime", action="store_true")
    create.add_argument("--include", action="append", help="Manifest-relative glob or subtree path to include; may be repeated or comma-separated")
    create.add_argument("--exclude", action="append", help="Manifest-relative glob or subtree path to exclude after includes; may be repeated or comma-separated")
    create.add_argument("--allow-empty", action="store_true", help="Allow filters to select zero files instead of failing")

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
    sandbox.add_argument("--require-added", help="Comma-separated paths that must be added")
    sandbox.add_argument("--require-changed", help="Comma-separated paths that must be changed")
    sandbox.add_argument("--require-removed", help="Comma-separated paths that must be removed")
    sandbox.add_argument("--format", choices=("json", "junit", "sarif"), default="json")
    sandbox.add_argument("-o", "--output", type=Path)

    evidence = sub.add_parser("evidence", help="Validate and sign evidence bundles")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    val = evidence_sub.add_parser("validate", help="Validate an evidence bundle YAML/JSON file")
    val.add_argument("bundle", type=Path)
    val.add_argument("--schema", action="store_true", help="Validate with schemas/evidence-bundle.schema.json using the optional jsonschema dependency")
    val.add_argument("--schema-path", type=Path, help="Use a custom JSON Schema path with --schema")
    val.add_argument("--format", choices=("json", "junit"), default="json")
    val.add_argument("-o", "--output", type=Path)

    sign = evidence_sub.add_parser("sign", help="Sign exact evidence bundle bytes with a local key")
    sign.add_argument("bundle", type=Path)
    sign.add_argument("--key", required=True, type=Path, help="Local synthetic or trusted HMAC key file")
    sign.add_argument("--key-hint", help="Non-secret key identifier to record in the sidecar")
    sign.add_argument("-o", "--output", type=Path)
    sign.add_argument("--dry-run", action="store_true", help="Print the sidecar that would be written without creating an output file")

    verify_sig = evidence_sub.add_parser("verify-signature", help="Verify an evidence bundle signature sidecar")
    verify_sig.add_argument("bundle", type=Path)
    verify_sig.add_argument("--signature", required=True, type=Path, help="Signature sidecar JSON")
    verify_sig.add_argument("--key", required=True, type=Path, help="Local synthetic or trusted HMAC key file")
    verify_sig.add_argument("--format", choices=("json", "text"), default="json")
    verify_sig.add_argument("--schema", action="store_true", help="Also validate the signature sidecar shape with schemas/signature-sidecar.schema.json")
    verify_sig.add_argument("--schema-path", type=Path, help="Use a custom JSON Schema path with --schema")
    verify_sig.add_argument("-o", "--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "manifest" and args.manifest_command == "create":
            _ensure_output_does_not_overwrite_input(args.output, args.path)
            write_json(
                create_manifest(
                    args.path,
                    include_mtime=args.include_mtime,
                    include=_csv_list(args.include),
                    exclude=_csv_list(args.exclude),
                    allow_empty=args.allow_empty,
                ),
                args.output,
            )
            return 0
        if args.command == "manifest" and args.manifest_command == "diff":
            _ensure_output_does_not_overwrite_input(args.output, args.before, args.after)
            manifest_diff = diff_manifests(load_manifest(args.before), load_manifest(args.after))
            if args.format == "markdown":
                write_text(manifest_diff.as_markdown(), args.output)
            else:
                write_json(manifest_diff.as_dict(), args.output)
            return 0
        if args.command == "verify" and args.verify_command == "sandbox-run":
            _ensure_output_does_not_overwrite_input(args.output, args.before, args.after)
            sandbox_result = verify_sandbox_output(
                load_manifest(args.before),
                load_manifest(args.after),
                allow_added=_csv_set(args.allow_added),
                allow_changed=_csv_set(args.allow_changed),
                allow_removed=_csv_set(args.allow_removed),
                require_added=_csv_set(args.require_added),
                require_changed=_csv_set(args.require_changed),
                require_removed=_csv_set(args.require_removed),
            )
            if args.format == "junit":
                write_text(sandbox_result_as_junit(sandbox_result), args.output)
            elif args.format == "sarif":
                write_text(sandbox_result_as_sarif(sandbox_result), args.output)
            else:
                write_json(sandbox_result, args.output)
            return 0 if sandbox_result["ok"] else 1
        if args.command == "evidence" and args.evidence_command == "validate":
            _ensure_output_does_not_overwrite_input(args.output, args.bundle, args.schema_path)
            bundle = load_evidence(args.bundle)
            evidence_result = validate_evidence_bundle_schema(bundle, args.schema_path) if args.schema else validate_evidence_bundle(bundle)
            if args.format == "junit":
                write_text(evidence_result_as_junit(evidence_result), args.output)
            else:
                write_json(evidence_result, args.output)
            return 0 if evidence_result["ok"] else 1
        if args.command == "evidence" and args.evidence_command == "sign":
            if args.dry_run:
                sidecar = sign_bundle(args.bundle, args.key, key_hint=args.key_hint)
                write_json(sidecar, None)
                return 0
            if args.output is None:
                raise ValueError("evidence sign requires -o/--output unless --dry-run is used")
            _ensure_output_does_not_overwrite_input(args.output, args.bundle, args.key)
            sidecar = sign_bundle(args.bundle, args.key, key_hint=args.key_hint)
            write_json(sidecar, args.output)
            return 0
        if args.command == "evidence" and args.evidence_command == "verify-signature":
            _ensure_output_does_not_overwrite_input(
                args.output,
                args.bundle,
                args.signature,
                args.key,
                args.schema_path,
            )
            sidecar = load_signature_sidecar(args.signature)
            signature_result = verify_bundle_signature(args.bundle, sidecar, args.key)
            if args.schema:
                schema_result = validate_signature_sidecar_schema(sidecar, args.schema_path)
                signature_result["schema"] = schema_result
                signature_result["ok"] = bool(signature_result["ok"] and schema_result["ok"])
            if args.format == "text":
                write_text(signature_verification_as_text(signature_result), args.output)
            else:
                write_json(signature_result, args.output)
            return 0 if signature_result["ok"] else 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
