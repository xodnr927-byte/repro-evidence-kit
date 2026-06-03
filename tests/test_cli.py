from __future__ import annotations

import contextlib
import io
import json
import tempfile
import xml.etree.ElementTree as ET
import unittest
from pathlib import Path

from repro_evidence_kit.cli import main
from repro_evidence_kit.evidence import Draft202012Validator


class CliTests(unittest.TestCase):
    def test_manifest_create_cli(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "x.txt").write_text("x", encoding="utf-8")
            output = root / "manifest.json"
            code = main(["manifest", "create", str(root / "x.txt"), "-o", str(output)])
            self.assertEqual(code, 0)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["file_count"], 1)

    def test_evidence_validate_invalid_bundle_returns_1(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bad.yaml"
            output = root / "result.json"
            bundle.write_text("title: Missing required fields\n", encoding="utf-8")
            code = main(["evidence", "validate", str(bundle), "-o", str(output)])
            self.assertEqual(code, 1)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(data["ok"])
            self.assertIn("missing top-level field: inputs", data["errors"])

    def test_verify_sandbox_unexpected_output_returns_1(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            before = root / "before.json"
            after = root / "after.json"
            output = root / "verify.json"
            before.write_text(json.dumps({"files": []}), encoding="utf-8")
            after.write_text(
                json.dumps({"files": [{"path": "report.json", "size": 2, "sha256": "a" * 64}]}),
                encoding="utf-8",
            )
            code = main(["verify", "sandbox-run", str(before), str(after), "-o", str(output)])
            self.assertEqual(code, 1)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["unexpected"]["added"], ["report.json"])

    def test_missing_input_file_returns_2(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["manifest", "diff", str(root / "missing-before.json"), str(root / "missing-after.json")])
            self.assertEqual(code, 2)
            self.assertIn("error:", stderr.getvalue())

    def test_manifest_diff_markdown_cli(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            before = root / "before.json"
            after = root / "after.json"
            output = root / "diff.md"
            before.write_text(json.dumps({"files": []}), encoding="utf-8")
            after.write_text(
                json.dumps({"files": [{"path": "report.md", "size": 2, "sha256": "a" * 64}]}),
                encoding="utf-8",
            )
            code = main(["manifest", "diff", str(before), str(after), "--format", "markdown", "-o", str(output)])
            self.assertEqual(code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("# Manifest diff", text)
            self.assertIn("| Added | 1 |", text)
            self.assertIn("- `report.md`", text)

    def test_manifest_create_cli_include_exclude_filters(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir()
            (root / "reports" / "keep.txt").write_text("keep", encoding="utf-8")
            (root / "reports" / "skip.log").write_text("skip", encoding="utf-8")
            (root / "cache.txt").write_text("cache", encoding="utf-8")
            output = root / "manifest.json"
            code = main([
                "manifest",
                "create",
                str(root),
                "--include",
                "reports",
                "--exclude",
                "*.log",
                "-o",
                str(output),
            ])
            self.assertEqual(code, 0)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual([item["path"] for item in data["files"]], ["reports/keep.txt"])
            self.assertEqual(data["filters"]["include"], ["reports"])
            self.assertEqual(data["filters"]["exclude"], ["*.log"])

    def test_verify_sandbox_junit_output_keeps_failure_exit_code(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            before = root / "before.json"
            after = root / "after.json"
            output = root / "verify.xml"
            before.write_text(json.dumps({"files": []}), encoding="utf-8")
            after.write_text(
                json.dumps({"files": [{"path": "report.json", "size": 2, "sha256": "a" * 64}]}),
                encoding="utf-8",
            )
            code = main(["verify", "sandbox-run", str(before), str(after), "--format", "junit", "-o", str(output)])
            self.assertEqual(code, 1)
            root_xml = ET.fromstring(output.read_text(encoding="utf-8"))
            self.assertEqual(root_xml.attrib["failures"], "1")
            self.assertIn("report.json", root_xml.findtext("./testcase/failure") or "")

    def test_evidence_sign_and_verify_signature_cli(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle.yaml"
            key = root / "local-test.key"
            signature = root / "bundle.yaml.sig.json"
            verify_output = root / "verify-signature.json"
            bundle.write_text("title: Synthetic\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")

            sign_code = main(["evidence", "sign", str(bundle), "--key", str(key), "--key-hint", "local-test", "-o", str(signature)])
            verify_code = main([
                "evidence",
                "verify-signature",
                str(bundle),
                "--signature",
                str(signature),
                "--key",
                str(key),
                "-o",
                str(verify_output),
            ])

            self.assertEqual(sign_code, 0)
            self.assertEqual(verify_code, 0)
            sidecar = json.loads(signature.read_text(encoding="utf-8"))
            result = json.loads(verify_output.read_text(encoding="utf-8"))
            self.assertEqual(sidecar["algorithm"], "hmac-sha256")
            self.assertTrue(result["ok"])

    def test_evidence_verify_signature_cli_returns_1_for_payload_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle.yaml"
            key = root / "local-test.key"
            signature = root / "bundle.yaml.sig.json"
            output = root / "verify-signature.json"
            bundle.write_text("title: Before\n", encoding="utf-8")
            key.write_text("synthetic test key only\n", encoding="utf-8")
            self.assertEqual(main(["evidence", "sign", str(bundle), "--key", str(key), "-o", str(signature)]), 0)
            bundle.write_text("title: After\n", encoding="utf-8")

            code = main(["evidence", "verify-signature", str(bundle), "--signature", str(signature), "--key", str(key), "-o", str(output)])

            self.assertEqual(code, 1)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(result["ok"])
            self.assertIn("payload_sha256 mismatch", result["errors"])

    @unittest.skipIf(Draft202012Validator is None, "jsonschema optional dependency is not installed")
    def test_evidence_validate_schema_cli_returns_1_for_schema_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle.json"
            output = root / "result.json"
            bundle.write_text(json.dumps({
                "schema_version": "1.0",
                "title": "Example",
                "inputs": [{"path": "input.bin", "sha256": "not-a-hex-digest"}],
                "commands": [{"argv": ["tool", "input.bin"]}],
                "outputs": [{"path": "output.bin", "sha256": "b" * 64}],
            }), encoding="utf-8")
            code = main(["evidence", "validate", str(bundle), "--schema", "-o", str(output)])
            self.assertEqual(code, 1)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(data["ok"])
            self.assertEqual(data["validator"], "jsonschema Draft 2020-12")


if __name__ == "__main__":
    unittest.main()
