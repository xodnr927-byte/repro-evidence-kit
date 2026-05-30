from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
