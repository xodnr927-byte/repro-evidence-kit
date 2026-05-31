from __future__ import annotations

from typing import Any

from .manifest import diff_manifests, normalize_manifest_path


def verify_sandbox_output(before: dict[str, Any], after: dict[str, Any], *, allow_added: set[str] | None = None, allow_changed: set[str] | None = None, allow_removed: set[str] | None = None) -> dict[str, Any]:
    allow_added = {normalize_manifest_path(path) for path in (allow_added or set())}
    allow_changed = {normalize_manifest_path(path) for path in (allow_changed or set())}
    allow_removed = {normalize_manifest_path(path) for path in (allow_removed or set())}
    diff = diff_manifests(before, after).as_dict()
    unexpected_added = sorted(set(diff["added"]) - allow_added)
    unexpected_changed = sorted(set(diff["changed"]) - allow_changed)
    unexpected_removed = sorted(set(diff["removed"]) - allow_removed)
    ok = not (unexpected_added or unexpected_changed or unexpected_removed)
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
    }
