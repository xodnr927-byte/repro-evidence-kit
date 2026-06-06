from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any

from .manifest import diff_manifests, normalize_manifest_path


def verify_sandbox_output(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    allow_added: set[str] | None = None,
    allow_changed: set[str] | None = None,
    allow_removed: set[str] | None = None,
    require_added: set[str] | None = None,
    require_changed: set[str] | None = None,
    require_removed: set[str] | None = None,
) -> dict[str, Any]:
    allow_added = {normalize_manifest_path(path) for path in (allow_added or set())}
    allow_changed = {normalize_manifest_path(path) for path in (allow_changed or set())}
    allow_removed = {normalize_manifest_path(path) for path in (allow_removed or set())}
    require_added = {normalize_manifest_path(path) for path in (require_added or set())}
    require_changed = {normalize_manifest_path(path) for path in (require_changed or set())}
    require_removed = {normalize_manifest_path(path) for path in (require_removed or set())}
    diff = diff_manifests(before, after).as_dict()
    unexpected_added = sorted(set(diff["added"]) - allow_added)
    unexpected_changed = sorted(set(diff["changed"]) - allow_changed)
    unexpected_removed = sorted(set(diff["removed"]) - allow_removed)
    missing_required_added = sorted(require_added - set(diff["added"]))
    missing_required_changed = sorted(require_changed - set(diff["changed"]))
    missing_required_removed = sorted(require_removed - set(diff["removed"]))
    ok = not (unexpected_added or unexpected_changed or unexpected_removed or missing_required_added or missing_required_changed or missing_required_removed)
    return {
        "ok": ok,
        "diff_summary": diff["summary"],
        "unexpected": {
            "added": unexpected_added,
            "changed": unexpected_changed,
            "removed": unexpected_removed,
        },
        "allowed": {
            "added": sorted(allow_added),
            "changed": sorted(allow_changed),
            "removed": sorted(allow_removed),
        },
        "required": {
            "added": sorted(require_added),
            "changed": sorted(require_changed),
            "removed": sorted(require_removed),
        },
        "missing_required": {
            "added": missing_required_added,
            "changed": missing_required_changed,
            "removed": missing_required_removed,
        },
    }


def sandbox_result_as_junit(result: dict[str, Any]) -> str:
    """Render a sandbox verification result as a minimal JUnit XML report."""
    ok = bool(result.get("ok"))
    suite = ET.Element(
        "testsuite",
        {
            "name": "repro-evidence sandbox-run",
            "tests": "1",
            "failures": "0" if ok else "1",
            "errors": "0",
        },
    )
    case = ET.SubElement(suite, "testcase", {"classname": "repro_evidence_kit.verify", "name": "sandbox-run"})
    if not ok:
        failure = ET.SubElement(case, "failure", {"message": "sandbox output predicate failed"})
        failure.text = json.dumps(
            {
                "unexpected": result.get("unexpected", {}),
                "missing_required": result.get("missing_required", {}),
            },
            indent=2,
            sort_keys=True,
        )
    return ET.tostring(suite, encoding="unicode") + "\n"


def sandbox_result_as_sarif(result: dict[str, Any]) -> str:
    """Render sandbox verification failures as a minimal SARIF log."""
    rules = [
        {
            "id": "unexpected-sandbox-change",
            "name": "Unexpected sandbox output change",
            "shortDescription": {"text": "Sandbox output changed outside the allowlist."},
            "help": {"text": "Add intentional outputs to the allowlist or remove unexpected artifacts."},
        },
        {
            "id": "missing-required-sandbox-change",
            "name": "Missing required sandbox output change",
            "shortDescription": {"text": "A required sandbox output change was not observed."},
            "help": {"text": "Check the producer command or update the required output list."},
        },
    ]
    results: list[dict[str, Any]] = []
    for group, values in (result.get("unexpected") or {}).items():
        for path in values:
            results.append({
                "ruleId": "unexpected-sandbox-change",
                "level": "error",
                "message": {"text": f"Unexpected {group} path: {path}"},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": path}}}],
            })
    for group, values in (result.get("missing_required") or {}).items():
        for path in values:
            results.append({
                "ruleId": "missing-required-sandbox-change",
                "level": "error",
                "message": {"text": f"Missing required {group} path: {path}"},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": path}}}],
            })
    sarif = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {"name": "repro-evidence", "rules": rules}},
            "results": results,
        }],
    }
    return json.dumps(sarif, indent=2, sort_keys=True) + "\n"
