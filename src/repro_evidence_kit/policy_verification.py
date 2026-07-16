from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .key_resolver import EnvironmentKeyResolver, FileKeyResolver, KeyResolutionError, KeyResolver, resolve_trust_policy_key
from .signing import verify_bundle_signature_with_key
from .trust_policy import TrustPolicy, TrustPolicyError


POLICY_ERROR_MESSAGES = {
    "unknown_key_id": "expected key_id is not present in the trust policy",
    "key_not_active": "policy key is not active yet",
    "key_revoked": "policy key is revoked",
    "policy_algorithm_mismatch": "sidecar algorithm does not match the selected policy key",
    "key_resolution_failed": "policy key reference could not be resolved",
    "policy_invalid": "trust policy is invalid",
    "policy_parse_error": "trust policy could not be parsed",
}


def _policy_result(
    sidecar: dict[str, Any],
    policy: TrustPolicy,
    key_id: str,
    *,
    code: str,
    field: str,
    failure_class: str = "trust",
    state: str | None = None,
    expected: Any = None,
    actual: Any = None,
    cause_code: str | None = None,
) -> dict[str, Any]:
    detail: dict[str, Any] = {"code": code, "field": field, "message": POLICY_ERROR_MESSAGES[code]}
    if expected is not None:
        detail["expected"] = expected
    if actual is not None:
        detail["actual"] = actual
    if cause_code is not None:
        detail["cause_code"] = cause_code
    return {
        "ok": False,
        "errors": [POLICY_ERROR_MESSAGES[code]],
        "error_details": [detail],
        "failure_class": failure_class,
        "algorithm": sidecar.get("algorithm"),
        "payload_path": sidecar.get("payload_path"),
        "key_hint": sidecar.get("key_hint"),
        "policy_id": policy.policy_id,
        "key_id": key_id,
        "policy_state": state,
        "policy_key_allowed_for_verification": False,
    }


def trust_policy_error_result(sidecar: dict[str, Any], key_id: str, error: TrustPolicyError) -> dict[str, Any]:
    """Render a parser failure without falling back to a sidecar hint or legacy key."""
    code = error.code if error.code in POLICY_ERROR_MESSAGES else "policy_invalid"
    detail = {
        "code": code,
        "field": "trust_policy",
        "message": POLICY_ERROR_MESSAGES[code],
        "policy_details": list(error.details),
    }
    return {
        "ok": False,
        "errors": [POLICY_ERROR_MESSAGES[code]],
        "error_details": [detail],
        "failure_class": "infrastructure",
        "algorithm": sidecar.get("algorithm"),
        "payload_path": sidecar.get("payload_path"),
        "key_hint": sidecar.get("key_hint"),
        "policy_id": None,
        "key_id": key_id,
        "policy_state": None,
        "policy_key_allowed_for_verification": False,
    }


def verify_bundle_signature_with_policy(
    bundle_path: Path,
    sidecar: dict[str, Any],
    policy: TrustPolicy,
    key_id: str,
    *,
    resolvers: Iterable[KeyResolver] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Authorize one caller-selected policy key, then verify exact version 1 bundle bytes."""
    selected = policy.key_by_id(key_id)
    if selected is None:
        return _policy_result(sidecar, policy, key_id, code="unknown_key_id", field="key_id", actual=key_id)
    if selected.state == "revoked":
        return _policy_result(sidecar, policy, key_id, code="key_revoked", field="state", state=selected.state, actual=selected.state)

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ValueError("policy verification time must include a timezone")
    current_time = current_time.astimezone(timezone.utc)
    if current_time < selected.not_before:
        return _policy_result(
            sidecar,
            policy,
            key_id,
            code="key_not_active",
            field="not_before",
            state=selected.state,
            expected=f"at or after {selected.not_before.isoformat()}",
            actual=current_time.isoformat(),
        )
    if sidecar.get("algorithm") != selected.algorithm:
        return _policy_result(
            sidecar,
            policy,
            key_id,
            code="policy_algorithm_mismatch",
            field="algorithm",
            state=selected.state,
            expected=selected.algorithm,
            actual=sidecar.get("algorithm"),
        )

    try:
        key = resolve_trust_policy_key(selected, resolvers=resolvers)
    except KeyResolutionError as exc:
        return _policy_result(
            sidecar,
            policy,
            key_id,
            code="key_resolution_failed",
            field="key_ref",
            failure_class="infrastructure",
            state=selected.state,
            cause_code=exc.code,
        )

    result = verify_bundle_signature_with_key(bundle_path, sidecar, key)
    result.update(
        {
            "policy_id": policy.policy_id,
            "key_id": key_id,
            "policy_state": selected.state,
            "policy_key_allowed_for_verification": True,
        }
    )
    if not result["ok"]:
        result["failure_class"] = "verification"
    return result


def default_policy_resolvers(policy_path: Path) -> tuple[KeyResolver, ...]:
    """Bind relative file references to the selected policy's directory."""
    return (EnvironmentKeyResolver(), FileKeyResolver(policy_path.parent.resolve()))


def selected_policy_key_file(policy: TrustPolicy, key_id: str, policy_path: Path) -> Path | None:
    """Return the selected local file reference for output-overwrite protection."""
    selected = policy.key_by_id(key_id)
    if selected is None:
        return None
    scheme, _, reference = selected.key_ref.partition(":")
    if scheme != "file":
        return None
    path = Path(reference)
    return path if path.is_absolute() else policy_path.parent.resolve() / path


def policy_verification_exit_code(result: dict[str, Any]) -> int:
    if result.get("ok"):
        return 0
    return 2 if result.get("failure_class") == "infrastructure" else 1
