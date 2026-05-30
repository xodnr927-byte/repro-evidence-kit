from __future__ import annotations

import unittest

from repro_evidence_kit.evidence import validate_evidence_bundle


class EvidenceTests(unittest.TestCase):
    def test_valid_bundle(self):
        result = validate_evidence_bundle({
            "schema_version": "1.0",
            "title": "Example",
            "inputs": [{"path": "input.bin", "sha256": "a" * 64}],
            "commands": [{"argv": ["tool", "input.bin"]}],
            "outputs": [{"path": "output.bin", "sha256": "b" * 64}],
        })
        self.assertTrue(result["ok"])

    def test_missing_fields(self):
        result = validate_evidence_bundle({"title": "Bad"})
        self.assertFalse(result["ok"])
        self.assertIn("missing top-level field: inputs", result["errors"])


if __name__ == "__main__":
    unittest.main()
