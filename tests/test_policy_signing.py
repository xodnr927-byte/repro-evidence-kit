from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from repro_evidence_kit.cli import main
from repro_evidence_kit.key_resolver import EnvironmentKeyResolver
from repro_evidence_kit.policy_signing import PolicySigningError, policy_signing_exit_code, sign_bundle_with_policy
from repro_evidence_kit.policy_verification import verify_bundle_signature_with_policy
from repro_evidence_kit.trust_policy import parse_trust_policy


NOW = datetime(2026, 7, 18, tzinfo=timezone.utc)


def _policy(*, key_ref: str = "env:SYNTHETIC_KEY", state: str = "active", not_before: str = "2026-01-01T00:00:00Z"):
    return parse_trust_policy(
        {
            "policy_version": "1.0",
            "policy_id": "synthetic-signing-policy",
            "keys": [
                {
                    "key_id": "expected-key",
                    "algorithm": "hmac-sha256",
                    "key_ref": key_ref,
                    "state": state,
                    "not_before": not_before,
                }
            ],
        }
    )


class PolicySigningTests(unittest.TestCase):
    def test_active_key_signs_version_1_sidecar_and_policy_verification_accepts_it(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "bundle.yaml"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            resolver = EnvironmentKeyResolver({"SYNTHETIC_KEY": "synthetic-policy-key"})
            policy = _policy()

            sidecar = sign_bundle_with_policy(bundle, policy, "expected-key", resolvers=(resolver,), now=NOW)
            result = verify_bundle_signature_with_policy(
                bundle,
                sidecar,
                policy,
                "expected-key",
                resolvers=(resolver,),
                now=NOW,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(
            set(sidecar),
            {"signature_version", "payload_path", "payload_sha256", "algorithm", "key_hint", "signature"},
        )
        self.assertEqual(sidecar["signature_version"], "1.0")
        self.assertEqual(sidecar["key_hint"], "expected-key")

    def test_explicit_key_hint_remains_advisory_sidecar_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "bundle.yaml"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            sidecar = sign_bundle_with_policy(
                bundle,
                _policy(),
                "expected-key",
                key_hint="different-advisory-label",
                resolvers=(EnvironmentKeyResolver({"SYNTHETIC_KEY": "synthetic-policy-key"}),),
                now=NOW,
            )

        self.assertEqual(sidecar["key_hint"], "different-advisory-label")

    def test_verify_only_revoked_unknown_and_future_keys_fail_before_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "bundle.yaml"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            cases = (
                (_policy(state="verify_only"), "expected-key", "key_not_allowed_for_signing"),
                (_policy(state="revoked"), "expected-key", "key_revoked"),
                (_policy(), "missing-key", "unknown_key_id"),
                (_policy(not_before="2026-08-01T00:00:00Z"), "expected-key", "key_not_active"),
            )
            for policy, key_id, expected_code in cases:
                with self.subTest(expected_code=expected_code), self.assertRaises(PolicySigningError) as caught:
                    sign_bundle_with_policy(
                        bundle,
                        policy,
                        key_id,
                        key_hint="expected-key",
                        resolvers=(EnvironmentKeyResolver({}),),
                        now=NOW,
                    )
                self.assertEqual(caught.exception.code, expected_code)
                self.assertEqual(policy_signing_exit_code(caught.exception), 1)

    def test_resolution_failure_is_infrastructure_error(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "bundle.yaml"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            with self.assertRaises(PolicySigningError) as caught:
                sign_bundle_with_policy(
                    bundle,
                    _policy(),
                    "expected-key",
                    resolvers=(EnvironmentKeyResolver({}),),
                    now=NOW,
                )

        self.assertEqual(caught.exception.code, "key_resolution_failed")
        self.assertEqual(caught.exception.cause_code, "key_reference_missing")
        self.assertEqual(policy_signing_exit_code(caught.exception), 2)


class PolicySigningCliTests(unittest.TestCase):
    def _write_fixture(self, root: Path, *, state: str = "active") -> tuple[Path, Path, Path]:
        bundle = root / "bundle.yaml"
        key = root / "synthetic.key"
        policy = root / "trust-policy.yaml"
        bundle.write_text("title: Synthetic\n", encoding="utf-8")
        key.write_bytes(b"synthetic-policy-key")
        policy.write_text(
            "policy_version: '1.0'\npolicy_id: synthetic-cli-policy\nkeys:\n"
            "  - key_id: expected-key\n    algorithm: hmac-sha256\n"
            f"    key_ref: file:{key.name}\n    state: {state}\n"
            "    not_before: '2026-01-01T00:00:00Z'\n",
            encoding="utf-8",
        )
        return bundle, key, policy

    def test_cli_signs_with_relative_policy_file_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, _, policy = self._write_fixture(root)
            output = root / "bundle.yaml.sig.json"
            code = main(
                [
                    "evidence",
                    "sign",
                    str(bundle),
                    "--trust-policy",
                    str(policy),
                    "--key-id",
                    "expected-key",
                    "-o",
                    str(output),
                ]
            )
            sidecar = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(sidecar["key_hint"], "expected-key")
        self.assertEqual(sidecar["signature_version"], "1.0")

    def test_cli_policy_dry_run_prints_sidecar_without_writing_one(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, _, policy = self._write_fixture(root)
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                code = main(
                    [
                        "evidence",
                        "sign",
                        str(bundle),
                        "--trust-policy",
                        str(policy),
                        "--key-id",
                        "expected-key",
                        "--dry-run",
                    ]
                )
            sidecar = json.loads(stdout.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(sidecar["key_hint"], "expected-key")

    def test_cli_disallowed_state_returns_1_without_writing_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, _, policy = self._write_fixture(root, state="verify_only")
            output = root / "bundle.yaml.sig.json"
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                code = main(
                    [
                        "evidence",
                        "sign",
                        str(bundle),
                        "--trust-policy",
                        str(policy),
                        "--key-id",
                        "expected-key",
                        "-o",
                        str(output),
                    ]
                )

        self.assertEqual(code, 1)
        self.assertIn("key_not_allowed_for_signing", stderr.getvalue())
        self.assertFalse(output.exists())

    def test_cli_missing_key_reference_returns_2_without_writing_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, key, policy = self._write_fixture(root)
            key.unlink()
            output = root / "bundle.yaml.sig.json"
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                code = main(
                    [
                        "evidence",
                        "sign",
                        str(bundle),
                        "--trust-policy",
                        str(policy),
                        "--key-id",
                        "expected-key",
                        "-o",
                        str(output),
                    ]
                )

        self.assertEqual(code, 2)
        self.assertIn("key_resolution_failed", stderr.getvalue())
        self.assertIn("key_reference_missing", stderr.getvalue())
        self.assertFalse(output.exists())

    def test_cli_invalid_policy_returns_2_without_writing_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, _, policy = self._write_fixture(root)
            policy.write_text("policy_version: [broken\n", encoding="utf-8")
            output = root / "bundle.yaml.sig.json"
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                code = main(
                    [
                        "evidence",
                        "sign",
                        str(bundle),
                        "--trust-policy",
                        str(policy),
                        "--key-id",
                        "expected-key",
                        "-o",
                        str(output),
                    ]
                )

        self.assertEqual(code, 2)
        self.assertIn("policy_parse_error", stderr.getvalue())
        self.assertFalse(output.exists())

    def test_cli_requires_key_id_only_for_policy_mode(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, key, policy = self._write_fixture(root)
            commands = (
                ["evidence", "sign", str(bundle), "--trust-policy", str(policy), "--dry-run"],
                ["evidence", "sign", str(bundle), "--trust-policy", str(policy), "--key-id", "", "--dry-run"],
                ["evidence", "sign", str(bundle), "--key", str(key), "--key-id", "expected-key", "--dry-run"],
            )
            for command in commands:
                with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(main(command), 2)
                    self.assertIn("error:", stderr.getvalue())

    def test_cli_does_not_overwrite_selected_policy_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, key, policy = self._write_fixture(root)
            before = key.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                code = main(
                    [
                        "evidence",
                        "sign",
                        str(bundle),
                        "--trust-policy",
                        str(policy),
                        "--key-id",
                        "expected-key",
                        "-o",
                        str(key),
                    ]
                )
            self.assertEqual(code, 2)
            self.assertIn("must not overwrite", stderr.getvalue())
            self.assertEqual(key.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
