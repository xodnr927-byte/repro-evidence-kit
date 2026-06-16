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
_HEX64 = set("0123456789abcdefABCDEF")


def normalize_manifest_path(path: object) -> str:
    """Return the manifest's portable logical path form."""
    normalized = str(path).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


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
    normalized = {normalize_manifest_path(pattern.strip()) for pattern in patterns if pattern.strip()}
    return sorted(pattern for pattern in normalized if pattern)


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
    allow_empty: bool = False,
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
    filters_requested = bool(include_patterns or exclude_patterns)
    if filters_requested and not entries and not allow_empty:
        raise ValueError("manifest filters selected no files; use --allow-empty to write an empty filtered manifest")
    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root_name": root.name,
        "file_count": len(entries),
        "total_bytes": sum(e["size"] for e in entries),
        "files": entries,
    }
    if filters_requested:
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


def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    files = data.get("files")
    if not isinstance(files, list):
        return ["files must be a list"]

    seen: set[str] = set()
    total_bytes = 0
    for index, item in enumerate(files):
        prefix = f"files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue

        path = item.get("path")
        normalized_path: str | None = None
        if not isinstance(path, str) or not path:
            errors.append(f"{prefix}.path must be a non-empty string")
        else:
            normalized_path = normalize_manifest_path(path)
            if normalized_path in seen:
                errors.append(f"duplicate manifest path: {normalized_path}")
            seen.add(normalized_path)

        size = item.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"{prefix}.size must be a non-negative integer")
        else:
            total_bytes += size

        sha256 = item.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64 or any(char not in _HEX64 for char in sha256):
            errors.append(f"{prefix}.sha256 must be 64 hexadecimal characters")

    manifest_version = data.get("manifest_version")
    if manifest_version is not None and manifest_version != MANIFEST_VERSION:
        errors.append(f"unsupported manifest_version: {manifest_version}")
    file_count = data.get("file_count")
    if file_count is not None and file_count != len(files):
        errors.append(f"file_count does not match files length: {file_count} != {len(files)}")
    recorded_total = data.get("total_bytes")
    if recorded_total is not None and recorded_total != total_bytes:
        errors.append(f"total_bytes does not match file sizes: {recorded_total} != {total_bytes}")
    return errors


def load_manifest(path: Path) -> dict[str, Any]:
    data = load_json(path)
    errors = validate_manifest(data)
    if errors:
        raise ValueError(f"invalid manifest {path}: {'; '.join(errors)}")
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
