from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

REQUIRED_TOP_LEVEL = {"schema_version", "title", "inputs", "commands", "outputs"}
REQUIRED_ARTIFACT_FIELDS = {"path", "sha256"}


def load_evidence(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML evidence files require PyYAML")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("evidence bundle must be a mapping/object")
    return data


def validate_evidence_bundle(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    for key in missing:
        errors.append(f"missing top-level field: {key}")
    for key in ["inputs", "outputs"]:
        value = data.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            errors.append(f"{key} must be a list")
            continue
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"{key}[{i}] must be an object")
                continue
            for required in sorted(REQUIRED_ARTIFACT_FIELDS - set(item)):
                errors.append(f"{key}[{i}] missing field: {required}")
    commands = data.get("commands")
    if commands is not None:
        if not isinstance(commands, list):
            errors.append("commands must be a list")
        else:
            for i, item in enumerate(commands):
                if not isinstance(item, dict):
                    errors.append(f"commands[{i}] must be an object")
                elif "argv" not in item and "command" not in item:
                    errors.append(f"commands[{i}] missing field: argv or command")
    return {"ok": not errors, "errors": errors}
