from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def run(cmd: list[str], *, cwd: Path | None = None, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != expect:
        print(f"command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"expected exit {expect}, got {result.returncode}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(2)
    return result


def bin_path(venv_dir: Path, name: str) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fresh-environment release/install smoke check.")
    parser.add_argument("source", help="Tagged source reference, local path, or git+ URL to install")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        env = root / "venv"
        venv.EnvBuilder(with_pip=True).create(env)
        python = bin_path(env, "python")
        repro = bin_path(env, "repro-evidence")
        run([str(python), "-m", "pip", "install", args.source])
        run([str(repro), "--version"])
        run([
            str(python),
            "-c",
            (
                "from importlib.resources import files; "
                "root=files('repro_evidence_kit.schemas'); "
                "names=('evidence-bundle.schema.json','signature-sidecar.schema.json',"
                "'manifest.schema.json','sandbox-sarif.schema.json'); "
                "assert all(root.joinpath(name).is_file() for name in names)"
            ),
        ])

        bundle = root / "evidence-bundle.yaml"
        key = root / "local-test.key"
        signature = root / "evidence-bundle.yaml.sig.json"
        bundle.write_text("schema_version: '1.0'\ntitle: Synthetic\ninputs: []\ncommands: []\noutputs: []\n", encoding="utf-8")
        key.write_text("synthetic local test key only\n", encoding="utf-8")
        run([str(repro), "evidence", "sign", str(bundle), "--key", str(key), "--key-hint", "local-synthetic", "-o", str(signature)])
        run([str(repro), "evidence", "verify-signature", str(bundle), "--signature", str(signature), "--key", str(key)])
        bundle.write_text(bundle.read_text(encoding="utf-8") + "tamper: true\n", encoding="utf-8")
        run([str(repro), "evidence", "verify-signature", str(bundle), "--signature", str(signature), "--key", str(key)], expect=1)

    print("release/install smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
