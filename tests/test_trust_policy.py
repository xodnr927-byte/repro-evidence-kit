from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from repro_evidence_kit.trust_policy import (
    TrustPolicyError,
    default_trust_policy_schema_path,
    load_trust_policy,
    parse_trust_policy,
)

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None


VALID_POLICY = {
    "policy_version": "1.0",
    "policy_id": "synthetic-maintainer-policy",
    "keys": [
        {
            "key_id": "maintainer-2026-a",
            "algorithm": "hmac-sha256",
            "key_ref": "env:REPRO_EVIDENCE_KEY_2026_A",
            "state": "verify_only",
            "not_before": "2026-01-01T00:00:00Z",
        },
        {
            "key_id": "maintainer-2026-b",
            "algorithm": "hmac-sha256",
            "key_ref": "file:/run/secrets/repro-evidence-key-2026-b",
            "state": "revoked",
            "not_before": "2026-06-01T00:00:00+00:00",
            "revoked_at": "2026-07-01T00:00:00Z",
            "comment": "synthetic fixture",
        },
    ],
}


class TrustPolicyTests(unittest.TestCase):
    def test_parse_valid_policy_and_normalize_timestamps(self):
        policy = parse_trust_policy(VALID_POLICY)

        self.assertEqual(policy.policy_version, "1.0")
        self.assertEqual(policy.policy_id, "synthetic-maintainer-policy")
        self.assertEqual(policy.key_by_id("maintainer-2026-a").state, "verify_only")
        self.assertEqual(policy.keys[0].not_before, datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertIsNone(policy.key_by_id("missing"))

    def test_loads_json_and_yaml(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            json_path = root / "policy.json"
            yaml_path = root / "policy.yaml"
            json_path.write_text(json.dumps(VALID_POLICY), encoding="utf-8")
            yaml_path.write_text(
                "policy_version: '1.0'\npolicy_id: synthetic\nkeys:\n"
                "  - key_id: key-a\n    algorithm: hmac-sha256\n"
                "    key_ref: env:TEST_KEY\n    state: active\n"
                "    not_before: '2026-01-01T00:00:00Z'\n",
                encoding="utf-8",
            )

            self.assertEqual(load_trust_policy(json_path).keys[1].key_id, "maintainer-2026-b")
            self.assertEqual(load_trust_policy(yaml_path).keys[0].key_ref, "env:TEST_KEY")

    def test_rejects_unknown_fields_and_duplicate_key_ids(self):
        policy = json.loads(json.dumps(VALID_POLICY))
        policy["unexpected"] = True
        policy["keys"].append(dict(policy["keys"][0]))

        with self.assertRaises(TrustPolicyError) as raised:
            parse_trust_policy(policy)

        codes = {detail["code"] for detail in raised.exception.details}
        self.assertIn("unknown_field", codes)
        self.assertIn("duplicate_key_id", codes)

    def test_rejects_duplicate_json_and_yaml_mapping_keys(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            json_path = root / "duplicate.json"
            yaml_path = root / "duplicate.yaml"
            json_path.write_text('{"policy_version":"1.0","policy_version":"1.0"}', encoding="utf-8")
            yaml_path.write_text("policy_version: '1.0'\npolicy_version: '1.0'\n", encoding="utf-8")

            for path in (json_path, yaml_path):
                with self.subTest(path=path), self.assertRaises(TrustPolicyError) as raised:
                    load_trust_policy(path)
                self.assertEqual(raised.exception.code, "policy_parse_error")
                self.assertEqual(raised.exception.details[0]["code"], "duplicate_mapping_key")

    def test_rejects_embedded_key_material_and_unsupported_resolver(self):
        for key_ref, expected_code in (
            ("hex:" + "a" * 64, "embedded_key_material"),
            ("https://example.test/key", "unsupported_resolver"),
            ("env:bad-name", "invalid_key_reference"),
            ("file://remote/key", "invalid_key_reference"),
        ):
            policy = json.loads(json.dumps(VALID_POLICY))
            policy["keys"] = [dict(policy["keys"][0], key_ref=key_ref)]
            with self.subTest(key_ref=key_ref), self.assertRaises(TrustPolicyError) as raised:
                parse_trust_policy(policy)
            self.assertIn(expected_code, {detail["code"] for detail in raised.exception.details})

    def test_rejects_bad_timestamps_and_state_conflicts(self):
        policy = json.loads(json.dumps(VALID_POLICY))
        policy["keys"] = [
            dict(
                policy["keys"][0],
                state="active",
                not_before="2026-06-01T00:00:00",
                revoked_at="2026-05-01T00:00:00Z",
            )
        ]

        with self.assertRaises(TrustPolicyError) as raised:
            parse_trust_policy(policy)

        codes = {detail["code"] for detail in raised.exception.details}
        self.assertIn("invalid_timestamp", codes)
        self.assertIn("timestamp_conflict", codes)

    def test_rejects_null_optional_fields_instead_of_treating_them_as_absent(self):
        for field in ("comment", "revoked_at"):
            policy = json.loads(json.dumps(VALID_POLICY))
            policy["keys"] = [dict(policy["keys"][0], **{field: None})]
            with self.subTest(field=field), self.assertRaises(TrustPolicyError) as raised:
                parse_trust_policy(policy)
            self.assertIn("invalid_type", {detail["code"] for detail in raised.exception.details})

    @unittest.skipIf(Draft202012Validator is None, "jsonschema optional dependency is not installed")
    def test_checked_in_and_packaged_schema_validate_shape(self):
        repo_schema = Path("schemas/trust-policy.schema.json")
        packaged_schema = Path("src/repro_evidence_kit/schemas/trust-policy.schema.json")
        self.assertEqual(repo_schema.read_text(encoding="utf-8"), packaged_schema.read_text(encoding="utf-8"))
        schema = json.loads(repo_schema.read_text(encoding="utf-8"))
        self.assertEqual(default_trust_policy_schema_path(), repo_schema.resolve())
        errors = list(Draft202012Validator(schema).iter_errors(VALID_POLICY))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
