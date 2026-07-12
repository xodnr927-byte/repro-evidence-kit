from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module, resources
from pathlib import Path
from typing import Any, Mapping

try:
    yaml: Any = import_module("yaml")
except ImportError:  # pragma: no cover - PyYAML is a runtime dependency
    yaml = None


POLICY_VERSION = "1.0"
SUPPORTED_ALGORITHM = "hmac-sha256"
SUPPORTED_STATES = frozenset({"active", "verify_only", "revoked"})
SUPPORTED_RESOLVERS = frozenset({"env", "file"})
_TOP_LEVEL_FIELDS = frozenset({"policy_version", "policy_id", "keys"})
_KEY_FIELDS = frozenset({"key_id", "algorithm", "key_ref", "state", "not_before", "revoked_at", "comment"})
_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_HEX_OR_BASE64_LIKE = re.compile(r"[A-Za-z0-9+/=_-]{32,}\Z")

REPO_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "trust-policy.schema.json"


class _DuplicateMappingKey(ValueError):
    def __init__(self, key: Any) -> None:
        self.key = key
        super().__init__(f"duplicate mapping key: {key!r}")


class _InvalidMappingKey(ValueError):
    pass


class TrustPolicyError(ValueError):
    """Fail-closed policy parsing/validation error with stable detail codes."""

    def __init__(self, code: str, message: str, *, details: list[dict[str, str]] | None = None) -> None:
        self.code = code
        self.details = tuple(details or ({"code": code, "path": "<root>", "message": message},))
        rendered = "; ".join(f"{item['path']}: {item['message']}" for item in self.details)
        super().__init__(f"{code}: {rendered}")


@dataclass(frozen=True)
class TrustPolicyKey:
    key_id: str
    algorithm: str
    key_ref: str
    state: str
    not_before: datetime
    revoked_at: datetime | None = None
    comment: str | None = None


@dataclass(frozen=True)
class TrustPolicy:
    policy_version: str
    policy_id: str
    keys: tuple[TrustPolicyKey, ...]

    def key_by_id(self, key_id: str) -> TrustPolicyKey | None:
        """Return a parsed key record without resolving or authorizing it."""
        return next((key for key in self.keys if key.key_id == key_id), None)


def _duplicate_json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateMappingKey(key)
        result[key] = value
    return result


if yaml is not None:  # pragma: no branch - selected by the installed dependency
    class _UniqueSafeLoader(yaml.SafeLoader):
        pass


    def _construct_unique_mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
        result: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                duplicate = key in result
            except TypeError as exc:
                raise _InvalidMappingKey("mapping keys must be hashable") from exc
            if duplicate:
                raise _DuplicateMappingKey(key)
            result[key] = loader.construct_object(value_node, deep=deep)
        return result


    _UniqueSafeLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        _construct_unique_mapping,
    )


def _detail(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _raise_invalid(details: list[dict[str, str]]) -> None:
    if details:
        raise TrustPolicyError("policy_invalid", "policy validation failed", details=details)


def _require_string(value: Any, path: str, details: list[dict[str, str]], *, identifier: bool = False) -> str | None:
    if not isinstance(value, str):
        details.append(_detail("invalid_type", path, "must be a string"))
        return None
    if not value or not value.strip():
        details.append(_detail("empty_value", path, "must not be empty"))
        return None
    if value != value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
        details.append(_detail("invalid_value", path, "must not contain surrounding whitespace or control characters"))
        return None
    if identifier and any(char.isspace() for char in value):
        details.append(_detail("invalid_identifier", path, "must not contain whitespace"))
        return None
    return value


def _parse_timestamp(value: Any, path: str, details: list[dict[str, str]]) -> datetime | None:
    text = _require_string(value, path, details)
    if text is None:
        return None
    normalized = f"{text[:-1]}+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        details.append(_detail("invalid_timestamp", path, "must be an ISO-8601 timestamp with an explicit timezone"))
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        details.append(_detail("invalid_timestamp", path, "must include an explicit timezone"))
        return None
    return parsed.astimezone(timezone.utc)


def _validate_key_ref(value: Any, path: str, details: list[dict[str, str]]) -> str | None:
    text = _require_string(value, path, details)
    if text is None:
        return None
    if re.fullmatch(r"(?:raw|hex|base64|literal|secret):.*", text, re.IGNORECASE) or _HEX_OR_BASE64_LIKE.fullmatch(text):
        details.append(_detail("embedded_key_material", path, "must contain a non-secret env: or file: reference, not key bytes"))
        return None
    scheme, separator, reference = text.partition(":")
    if not separator or scheme not in SUPPORTED_RESOLVERS:
        details.append(_detail("unsupported_resolver", path, "must use the env: or file: resolver scheme"))
        return None
    if scheme == "env" and _ENV_NAME.fullmatch(reference) is None:
        details.append(_detail("invalid_key_reference", path, "env: references must contain one environment-variable name"))
        return None
    if scheme == "file" and (not reference or reference.startswith("//")):
        details.append(_detail("invalid_key_reference", path, "file: references must contain a local path, not a remote URL"))
        return None
    return text


def _parse_document(text: str, suffix: str) -> Any:
    try:
        if suffix in {".yaml", ".yml"}:
            if yaml is None:
                raise TrustPolicyError("policy_parse_error", "YAML policy files require PyYAML")
            return yaml.load(text, Loader=_UniqueSafeLoader)
        if suffix == ".json":
            return json.loads(text, object_pairs_hook=_duplicate_json_pairs)
        raise TrustPolicyError("unsupported_policy_format", "policy path must use .json, .yaml, or .yml")
    except _DuplicateMappingKey as exc:
        raise TrustPolicyError(
            "policy_parse_error",
            "duplicate mapping keys are not allowed",
            details=[_detail("duplicate_mapping_key", "<document>", str(exc))],
        ) from exc
    except _InvalidMappingKey as exc:
        raise TrustPolicyError(
            "policy_parse_error",
            "policy document could not be parsed",
            details=[_detail("invalid_mapping_key", "<document>", str(exc))],
        ) from exc
    except TrustPolicyError:
        raise
    except (json.JSONDecodeError, yaml.YAMLError if yaml is not None else ValueError) as exc:
        raise TrustPolicyError(
            "policy_parse_error",
            "policy document could not be parsed",
            details=[_detail("malformed_document", "<document>", str(exc))],
        ) from exc


def parse_trust_policy(data: Mapping[str, Any]) -> TrustPolicy:
    """Validate a policy mapping without resolving keys or changing runtime behavior."""
    details: list[dict[str, str]] = []
    if not isinstance(data, Mapping):
        raise TrustPolicyError("policy_invalid", "policy must be a mapping/object")

    unknown = sorted((str(key) for key in data if key not in _TOP_LEVEL_FIELDS))
    details.extend(_detail("unknown_field", key, "unknown top-level field") for key in unknown)
    for field in sorted(_TOP_LEVEL_FIELDS - set(data)):
        details.append(_detail("missing_field", field, "required top-level field is missing"))

    policy_version = _require_string(data.get("policy_version"), "policy_version", details)
    if policy_version is not None and policy_version != POLICY_VERSION:
        details.append(_detail("policy_version_unsupported", "policy_version", f"must equal {POLICY_VERSION!r}"))
    policy_id = _require_string(data.get("policy_id"), "policy_id", details, identifier=True)
    raw_keys = data.get("keys")
    if not isinstance(raw_keys, list):
        details.append(_detail("invalid_type", "keys", "must be a non-empty list"))
        raw_keys = []
    elif not raw_keys:
        details.append(_detail("empty_value", "keys", "must contain at least one key record"))

    parsed_keys: list[TrustPolicyKey] = []
    seen_key_ids: set[str] = set()
    for index, raw_key in enumerate(raw_keys):
        path = f"keys[{index}]"
        if not isinstance(raw_key, Mapping):
            details.append(_detail("invalid_type", path, "must be an object"))
            continue
        unknown_key_fields = sorted((str(key) for key in raw_key if key not in _KEY_FIELDS))
        details.extend(_detail("unknown_field", f"{path}.{key}", "unknown key field") for key in unknown_key_fields)
        for field in sorted({"key_id", "algorithm", "key_ref", "state", "not_before"} - set(raw_key)):
            details.append(_detail("missing_field", f"{path}.{field}", "required key field is missing"))

        key_id = _require_string(raw_key.get("key_id"), f"{path}.key_id", details, identifier=True)
        if key_id is not None:
            if key_id in seen_key_ids:
                details.append(_detail("duplicate_key_id", f"{path}.key_id", f"duplicate key_id {key_id!r}"))
            seen_key_ids.add(key_id)
        algorithm = _require_string(raw_key.get("algorithm"), f"{path}.algorithm", details)
        if algorithm is not None and algorithm != SUPPORTED_ALGORITHM:
            details.append(_detail("unsupported_algorithm", f"{path}.algorithm", f"must equal {SUPPORTED_ALGORITHM!r}"))
        key_ref = _validate_key_ref(raw_key.get("key_ref"), f"{path}.key_ref", details)
        state = _require_string(raw_key.get("state"), f"{path}.state", details)
        if state is not None and state not in SUPPORTED_STATES:
            details.append(_detail("unsupported_state", f"{path}.state", "must be active, verify_only, or revoked"))
        not_before = _parse_timestamp(raw_key.get("not_before"), f"{path}.not_before", details)
        revoked_at = None
        if "revoked_at" in raw_key:
            revoked_at = _parse_timestamp(raw_key["revoked_at"], f"{path}.revoked_at", details)
        comment = None
        if "comment" in raw_key:
            comment = _require_string(raw_key["comment"], f"{path}.comment", details)

        if revoked_at is not None and state is not None and state != "revoked":
            details.append(_detail("timestamp_conflict", f"{path}.revoked_at", "revoked_at requires state: revoked"))
        if revoked_at is not None and not_before is not None and revoked_at < not_before:
            details.append(_detail("timestamp_conflict", f"{path}.revoked_at", "must not be earlier than not_before"))
        if (
            key_id is not None
            and algorithm is not None
            and key_ref is not None
            and state is not None
            and not_before is not None
            and state in SUPPORTED_STATES
            and algorithm == SUPPORTED_ALGORITHM
        ):
            parsed_keys.append(
                TrustPolicyKey(
                    key_id=key_id,
                    algorithm=algorithm,
                    key_ref=key_ref,
                    state=state,
                    not_before=not_before,
                    revoked_at=revoked_at,
                    comment=comment,
                )
            )

    _raise_invalid(details)
    assert policy_version is not None and policy_id is not None
    return TrustPolicy(policy_version=policy_version, policy_id=policy_id, keys=tuple(parsed_keys))


def load_trust_policy(path: Path) -> TrustPolicy:
    """Load and validate a local JSON/YAML policy document."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TrustPolicyError("policy_parse_error", f"could not read policy: {path}") from exc
    data = _parse_document(text, path.suffix.lower())
    if not isinstance(data, Mapping):
        raise TrustPolicyError("policy_invalid", "policy must be a mapping/object")
    return parse_trust_policy(data)


def default_trust_policy_schema_path() -> Path:
    if REPO_SCHEMA_PATH.exists():
        return REPO_SCHEMA_PATH
    return Path(str(resources.files("repro_evidence_kit.schemas") / "trust-policy.schema.json"))
