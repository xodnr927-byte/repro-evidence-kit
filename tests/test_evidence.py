from __future__ import annotations

import unittest
from pathlib import Path

from repro_evidence_kit.evidence import Draft202012Validator, validate_evidence_bundle, validate_evidence_bundle_schema


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

    @unittest.skipIf(Draft202012Validator is None, "jsonschema optional dependency is not installed")
    def test_schema_valid_bundle(self):
        result = validate_evidence_bundle_schema({
            "schema_version": "1.0",
            "title": "Example",
            "inputs": [{"path": "input.bin", "sha256": "a" * 64}],
            "commands": [{"argv": ["tool", "input.bin"]}],
            "outputs": [{"path": "output.bin", "sha256": "b" * 64}],
        })
        self.assertTrue(result["ok"])
        self.assertEqual(result["validator"], "jsonschema Draft 2020-12")

    @unittest.skipIf(Draft202012Validator is None, "jsonschema optional dependency is not installed")
    def test_schema_catches_schema_only_sha_failure(self):
        bundle = {
            "schema_version": "1.0",
            "title": "Example",
            "inputs": [{"path": "input.bin", "sha256": "not-a-hex-digest"}],
            "commands": [{"argv": ["tool", "input.bin"]}],
            "outputs": [{"path": "output.bin", "sha256": "b" * 64}],
        }
        lightweight = validate_evidence_bundle(bundle)
        schema_result = validate_evidence_bundle_schema(bundle)
        self.assertTrue(lightweight["ok"])
        self.assertFalse(schema_result["ok"])
        self.assertTrue(any("sha256" in error for error in schema_result["errors"]))

    def test_packaged_schema_matches_checked_in_schema(self):
        repo_schema = Path("schemas/evidence-bundle.schema.json").read_text(encoding="utf-8")
        packaged_schema = Path("src/repro_evidence_kit/schemas/evidence-bundle.schema.json").read_text(encoding="utf-8")
        self.assertEqual(packaged_schema, repo_schema)


if __name__ == "__main__":
    unittest.main()
