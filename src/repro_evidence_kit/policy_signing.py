from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .key_resolver import KeyResolutionError, KeyResolver, resolve_trust_policy_key
from .signing import ALGORITHM, sign_bundle_with_key
from .trust_policy import TrustPolicy


POLICY_SIGNING_ERROR_MESSAGES = {
    "unknown_key_id": "selected key_id is not present in the trust policy",
    "key_not_active": "policy key is not active yet",
    "key_not_allowed_for_signing": "policy key state does not permit signing",
    "key_revoked": "policy key is revoked",
    "policy_algorithm_mismatch": "policy key algorithm is not supported for signing",
    "key_resolution_failed": "policy key reference could not be resolved",
}


class PolicySigningError(ValueError):
    """Fail-closed policy authorization or key-resolution error."""

    def __init__(
        self,
        code: str,
        *,
        policy_id: str,
        key_id: str,
        state: str | None = None,
        failure_class: str = "trust",
        cause_code: str | None = None,
    ) -> None:
        self.code = code
        self.policy_id = policy_id
        self.key_id = key_id
        self.state = state
        self.failure_class = failure_class
        self.cause_code = cause_code
        super().__init__(f"{code}: {POLICY_SIGNING_ERROR_MESSAGES[code]}")


def sign_bundle_with_policy(
    bundle_path: Path,
    policy: TrustPolicy,
    key_id: str,
    *,
    key_hint: str | None = None,
    resolvers: Iterable[KeyResolver] | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Authorize one caller-selected active policy key, then create a version 1 sidecar."""
    selected = policy.key_by_id(key_id)
    if selected is None:
        raise PolicySigningError("unknown_key_id", policy_id=policy.policy_id, key_id=key_id)
    if selected.state == "revoked":
        raise PolicySigningError("key_revoked", policy_id=policy.policy_id, key_id=key_id, state=selected.state)
    if selected.state != "active":
        raise PolicySigningError("key_not_allowed_for_signing", policy_id=policy.policy_id, key_id=key_id, state=selected.state)

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ValueError("policy signing time must include a timezone")
    current_time = current_time.astimezone(timezone.utc)
    if current_time < selected.not_before:
        raise PolicySigningError("key_not_active", policy_id=policy.policy_id, key_id=key_id, state=selected.state)
    if selected.algorithm != ALGORITHM:
        raise PolicySigningError("policy_algorithm_mismatch", policy_id=policy.policy_id, key_id=key_id, state=selected.state)

    try:
        key = resolve_trust_policy_key(selected, resolvers=resolvers)
    except KeyResolutionError as exc:
        raise PolicySigningError(
            "key_resolution_failed",
            policy_id=policy.policy_id,
            key_id=key_id,
            state=selected.state,
            failure_class="infrastructure",
            cause_code=exc.code,
        ) from exc
    return sign_bundle_with_key(bundle_path, key, key_hint=key_hint or key_id)


def policy_signing_exit_code(error: PolicySigningError) -> int:
    return 2 if error.failure_class == "infrastructure" else 1
