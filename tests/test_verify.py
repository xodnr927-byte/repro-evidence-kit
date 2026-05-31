from __future__ import annotations

import unittest

from repro_evidence_kit.verify import verify_sandbox_output


class VerifyTests(unittest.TestCase):
    def test_unexpected_added_path_fails(self):
        before = {"files": []}
        after = {"files": [{"path": "report.json", "size": 2, "sha256": "a" * 64}]}
        result = verify_sandbox_output(before, after)
        self.assertFalse(result["ok"])
        self.assertEqual(result["unexpected"]["added"], ["report.json"])

    def test_allowed_added_path_passes(self):
        before = {"files": []}
        after = {"files": [{"path": "report.json", "size": 2, "sha256": "a" * 64}]}
        result = verify_sandbox_output(before, after, allow_added={"report.json"})
        self.assertTrue(result["ok"])

    def test_allowlist_normalizes_windows_style_paths(self):
        before = {"files": []}
        after = {"files": [{"path": "reports\\summary.json", "size": 2, "sha256": "a" * 64}]}
        result = verify_sandbox_output(before, after, allow_added={"reports/summary.json"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["allowed"]["added"], ["reports/summary.json"])


if __name__ == "__main__":
    unittest.main()
