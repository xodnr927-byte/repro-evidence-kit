from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repro_evidence_kit.signing import sign_bundle, verify_bundle_signature


class SigningTests(unittest.TestCase):
    def test_sign_and_verify_exact_bundle_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            key = root / "local-test.key"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")

            sidecar = sign_bundle(bundle, key, key_hint="local-test")
            result = verify_bundle_signature(bundle, sidecar, key)

        self.assertTrue(result["ok"])
        self.assertEqual(sidecar["signature_version"], "1.0")
        self.assertEqual(sidecar["algorithm"], "hmac-sha256")
        self.assertEqual(sidecar["payload_path"], "evidence-bundle.yaml")
        self.assertEqual(sidecar["key_hint"], "local-test")

    def test_verify_rejects_changed_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            key = root / "local-test.key"
            bundle.write_text("title: Before\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")
            sidecar = sign_bundle(bundle, key)

            bundle.write_text("title: After\n", encoding="utf-8")
            result = verify_bundle_signature(bundle, sidecar, key)

        self.assertFalse(result["ok"])
        self.assertIn("payload_sha256 mismatch", result["errors"])
        self.assertIn("signature mismatch", result["errors"])

    def test_verify_rejects_unsupported_algorithm(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            key = root / "local-test.key"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")
            sidecar = sign_bundle(bundle, key)
            sidecar["algorithm"] = "unknown"

            result = verify_bundle_signature(bundle, sidecar, key)

        self.assertFalse(result["ok"])
        self.assertIn("unsupported algorithm", result["errors"])

    def test_verify_rejects_wrong_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            signing_key = root / "signing.key"
            wrong_key = root / "wrong.key"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            signing_key.write_text("synthetic signing key only\n", encoding="utf-8")
            wrong_key.write_text("different synthetic key only\n", encoding="utf-8")

            sidecar = sign_bundle(bundle, signing_key)
            result = verify_bundle_signature(bundle, sidecar, wrong_key)

        self.assertFalse(result["ok"])
        self.assertIn("signature mismatch", result["errors"])
        self.assertEqual(result["error_details"][-1]["code"], "signature_mismatch")

    def test_verify_rejects_missing_signature(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            key = root / "local-test.key"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")
            sidecar = sign_bundle(bundle, key)
            del sidecar["signature"]

            result = verify_bundle_signature(bundle, sidecar, key)

        self.assertFalse(result["ok"])
        self.assertIn("missing signature", result["errors"])
        self.assertEqual(result["error_details"][-1]["code"], "missing_signature")

    def test_verify_rejects_invalid_payload_hash_shape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            key = root / "local-test.key"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")
            sidecar = sign_bundle(bundle, key)
            sidecar["payload_sha256"] = "not-a-sha256"

            result = verify_bundle_signature(bundle, sidecar, key)

        self.assertFalse(result["ok"])
        self.assertIn("invalid payload_sha256", result["errors"])
        self.assertEqual(result["error_details"][0]["code"], "invalid_payload_sha256")


class SignatureUxTests(unittest.TestCase):
    def test_verify_reports_structured_error_details(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            key = root / "local-test.key"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")
            sidecar = sign_bundle(bundle, key)
            sidecar["signature"] = "not-hex"

            result = verify_bundle_signature(bundle, sidecar, key)

        self.assertFalse(result["ok"])
        self.assertIn("invalid signature", result["errors"])
        self.assertEqual(result["error_details"][0]["code"], "invalid_signature")
        self.assertEqual(result["error_details"][0]["field"], "signature")

    def test_verify_reports_payload_path_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "evidence-bundle.yaml"
            key = root / "local-test.key"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")
            sidecar = sign_bundle(bundle, key)
            sidecar["payload_path"] = "other.yaml"

            result = verify_bundle_signature(bundle, sidecar, key)

        self.assertFalse(result["ok"])
        self.assertIn("payload_path mismatch", result["errors"])
        self.assertEqual(result["error_details"][0]["code"], "payload_path_mismatch")


if __name__ == "__main__":
    unittest.main()
