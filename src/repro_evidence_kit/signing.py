from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Any, Callable

SIGNATURE_VERSION = "1.0"
ALGORITHM = "hmac-sha256"
SIGNATURE_ERROR_MESSAGES = {
    "unsupported_signature_version": "unsupported signature_version",
    "unsupported_algorithm": "unsupported algorithm",
    "payload_hash_mismatch": "payload_sha256 mismatch",
    "signature_mismatch": "signature mismatch",
    "missing_signature": "missing signature",
    "invalid_signature": "invalid signature",
    "missing_payload_sha256": "missing payload_sha256",
    "invalid_payload_sha256": "invalid payload_sha256",
    "payload_path_mismatch": "payload_path mismatch",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_key(path: Path) -> bytes:
    key = path.read_bytes()
    if not key:
        raise ValueError(f"signing key is empty: {path}")
    return key


def load_signature_sidecar(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("signature sidecar must be a JSON object")
    return data


def sign_bundle(bundle_path: Path, key_path: Path, *, key_hint: str | None = None) -> dict[str, Any]:
    key = load_key(key_path)
    return sign_bundle_with_key(bundle_path, key, key_hint=key_hint or key_path.name)


def sign_bundle_with_key(bundle_path: Path, key: bytes, *, key_hint: str) -> dict[str, Any]:
    """Sign exact bundle bytes with already-resolved non-empty key material."""
    if not key:
        raise ValueError("signing key is empty")
    payload = bundle_path.read_bytes()
    signature = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return {
        "signature_version": SIGNATURE_VERSION,
        "payload_path": bundle_path.name,
        "payload_sha256": sha256_bytes(payload),
        "algorithm": ALGORITHM,
        "key_hint": key_hint,
        "signature": signature,
    }


def signature_error(code: str, *, field: str, expected: Any = None, actual: Any = None) -> dict[str, Any]:
    detail = {"code": code, "field": field, "message": SIGNATURE_ERROR_MESSAGES[code]}
    if expected is not None:
        detail["expected"] = expected
    if actual is not None:
        detail["actual"] = actual
    return detail


def _append_error(errors: list[str], details: list[dict[str, Any]], code: str, **kwargs: Any) -> None:
    errors.append(SIGNATURE_ERROR_MESSAGES[code])
    details.append(signature_error(code, **kwargs))


def verify_bundle_signature(bundle_path: Path, sidecar: dict[str, Any], key_path: Path) -> dict[str, Any]:
    return _verify_bundle_signature(bundle_path, sidecar, lambda: load_key(key_path))


def verify_bundle_signature_with_key(bundle_path: Path, sidecar: dict[str, Any], key: bytes) -> dict[str, Any]:
    """Verify exact bundle bytes with already-resolved non-empty key material."""
    if not key:
        raise ValueError("verification key is empty")
    return _verify_bundle_signature(bundle_path, sidecar, lambda: key)


def _verify_bundle_signature(bundle_path: Path, sidecar: dict[str, Any], load_verification_key: Callable[[], bytes]) -> dict[str, Any]:
    errors: list[str] = []
    details: list[dict[str, Any]] = []
    if sidecar.get("signature_version") != SIGNATURE_VERSION:
        _append_error(
            errors,
            details,
            "unsupported_signature_version",
            field="signature_version",
            expected=SIGNATURE_VERSION,
            actual=sidecar.get("signature_version"),
        )
    if sidecar.get("algorithm") != ALGORITHM:
        _append_error(errors, details, "unsupported_algorithm", field="algorithm", expected=ALGORITHM, actual=sidecar.get("algorithm"))

    payload = bundle_path.read_bytes()
    payload_sha256 = sha256_bytes(payload)
    recorded_payload_sha256 = sidecar.get("payload_sha256")
    if not isinstance(recorded_payload_sha256, str) or not recorded_payload_sha256:
        _append_error(errors, details, "missing_payload_sha256", field="payload_sha256", expected=payload_sha256, actual=recorded_payload_sha256)
    elif not _HEX64.match(recorded_payload_sha256):
        _append_error(errors, details, "invalid_payload_sha256", field="payload_sha256", expected="64 lowercase hex characters", actual=recorded_payload_sha256)
    elif recorded_payload_sha256 != payload_sha256:
        _append_error(errors, details, "payload_hash_mismatch", field="payload_sha256", expected=recorded_payload_sha256, actual=payload_sha256)

    payload_path = sidecar.get("payload_path")
    if isinstance(payload_path, str) and payload_path and payload_path != bundle_path.name:
        _append_error(errors, details, "payload_path_mismatch", field="payload_path", expected=bundle_path.name, actual=payload_path)

    signature = sidecar.get("signature")
    if not isinstance(signature, str) or not signature:
        _append_error(errors, details, "missing_signature", field="signature", expected="64 lowercase hex characters", actual=signature)
    elif not _HEX64.match(signature):
        _append_error(errors, details, "invalid_signature", field="signature", expected="64 lowercase hex characters", actual=signature)
    else:
        expected = hmac.new(load_verification_key(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            _append_error(errors, details, "signature_mismatch", field="signature", expected=expected, actual=signature)

    return {
        "ok": not errors,
        "errors": errors,
        "error_details": details,
        "algorithm": sidecar.get("algorithm"),
        "payload_path": sidecar.get("payload_path"),
        "payload_sha256": payload_sha256,
        "key_hint": sidecar.get("key_hint"),
    }


def signature_verification_as_text(result: dict[str, Any]) -> str:
    lines = ["signature verification: PASS" if result.get("ok") else "signature verification: FAIL"]
    if result.get("algorithm"):
        lines.append(f"algorithm: {result['algorithm']}")
    if result.get("key_hint"):
        lines.append(f"key_hint: {result['key_hint']}")
    if result.get("policy_id"):
        lines.append(f"policy_id: {result['policy_id']}")
    if result.get("key_id"):
        lines.append(f"key_id: {result['key_id']}")
    if result.get("policy_state"):
        lines.append(f"policy_state: {result['policy_state']}")
    if result.get("payload_path"):
        lines.append(f"payload_path: {result['payload_path']}")
    if result.get("payload_sha256"):
        lines.append(f"payload_sha256: {result['payload_sha256']}")
    details = result.get("error_details") or []
    if details:
        lines.append("errors:")
        for detail in details:
            field = detail.get("field", "<unknown>")
            code = detail.get("code", "unknown")
            message = detail.get("message", code)
            lines.append(f"- {code} ({field}): {message}")
    return "\n".join(lines) + "\n"
