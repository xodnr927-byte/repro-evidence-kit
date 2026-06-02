from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from repro_evidence_kit.cli import main


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


if __name__ == "__main__":
    unittest.main()
