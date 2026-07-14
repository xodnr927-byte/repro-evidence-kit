from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from unittest import mock

from repro_evidence_kit.key_resolver import (
    EnvironmentKeyResolver,
    FileKeyResolver,
    KeyResolutionError,
    resolve_key_reference,
    resolve_trust_policy_key,
)
from repro_evidence_kit.trust_policy import parse_trust_policy


def _parsed_key(key_ref: str):
    policy = parse_trust_policy(
        {
            "policy_version": "1.0",
            "policy_id": "synthetic-resolver-policy",
            "keys": [
                {
                    "key_id": "synthetic-key",
                    "algorithm": "hmac-sha256",
                    "key_ref": key_ref,
                    "state": "verify_only",
                    "not_before": "2026-01-01T00:00:00Z",
                }
            ],
        }
    )
    return policy.keys[0]


class KeyResolverTests(unittest.TestCase):
    def test_default_resolvers_use_the_current_environment_and_absolute_file(self):
        with tempfile.TemporaryDirectory() as td:
            key_path = Path(td) / "synthetic.key"
            key_path.write_bytes(b"synthetic-file-value")
            with mock.patch.dict("os.environ", {"SYNTHETIC_KEY": "synthetic-env-value"}, clear=True):
                self.assertEqual(resolve_key_reference("env:SYNTHETIC_KEY"), b"synthetic-env-value")
                self.assertEqual(resolve_key_reference(f"file:{key_path}"), b"synthetic-file-value")

    def test_resolves_synthetic_environment_material_exactly(self):
        resolver = EnvironmentKeyResolver({"SYNTHETIC_KEY": "synthetic-value-\u2603"})

        material = resolve_trust_policy_key(_parsed_key("env:SYNTHETIC_KEY"), resolvers=(resolver,))

        self.assertEqual(material, "synthetic-value-\u2603".encode())

    def test_resolves_synthetic_file_material_exactly(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "synthetic.key").write_bytes(b"synthetic-file-key\n")

            material = resolve_key_reference("file:synthetic.key", resolvers=(FileKeyResolver(root),))

        self.assertEqual(material, b"synthetic-file-key\n")

    def test_fails_closed_for_missing_references(self):
        with tempfile.TemporaryDirectory() as td:
            cases = (
                ("env:MISSING_KEY", (EnvironmentKeyResolver({}),)),
                ("file:missing.key", (FileKeyResolver(Path(td)),)),
            )
            for key_ref, resolvers in cases:
                with self.subTest(key_ref=key_ref), self.assertRaises(KeyResolutionError) as raised:
                    resolve_key_reference(key_ref, resolvers=resolvers)
                self.assertEqual(raised.exception.code, "key_reference_missing")
                self.assertEqual(raised.exception.details[0]["key_ref"], key_ref)

    def test_fails_closed_for_unsupported_invalid_and_ambiguous_references(self):
        for key_ref, expected_code in (
            ("https://example.test/key", "unsupported_resolver"),
            ("ENV:SYNTHETIC_KEY", "unsupported_resolver"),
            ("env:bad-name", "invalid_key_reference"),
            ("file://remote/key", "invalid_key_reference"),
        ):
            with self.subTest(key_ref=key_ref), self.assertRaises(KeyResolutionError) as raised:
                resolve_key_reference(key_ref)
            self.assertEqual(raised.exception.code, expected_code)

        duplicate = (EnvironmentKeyResolver({"SYNTHETIC_KEY": "a"}), EnvironmentKeyResolver({"SYNTHETIC_KEY": "b"}))
        with self.assertRaises(KeyResolutionError) as raised:
            resolve_key_reference("env:SYNTHETIC_KEY", resolvers=duplicate)
        self.assertEqual(raised.exception.code, "ambiguous_key_reference")

        with self.assertRaises(KeyResolutionError) as raised:
            resolve_key_reference("file:relative.key", resolvers=(FileKeyResolver(),))
        self.assertEqual(raised.exception.code, "ambiguous_key_reference")

    def test_fails_closed_for_unreadable_file(self):
        resolver = FileKeyResolver()
        key_ref = f"file:{Path.cwd() / 'synthetic.key'}"
        with mock.patch("pathlib.Path.read_bytes", side_effect=PermissionError("denied")):
            with self.assertRaises(KeyResolutionError) as raised:
                resolve_key_reference(key_ref, resolvers=(resolver,))
        self.assertEqual(raised.exception.code, "key_reference_unreadable")

    def test_fails_closed_for_empty_or_non_byte_material(self):
        @dataclass(frozen=True)
        class SyntheticResolver:
            values: Mapping[str, object]
            scheme: str = "env"

            def resolve(self, reference: str) -> bytes:
                return self.values[reference]  # type: ignore[return-value]

        for material in (b"", "not-bytes"):
            with self.subTest(material=material), self.assertRaises(KeyResolutionError) as raised:
                resolve_key_reference("env:SYNTHETIC_KEY", resolvers=(SyntheticResolver({"SYNTHETIC_KEY": material}),))
            self.assertEqual(raised.exception.code, "malformed_key_material")

        with tempfile.TemporaryDirectory() as td:
            empty_path = Path(td) / "empty.key"
            empty_path.write_bytes(b"")
            empty_cases = (
                ("env:SYNTHETIC_KEY", (EnvironmentKeyResolver({"SYNTHETIC_KEY": ""}),)),
                (f"file:{empty_path}", (FileKeyResolver(),)),
            )
            for key_ref, resolvers in empty_cases:
                with self.subTest(key_ref=key_ref), self.assertRaises(KeyResolutionError) as raised:
                    resolve_key_reference(key_ref, resolvers=resolvers)
                self.assertEqual(raised.exception.code, "malformed_key_material")

    def test_classifies_unexpected_resolver_failure_without_leaking_values(self):
        @dataclass(frozen=True)
        class BrokenResolver:
            scheme: str = "env"

            def resolve(self, reference: str) -> bytes:
                raise RuntimeError("synthetic-secret-value")

        with self.assertRaises(KeyResolutionError) as raised:
            resolve_key_reference("env:SYNTHETIC_KEY", resolvers=(BrokenResolver(),))
        self.assertEqual(raised.exception.code, "key_resolution_failed")
        self.assertNotIn("synthetic-secret-value", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
