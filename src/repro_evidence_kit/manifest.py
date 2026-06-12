from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

MANIFEST_VERSION = "1.0"


def normalize_manifest_path(path: object) -> str:
    """Return the manifest's portable logical path form."""
    return str(path).replace("\\", "/")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        symlink_dirs = [current / name for name in dirnames if (current / name).is_symlink()]
        symlink_files = [current / name for name in filenames if (current / name).is_symlink()]
        symlinks = symlink_dirs + symlink_files
        if symlinks:
            raise ValueError(f"manifest input contains symlink: {symlinks[0]}")
        dirnames[:] = sorted(d for d in dirnames if d not in {".git", "__pycache__"})
        for name in sorted(filenames):
            yield Path(dirpath) / name


def normalize_filter_patterns(patterns: Sequence[str] | None) -> list[str]:
    if not patterns:
        return []
    return sorted({normalize_manifest_path(pattern.strip()) for pattern in patterns if pattern.strip()})


def path_matches_filter(path: str, pattern: str) -> bool:
    pattern = normalize_manifest_path(pattern)
    return path == pattern or path.startswith(f"{pattern.rstrip('/')}/") or fnmatch.fnmatchcase(path, pattern)


def path_selected(path: str, *, include: Sequence[str], exclude: Sequence[str]) -> bool:
    if include and not any(path_matches_filter(path, pattern) for pattern in include):
        return False
    if exclude and any(path_matches_filter(path, pattern) for pattern in exclude):
        return False
    return True


def create_manifest(
    root: Path,
    *,
    include_mtime: bool = False,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> dict[str, Any]:
    if not root.exists():
        raise ValueError(f"manifest input does not exist: {root}")
    if root.is_symlink():
        raise ValueError(f"manifest input must not be a symlink: {root}")
    if not root.is_file() and not root.is_dir():
        raise ValueError(f"manifest input must be a file or directory: {root}")
    root = root.resolve()
    include_patterns = normalize_filter_patterns(include)
    exclude_patterns = normalize_filter_patterns(exclude)
    entries: list[dict[str, Any]] = []
    for file_path in iter_files(root):
        rel = normalize_manifest_path(file_path.resolve().relative_to(root if root.is_dir() else root.parent).as_posix())
        if not path_selected(rel, include=include_patterns, exclude=exclude_patterns):
            continue
        st = file_path.stat()
        item: dict[str, Any] = {
            "path": rel,
            "size": st.st_size,
            "sha256": sha256_file(file_path),
        }
        if include_mtime:
            item["mtime_ns"] = st.st_mtime_ns
        entries.append(item)
    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root_name": root.name,
        "file_count": len(entries),
        "total_bytes": sum(e["size"] for e in entries),
        "files": entries,
    }
    if include_patterns or exclude_patterns:
        manifest["filters"] = {
            "include": include_patterns,
            "exclude": exclude_patterns,
            "order": "include_then_exclude",
            "pattern_syntax": "POSIX-style manifest-relative glob or subtree path",
        }
    return manifest


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def write_json(data: Any, path: Path | None) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if path is None:
        print(text, end="")
    else:
        atomic_write_text(text, path)


def write_text(text: str, path: Path | None) -> None:
    if path is None:
        print(text, end="")
    else:
        atomic_write_text(text, path)


def atomic_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    temp_path = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        if existing_mode is not None:
            os.chmod(temp_path, existing_mode)
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


@dataclass(frozen=True)
class ManifestDiff:
    added: list[str]
    removed: list[str]
    changed: list[str]
    unchanged: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "added": len(self.added),
                "removed": len(self.removed),
                "changed": len(self.changed),
                "unchanged": len(self.unchanged),
            },
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "unchanged": self.unchanged,
        }

    def as_markdown(self) -> str:
        lines = [
            "# Manifest diff",
            "",
            "## Summary",
            "",
            "| Status | Count |",
            "| --- | ---: |",
            f"| Added | {len(self.added)} |",
            f"| Removed | {len(self.removed)} |",
            f"| Changed | {len(self.changed)} |",
            f"| Unchanged | {len(self.unchanged)} |",
            "",
        ]
        for title, paths in (
            ("Added", self.added),
            ("Removed", self.removed),
            ("Changed", self.changed),
            ("Unchanged", self.unchanged),
        ):
            lines.extend([f"## {title}", ""])
            if paths:
                lines.extend(f"- `{path}`" for path in paths)
            else:
                lines.append("_None._")
            lines.append("")
        return "\n".join(lines) + "\n"


def diff_manifests(before: dict[str, Any], after: dict[str, Any]) -> ManifestDiff:
    before_files = {normalize_manifest_path(item["path"]): item for item in before.get("files", [])}
    after_files = {normalize_manifest_path(item["path"]): item for item in after.get("files", [])}
    before_paths = set(before_files)
    after_paths = set(after_files)
    added = sorted(after_paths - before_paths)
    removed = sorted(before_paths - after_paths)
    shared = sorted(before_paths & after_paths)
    changed = [p for p in shared if before_files[p].get("sha256") != after_files[p].get("sha256") or before_files[p].get("size") != after_files[p].get("size")]
    unchanged = [p for p in shared if p not in changed]
    return ManifestDiff(added=added, removed=removed, changed=changed, unchanged=unchanged)
