from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from repro_evidence_kit.manifest import create_manifest, diff_manifests, load_manifest, validate_manifest, write_text

REPO_ROOT = Path(__file__).resolve().parents[1]


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

    def test_diff_formats_markdown_report(self):
        before = {"files": [{"path": "old.txt", "size": 1, "sha256": "0" * 64}]}
        after = {
            "files": [
                {"path": "old.txt", "size": 2, "sha256": "1" * 64},
                {"path": "new.txt", "size": 1, "sha256": "2" * 64},
            ]
        }
        markdown = diff_manifests(before, after).as_markdown()
        self.assertIn("# Manifest diff", markdown)
        self.assertIn("| Added | 1 |", markdown)
        self.assertIn("| Changed | 1 |", markdown)
        self.assertIn("- `new.txt`", markdown)
        self.assertIn("- `old.txt`", markdown)

    def test_create_manifest_filters_include_exclude_and_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "keep").mkdir()
            (root / "keep" / "result.txt").write_text("result", encoding="utf-8")
            (root / "keep" / "debug.tmp").write_text("debug", encoding="utf-8")
            (root / "cache").mkdir()
            (root / "cache" / "noise.txt").write_text("noise", encoding="utf-8")
            manifest = create_manifest(root, include=["keep"], exclude=["*.tmp"])
        self.assertEqual([item["path"] for item in manifest["files"]], ["keep/result.txt"])
        self.assertEqual(manifest["file_count"], 1)
        self.assertEqual(manifest["filters"]["include"], ["keep"])
        self.assertEqual(manifest["filters"]["exclude"], ["*.tmp"])
        self.assertEqual(manifest["filters"]["order"], "include_then_exclude")

    def test_create_manifest_default_unfiltered_behavior_is_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "keep.txt").write_text("keep", encoding="utf-8")
            (root / "noise.tmp").write_text("noise", encoding="utf-8")
            manifest = create_manifest(root)
        self.assertEqual([item["path"] for item in manifest["files"]], ["keep.txt", "noise.tmp"])
        self.assertNotIn("filters", manifest)

    def test_create_manifest_rejects_missing_input(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing"
            with self.assertRaisesRegex(ValueError, "does not exist"):
                create_manifest(missing)

    def test_create_manifest_rejects_symlink_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target.txt"
            target.write_text("target", encoding="utf-8")
            link = root / "link.txt"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "contains symlink"):
                create_manifest(root)

    def test_create_manifest_rejects_symlink_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"
            target.mkdir()
            (target / "file.txt").write_text("target", encoding="utf-8")
            link = root / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "contains symlink"):
                create_manifest(root)

    def test_atomic_write_preserves_original_if_replace_fails(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "result.txt"
            output.write_text("original\n", encoding="utf-8")
            with mock.patch("repro_evidence_kit.manifest.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    write_text("replacement\n", output)
            self.assertEqual(output.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])

    def test_validate_manifest_rejects_duplicate_normalized_paths(self):
        errors = validate_manifest({
            "files": [
                {"path": r"reports\result.json", "size": 1, "sha256": "a" * 64},
                {"path": "reports/result.json", "size": 1, "sha256": "a" * 64},
            ]
        })
        self.assertIn("duplicate manifest path: reports/result.json", errors)

    def test_validate_manifest_rejects_missing_or_malformed_entry_fields(self):
        errors = validate_manifest({
            "files": [
                {"size": -1, "sha256": "bad"},
                "not-an-object",
            ]
        })
        self.assertIn("files[0].path must be a non-empty string", errors)
        self.assertIn("files[0].size must be a non-negative integer", errors)
        self.assertIn("files[0].sha256 must be 64 hexadecimal characters", errors)
        self.assertIn("files[1] must be an object", errors)

    def test_validate_manifest_rejects_inconsistent_metadata(self):
        errors = validate_manifest({
            "manifest_version": "2.0",
            "file_count": 2,
            "total_bytes": 9,
            "files": [{"path": "a", "size": 1, "sha256": "a" * 64}],
        })
        self.assertIn("unsupported manifest_version: 2.0", errors)
        self.assertIn("file_count does not match files length: 2 != 1", errors)
        self.assertIn("total_bytes does not match file sizes: 9 != 1", errors)

    def test_load_manifest_reports_validation_errors(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.json"
            path.write_text('{"files": [{"size": 1}]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"files\[0\]\.path"):
                load_manifest(path)

    def test_manifest_schema_copy_matches_packaged_copy(self):
        repo_schema = (REPO_ROOT / "schemas/manifest.schema.json").read_text(encoding="utf-8")
        packaged_schema = (REPO_ROOT / "src/repro_evidence_kit/schemas/manifest.schema.json").read_text(encoding="utf-8")
        self.assertEqual(packaged_schema, repo_schema)


if __name__ == "__main__":
    unittest.main()
