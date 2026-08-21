from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(args: list[str], *, expect: int = 0) -> subprocess.CompletedProcess[str]:
    cmd = [PYTHON, "-m", "repro_evidence_kit", *args]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env)
    if result.returncode != expect:
        print(f"command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"expected exit {expect}, got {result.returncode}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(2)
    return result


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        before = tmp / "before.json"
        after = tmp / "after.json"
        diff = tmp / "diff.md"
        verify = tmp / "verify.json"
        key = tmp / "local-test.key"
        signature = tmp / "evidence-bundle.yaml.sig.json"
        policy_signature = tmp / "evidence-bundle.policy.sig.json"
        disallowed_signature = tmp / "evidence-bundle.disallowed.sig.json"
        policy = tmp / "trust-policy.yaml"
        sig_text = tmp / "verify-signature.txt"

        run(["manifest", "create", "examples/dummy-binary", "-o", str(before)])
        run(["manifest", "diff", str(before), str(before), "--format", "markdown", "-o", str(diff)])
        run(["evidence", "validate", "examples/evidence-bundle.yaml"])

        sandbox = tmp / "sandbox"
        sandbox.mkdir()
        (sandbox / "input.txt").write_text("input\n", encoding="utf-8")
        run(["manifest", "create", str(sandbox), "-o", str(before)])
        (sandbox / "report.json").write_text('{"ok": true}\n', encoding="utf-8")
        run(["manifest", "create", str(sandbox), "-o", str(after)])
        run(["verify", "sandbox-run", str(before), str(after), "--allow-added", "report.json", "-o", str(verify)])

        key.write_text("synthetic local test key only\n", encoding="utf-8")
        policy.write_text(
            "policy_version: '1.0'\npolicy_id: example-smoke-policy\nkeys:\n"
            "  - key_id: local-synthetic\n    algorithm: hmac-sha256\n"
            f"    key_ref: file:{key.name}\n    state: active\n"
            "    not_before: '2026-01-01T00:00:00Z'\n",
            encoding="utf-8",
        )
        run(["evidence", "sign", "examples/evidence-bundle.yaml", "--key", str(key), "--key-hint", "local-synthetic", "-o", str(signature)])
        run([
            "evidence",
            "verify-signature",
            "examples/evidence-bundle.yaml",
            "--signature",
            str(signature),
            "--key",
            str(key),
            "--format",
            "text",
            "-o",
            str(sig_text),
        ])
        sidecar = json.loads(signature.read_text(encoding="utf-8"))
        if sidecar["algorithm"] != "hmac-sha256":
            raise SystemExit(2)
        run(
            [
                "evidence",
                "sign",
                "examples/evidence-bundle.yaml",
                "--trust-policy",
                str(policy),
                "--key-id",
                "local-synthetic",
                "-o",
                str(policy_signature),
            ]
        )
        policy_sidecar = json.loads(policy_signature.read_text(encoding="utf-8"))
        if policy_sidecar.get("signature_version") != "1.0":
            raise SystemExit(2)
        run(
            [
                "evidence",
                "verify-signature",
                "examples/evidence-bundle.yaml",
                "--signature",
                str(policy_signature),
                "--trust-policy",
                str(policy),
                "--key-id",
                "local-synthetic",
            ]
        )
        policy.write_text(policy.read_text(encoding="utf-8").replace("state: active", "state: verify_only"), encoding="utf-8")
        disallowed = run(
            [
                "evidence",
                "sign",
                "examples/evidence-bundle.yaml",
                "--trust-policy",
                str(policy),
                "--key-id",
                "local-synthetic",
                "-o",
                str(disallowed_signature),
            ],
            expect=1,
        )
        if "key_not_allowed_for_signing" not in disallowed.stderr or disallowed_signature.exists():
            raise SystemExit(2)

    print("example smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
