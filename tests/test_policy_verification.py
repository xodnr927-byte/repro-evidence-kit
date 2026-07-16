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
from repro_evidence_kit.policy_verification import policy_verification_exit_code, verify_bundle_signature_with_policy
from repro_evidence_kit.signing import sign_bundle
from repro_evidence_kit.trust_policy import parse_trust_policy


NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def _policy(*, key_ref: str = "env:SYNTHETIC_KEY", state: str = "verify_only", not_before: str = "2026-01-01T00:00:00Z"):
    return parse_trust_policy(
        {
            "policy_version": "1.0",
            "policy_id": "synthetic-verification-policy",
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


class PolicyVerificationTests(unittest.TestCase):
    def _sidecar(self, root: Path, *, key_hint: str = "attacker-controlled-hint"):
        bundle = root / "bundle.yaml"
        key = root / "signing.key"
        bundle.write_text("title: Synthetic\n", encoding="utf-8")
        key.write_bytes(b"synthetic-policy-key")
        return bundle, sign_bundle(bundle, key, key_hint=key_hint)

    def test_active_and_verify_only_keys_verify_with_caller_selected_identity(self):
        with tempfile.TemporaryDirectory() as td:
            bundle, sidecar = self._sidecar(Path(td))
            resolver = EnvironmentKeyResolver({"SYNTHETIC_KEY": "synthetic-policy-key"})
            for state in ("active", "verify_only"):
                with self.subTest(state=state):
                    result = verify_bundle_signature_with_policy(
                        bundle,
                        sidecar,
                        _policy(state=state),
                        "expected-key",
                        resolvers=(resolver,),
                        now=NOW,
                    )
                    self.assertTrue(result["ok"])
                    self.assertEqual(result["key_id"], "expected-key")
                    self.assertEqual(result["key_hint"], "attacker-controlled-hint")
                    self.assertTrue(result["policy_key_allowed_for_verification"])
                    self.assertEqual(policy_verification_exit_code(result), 0)

    def test_unknown_key_id_does_not_fall_back_to_key_hint_or_resolve(self):
        with tempfile.TemporaryDirectory() as td:
            bundle, sidecar = self._sidecar(Path(td), key_hint="expected-key")
            result = verify_bundle_signature_with_policy(
                bundle,
                sidecar,
                _policy(),
                "missing-key",
                resolvers=(EnvironmentKeyResolver({}),),
                now=NOW,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_details"][0]["code"], "unknown_key_id")
        self.assertEqual(policy_verification_exit_code(result), 1)

    def test_revoked_and_not_yet_active_keys_fail_before_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            bundle, sidecar = self._sidecar(Path(td))
            cases = (
                (_policy(state="revoked"), "key_revoked"),
                (_policy(not_before="2026-08-01T00:00:00Z"), "key_not_active"),
            )
            for policy, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    result = verify_bundle_signature_with_policy(
                        bundle,
                        sidecar,
                        policy,
                        "expected-key",
                        resolvers=(EnvironmentKeyResolver({}),),
                        now=NOW,
                    )
                    self.assertEqual(result["error_details"][0]["code"], expected_code)
                    self.assertFalse(result["policy_key_allowed_for_verification"])

    def test_algorithm_mismatch_fails_before_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            bundle, sidecar = self._sidecar(Path(td))
            sidecar["algorithm"] = "unknown"
            result = verify_bundle_signature_with_policy(
                bundle,
                sidecar,
                _policy(),
                "expected-key",
                resolvers=(EnvironmentKeyResolver({}),),
                now=NOW,
            )

        self.assertEqual(result["error_details"][0]["code"], "policy_algorithm_mismatch")

    def test_resolution_failure_is_structured_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as td:
            bundle, sidecar = self._sidecar(Path(td))
            result = verify_bundle_signature_with_policy(
                bundle,
                sidecar,
                _policy(),
                "expected-key",
                resolvers=(EnvironmentKeyResolver({}),),
                now=NOW,
            )

        detail = result["error_details"][0]
        self.assertEqual(detail["code"], "key_resolution_failed")
        self.assertEqual(detail["cause_code"], "key_reference_missing")
        self.assertEqual(policy_verification_exit_code(result), 2)

    def test_signature_mismatch_remains_a_verification_failure(self):
        with tempfile.TemporaryDirectory() as td:
            bundle, sidecar = self._sidecar(Path(td))
            result = verify_bundle_signature_with_policy(
                bundle,
                sidecar,
                _policy(),
                "expected-key",
                resolvers=(EnvironmentKeyResolver({"SYNTHETIC_KEY": "wrong-synthetic-key"}),),
                now=NOW,
            )

        self.assertEqual(result["failure_class"], "verification")
        self.assertIn("signature_mismatch", {detail["code"] for detail in result["error_details"]})
        self.assertEqual(policy_verification_exit_code(result), 1)


class PolicyVerificationCliTests(unittest.TestCase):
    def _write_fixture(self, root: Path, *, state: str = "verify_only") -> tuple[Path, Path, Path, Path]:
        bundle = root / "bundle.yaml"
        key = root / "synthetic.key"
        signature = root / "bundle.yaml.sig.json"
        policy = root / "trust-policy.yaml"
        bundle.write_text("title: Synthetic\n", encoding="utf-8")
        key.write_bytes(b"synthetic-policy-key")
        signature.write_text(json.dumps(sign_bundle(bundle, key, key_hint="untrusted-hint")), encoding="utf-8")
        policy.write_text(
            "policy_version: '1.0'\npolicy_id: synthetic-cli-policy\nkeys:\n"
            "  - key_id: expected-key\n    algorithm: hmac-sha256\n"
            f"    key_ref: file:{key.name}\n    state: {state}\n"
            "    not_before: '2026-01-01T00:00:00Z'\n",
            encoding="utf-8",
        )
        return bundle, key, signature, policy

    def test_cli_verifies_relative_file_reference_from_policy_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, _, signature, policy = self._write_fixture(root)
            output = root / "result.json"
            code = main(
                [
                    "evidence",
                    "verify-signature",
                    str(bundle),
                    "--signature",
                    str(signature),
                    "--trust-policy",
                    str(policy),
                    "--key-id",
                    "expected-key",
                    "-o",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["policy_id"], "synthetic-cli-policy")

    def test_cli_returns_1_for_revoked_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, _, signature, policy = self._write_fixture(root, state="revoked")
            output = root / "result.json"
            code = main(
                [
                    "evidence",
                    "verify-signature",
                    str(bundle),
                    "--signature",
                    str(signature),
                    "--trust-policy",
                    str(policy),
                    "--key-id",
                    "expected-key",
                    "-o",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 1)
        self.assertEqual(result["error_details"][0]["code"], "key_revoked")

    def test_cli_returns_structured_exit_2_for_invalid_policy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, _, signature, policy = self._write_fixture(root)
            policy.write_text("policy_version: [broken\n", encoding="utf-8")
            output = root / "result.json"
            code = main(
                [
                    "evidence",
                    "verify-signature",
                    str(bundle),
                    "--signature",
                    str(signature),
                    "--trust-policy",
                    str(policy),
                    "--key-id",
                    "expected-key",
                    "-o",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 2)
        self.assertEqual(result["error_details"][0]["code"], "policy_parse_error")

    def test_cli_returns_structured_exit_2_for_missing_key_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, key, signature, policy = self._write_fixture(root)
            key.unlink()
            output = root / "result.json"
            code = main(
                [
                    "evidence",
                    "verify-signature",
                    str(bundle),
                    "--signature",
                    str(signature),
                    "--trust-policy",
                    str(policy),
                    "--key-id",
                    "expected-key",
                    "-o",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 2)
        self.assertEqual(result["error_details"][0]["code"], "key_resolution_failed")
        self.assertEqual(result["error_details"][0]["cause_code"], "key_reference_missing")

    def test_cli_requires_key_id_only_for_policy_mode(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, key, signature, policy = self._write_fixture(root)
            commands = (
                ["evidence", "verify-signature", str(bundle), "--signature", str(signature), "--trust-policy", str(policy)],
                ["evidence", "verify-signature", str(bundle), "--signature", str(signature), "--trust-policy", str(policy), "--key-id", ""],
                ["evidence", "verify-signature", str(bundle), "--signature", str(signature), "--key", str(key), "--key-id", "expected-key"],
            )
            for command in commands:
                with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(main(command), 2)
                    self.assertIn("error:", stderr.getvalue())

    def test_cli_does_not_overwrite_selected_policy_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle, key, signature, policy = self._write_fixture(root)
            before = key.read_bytes()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "evidence",
                        "verify-signature",
                        str(bundle),
                        "--signature",
                        str(signature),
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
