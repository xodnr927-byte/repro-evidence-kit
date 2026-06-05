from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET

from repro_evidence_kit.verify import sandbox_result_as_junit, verify_sandbox_output


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

    def test_sandbox_result_as_junit_reports_failure_for_unexpected_changes(self):
        result = {
            "ok": False,
            "unexpected": {"added": ["report.json"], "changed": [], "removed": []},
        }
        root = ET.fromstring(sandbox_result_as_junit(result))
        self.assertEqual(root.tag, "testsuite")
        self.assertEqual(root.attrib["tests"], "1")
        self.assertEqual(root.attrib["failures"], "1")
        failure = root.find("./testcase/failure")
        self.assertIsNotNone(failure)
        self.assertIn("report.json", failure.text or "")

    def test_sandbox_result_as_junit_reports_success_without_failure(self):
        root = ET.fromstring(sandbox_result_as_junit({"ok": True, "unexpected": {}}))
        self.assertEqual(root.attrib["failures"], "0")
        self.assertIsNone(root.find("./testcase/failure"))


if __name__ == "__main__":
    unittest.main()

class VerifyReportingTests(unittest.TestCase):
    def test_required_added_path_must_be_observed(self):
        result = verify_sandbox_output({"files": []}, {"files": []}, allow_added={"report.json"}, require_added={"report.json"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["missing_required"]["added"], ["report.json"])

    def test_sandbox_result_as_sarif_reports_unexpected_path(self):
        from repro_evidence_kit.verify import sandbox_result_as_sarif
        import json

        result = verify_sandbox_output(
            {"files": []},
            {"files": [{"path": "report.json", "size": 2, "sha256": "a" * 64}]},
        )
        sarif = json.loads(sandbox_result_as_sarif(result))
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(sarif["runs"][0]["results"][0]["ruleId"], "unexpected-sandbox-change")
