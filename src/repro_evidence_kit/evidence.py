from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from importlib import import_module, resources
from pathlib import Path
from typing import Any

try:
    yaml: Any = import_module("yaml")
except ImportError:  # pragma: no cover
    yaml = None

try:
    Draft202012Validator: Any = import_module("jsonschema").Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None

REPO_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "evidence-bundle.schema.json"
REPO_SIGNATURE_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "signature-sidecar.schema.json"

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


def validate_evidence_bundle_schema(data: dict[str, Any], schema_path: Path | None = None) -> dict[str, Any]:
    if Draft202012Validator is None:
        raise ValueError("schema validation requires the optional 'jsonschema' dependency; install repro-evidence-kit[schema]")
    schema_file = schema_path or default_schema_path()
    schema = load_json_schema(schema_file)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    return {
        "ok": not errors,
        "errors": [format_schema_error(error) for error in errors],
        "validator": "jsonschema Draft 2020-12",
        "schema_path": str(schema_file),
    }


def default_schema_path() -> Path:
    if REPO_SCHEMA_PATH.exists():
        return REPO_SCHEMA_PATH
    return Path(str(resources.files("repro_evidence_kit.schemas") / "evidence-bundle.schema.json"))


def default_signature_schema_path() -> Path:
    if REPO_SIGNATURE_SCHEMA_PATH.exists():
        return REPO_SIGNATURE_SCHEMA_PATH
    return Path(str(resources.files("repro_evidence_kit.schemas") / "signature-sidecar.schema.json"))


def validate_signature_sidecar_schema(data: dict[str, Any], schema_path: Path | None = None) -> dict[str, Any]:
    if Draft202012Validator is None:
        raise ValueError("schema validation requires the optional 'jsonschema' dependency; install repro-evidence-kit[schema]")
    schema_file = schema_path or default_signature_schema_path()
    schema = load_json_schema(schema_file)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    return {
        "ok": not errors,
        "errors": [format_schema_error(error) for error in errors],
        "validator": "jsonschema Draft 2020-12",
        "schema_path": str(schema_file),
    }


def load_json_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    if not isinstance(schema, dict):
        raise ValueError(f"schema must be a JSON object: {path}")
    return schema


def format_schema_error(error: Any) -> str:
    location = "/".join(str(part) for part in error.path)
    if not location:
        location = "<root>"
    return f"{location}: {error.message}"


def evidence_result_as_junit(result: dict[str, Any], *, name: str = "evidence-validate") -> str:
    ok = bool(result.get("ok"))
    suite = ET.Element(
        "testsuite",
        {
            "name": f"repro-evidence {name}",
            "tests": "1",
            "failures": "0" if ok else "1",
            "errors": "0",
        },
    )
    case = ET.SubElement(suite, "testcase", {"classname": "repro_evidence_kit.evidence", "name": name})
    if not ok:
        failure = ET.SubElement(case, "failure", {"message": "evidence validation failed"})
        failure.text = json.dumps(result.get("errors", []), indent=2, sort_keys=True)
    return ET.tostring(suite, encoding="unicode") + "\n"
