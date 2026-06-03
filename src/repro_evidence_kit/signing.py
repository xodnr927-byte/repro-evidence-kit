from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

SIGNATURE_VERSION = "1.0"
ALGORITHM = "hmac-sha256"


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
    payload = bundle_path.read_bytes()
    key = load_key(key_path)
    signature = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return {
        "signature_version": SIGNATURE_VERSION,
        "payload_path": bundle_path.name,
        "payload_sha256": sha256_bytes(payload),
        "algorithm": ALGORITHM,
        "key_hint": key_hint or key_path.name,
        "signature": signature,
    }


def verify_bundle_signature(bundle_path: Path, sidecar: dict[str, Any], key_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    if sidecar.get("signature_version") != SIGNATURE_VERSION:
        errors.append("unsupported signature_version")
    if sidecar.get("algorithm") != ALGORITHM:
        errors.append("unsupported algorithm")

    payload = bundle_path.read_bytes()
    payload_sha256 = sha256_bytes(payload)
    if sidecar.get("payload_sha256") != payload_sha256:
        errors.append("payload_sha256 mismatch")

    signature = sidecar.get("signature")
    if not isinstance(signature, str) or not signature:
        errors.append("missing signature")
    else:
        expected = hmac.new(load_key(key_path), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            errors.append("signature mismatch")

    return {
        "ok": not errors,
        "errors": errors,
        "algorithm": sidecar.get("algorithm"),
        "payload_sha256": payload_sha256,
        "key_hint": sidecar.get("key_hint"),
    }
