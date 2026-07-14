from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Protocol

from .trust_policy import SUPPORTED_RESOLVERS, TrustPolicyKey


_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class KeyResolutionError(ValueError):
    """Fail-closed local key-resolution error with a stable machine-readable code."""

    def __init__(self, code: str, message: str, *, key_ref: str) -> None:
        self.code = code
        self.key_ref = key_ref
        self.details = ({"code": code, "key_ref": key_ref, "message": message},)
        super().__init__(f"{code}: {message}")


class KeyResolver(Protocol):
    """Interface for one local, parser-approved key-reference scheme."""

    scheme: str

    def resolve(self, reference: str) -> bytes:
        """Return the exact key bytes for the scheme-specific reference."""
        ...


@dataclass(frozen=True)
class EnvironmentKeyResolver:
    """Resolve key bytes from one explicitly named environment variable."""

    environment: Mapping[str, str] | None = None
    scheme: str = field(default="env", init=False)

    def resolve(self, reference: str) -> bytes:
        key_ref = f"{self.scheme}:{reference}"
        environment = os.environ if self.environment is None else self.environment
        if reference not in environment:
            raise KeyResolutionError("key_reference_missing", "environment variable is not set", key_ref=key_ref)
        try:
            return environment[reference].encode("utf-8")
        except UnicodeEncodeError as exc:
            raise KeyResolutionError("malformed_key_material", "environment value is not valid UTF-8 text", key_ref=key_ref) from exc


@dataclass(frozen=True)
class FileKeyResolver:
    """Resolve exact key bytes from a local file path."""

    base_directory: Path | None = None
    scheme: str = field(default="file", init=False)

    def resolve(self, reference: str) -> bytes:
        key_ref = f"{self.scheme}:{reference}"
        path = Path(reference)
        if not path.is_absolute():
            if self.base_directory is None:
                raise KeyResolutionError("ambiguous_key_reference", "relative key file requires an explicit base directory", key_ref=key_ref)
            path = self.base_directory / path
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise KeyResolutionError("key_reference_missing", "key file does not exist", key_ref=key_ref) from exc
        except OSError as exc:
            raise KeyResolutionError("key_reference_unreadable", "key file could not be read", key_ref=key_ref) from exc


def _split_key_reference(key_ref: str) -> tuple[str, str]:
    if not isinstance(key_ref, str) or key_ref != key_ref.strip() or any(ord(char) < 32 or ord(char) == 127 for char in key_ref):
        raise KeyResolutionError("invalid_key_reference", "key reference must be a trimmed string without control characters", key_ref=str(key_ref))
    scheme, separator, reference = key_ref.partition(":")
    if not separator or scheme not in SUPPORTED_RESOLVERS:
        raise KeyResolutionError("unsupported_resolver", "key reference must use the env: or file: resolver scheme", key_ref=key_ref)
    if scheme == "env" and _ENV_NAME.fullmatch(reference) is None:
        raise KeyResolutionError("invalid_key_reference", "env: reference must contain one environment-variable name", key_ref=key_ref)
    if scheme == "file" and (not reference or reference.startswith("//")):
        raise KeyResolutionError("invalid_key_reference", "file: reference must contain a local path, not a remote URL", key_ref=key_ref)
    return scheme, reference


def resolve_key_reference(key_ref: str, *, resolvers: Iterable[KeyResolver] | None = None) -> bytes:
    """Resolve one parser-approved local key reference without authorizing its use."""
    scheme, reference = _split_key_reference(key_ref)
    available = tuple(resolvers) if resolvers is not None else (EnvironmentKeyResolver(), FileKeyResolver())
    matches = tuple(resolver for resolver in available if resolver.scheme == scheme)
    if not matches:
        raise KeyResolutionError("unsupported_resolver", f"no resolver is configured for {scheme!r}", key_ref=key_ref)
    if len(matches) != 1:
        raise KeyResolutionError("ambiguous_key_reference", f"multiple resolvers are configured for {scheme!r}", key_ref=key_ref)
    try:
        material = matches[0].resolve(reference)
    except KeyResolutionError:
        raise
    except Exception as exc:
        raise KeyResolutionError("key_resolution_failed", "resolver failed without a classified error", key_ref=key_ref) from exc
    if not isinstance(material, bytes) or not material:
        raise KeyResolutionError("malformed_key_material", "resolved key material must be non-empty bytes", key_ref=key_ref)
    return material


def resolve_trust_policy_key(key: TrustPolicyKey, *, resolvers: Iterable[KeyResolver] | None = None) -> bytes:
    """Resolve a parsed policy key record without checking policy state or authorization."""
    return resolve_key_reference(key.key_ref, resolvers=resolvers)
