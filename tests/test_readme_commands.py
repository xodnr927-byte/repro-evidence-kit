from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ReadmeCommandSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        shutil.copytree(REPO_ROOT / "examples", self.root / "examples")

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-m", "repro_evidence_kit", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result

    def test_quick_start_and_filtered_manifest_commands(self):
        self.run_cli("manifest", "create", "examples/dummy-binary", "-o", "before.json")
        self.run_cli("manifest", "diff", "before.json", "before.json")
        self.run_cli("evidence", "validate", "examples/evidence-bundle.yaml")

        reports = self.root / "artifacts" / "reports"
        reports.mkdir(parents=True)
        (reports / "keep.json").write_text("{}\n", encoding="utf-8")
        (reports / "skip.tmp").write_text("temporary\n", encoding="utf-8")
        self.run_cli(
            "manifest",
            "create",
            "artifacts",
            "--include",
            "reports",
            "--exclude",
            "*.tmp",
            "-o",
            "manifest.json",
        )

        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([item["path"] for item in manifest["files"]], ["reports/keep.json"])

    def test_schema_and_signed_bundle_commands(self):
        self.run_cli("evidence", "validate", "examples/evidence-bundle.yaml", "--schema")

        (self.root / "local-test.key").write_text("synthetic local test key only\n", encoding="utf-8")
        self.run_cli(
            "evidence",
            "sign",
            "examples/evidence-bundle.yaml",
            "--key",
            "local-test.key",
            "-o",
            "evidence-bundle.yaml.sig.json",
        )
        self.run_cli(
            "evidence",
            "verify-signature",
            "examples/evidence-bundle.yaml",
            "--signature",
            "evidence-bundle.yaml.sig.json",
            "--key",
            "local-test.key",
        )

    def test_sandbox_verification_command(self):
        before = {"files": []}
        after = {"files": [{"path": "report.json", "size": 2, "sha256": "a" * 64}]}
        (self.root / "before.json").write_text(json.dumps(before), encoding="utf-8")
        (self.root / "after.json").write_text(json.dumps(after), encoding="utf-8")

        self.run_cli(
            "verify",
            "sandbox-run",
            "before.json",
            "after.json",
            "--allow-added",
            "report.json",
        )
