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


if __name__ == "__main__":
    unittest.main()
