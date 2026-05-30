from __future__ import annotations

from pathlib import Path
import hashlib
import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    dummy = ROOT / "examples" / "dummy-binary"
    sandbox = ROOT / "examples" / "sandbox-run"
    dummy.mkdir(parents=True, exist_ok=True)
    sandbox.mkdir(parents=True, exist_ok=True)

    (dummy / "sample.bin").write_bytes(bytes(range(32)) + b"\nsynthetic fixture\n")
    (dummy / "notes.txt").write_text("Synthetic fixture for documentation and tests.\n", encoding="utf-8")
    (sandbox / "input.txt").write_text("input\n", encoding="utf-8")
    (sandbox / "result.txt").write_text("result\n", encoding="utf-8")

    bundle = {
        "schema_version": "1.0",
        "title": "Synthetic artifact evidence example",
        "description": "Dummy data generated for public examples; contains no proprietary source material.",
        "inputs": [{"path": "examples/sandbox-run/input.txt", "sha256": sha256(sandbox / "input.txt"), "size": (sandbox / "input.txt").stat().st_size, "role": "input"}],
        "commands": [{"argv": ["python", "-c", "write result"], "cwd": ".", "exit_code": 0}],
        "outputs": [{"path": "examples/sandbox-run/result.txt", "sha256": sha256(sandbox / "result.txt"), "size": (sandbox / "result.txt").stat().st_size, "role": "output"}],
        "notes": ["All example files are synthetic."],
    }
    (ROOT / "examples" / "evidence-bundle.yaml").write_text(yaml.safe_dump(bundle, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
