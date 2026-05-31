from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repro_evidence_kit.manifest import create_manifest, diff_manifests


class ManifestTests(unittest.TestCase):
    def test_create_manifest_hashes_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.txt").write_text("alpha", encoding="utf-8")
            manifest = create_manifest(root)
        self.assertEqual(manifest["file_count"], 1)
        self.assertEqual(manifest["files"][0]["path"], "a.txt")
        self.assertEqual(len(manifest["files"][0]["sha256"]), 64)

    def test_create_manifest_uses_posix_paths_for_nested_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            nested = root / "logs"
            nested.mkdir()
            (nested / "run.txt").write_text("ok", encoding="utf-8")
            manifest = create_manifest(root)
        self.assertEqual(manifest["files"][0]["path"], "logs/run.txt")

    def test_diff_manifests(self):
        before = {"files": [{"path": "a.txt", "size": 1, "sha256": "0" * 64}]}
        after = {"files": [{"path": "a.txt", "size": 2, "sha256": "1" * 64}, {"path": "b.txt", "size": 1, "sha256": "2" * 64}]}
        diff = diff_manifests(before, after).as_dict()
        self.assertEqual(diff["changed"], ["a.txt"])
        self.assertEqual(diff["added"], ["b.txt"])

    def test_diff_normalizes_windows_style_manifest_paths(self):
        before = {"files": [{"path": "logs\\run.txt", "size": 2, "sha256": "0" * 64}]}
        after = {"files": [{"path": "logs/run.txt", "size": 2, "sha256": "0" * 64}]}
        diff = diff_manifests(before, after).as_dict()
        self.assertEqual(diff["unchanged"], ["logs/run.txt"])
        self.assertEqual(diff["added"], [])
        self.assertEqual(diff["removed"], [])


if __name__ == "__main__":
    unittest.main()
