from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, text=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def one_artifact(dist: Path, pattern: str) -> Path:
    matches = sorted(dist.glob(pattern))
    if len(matches) != 1:
        print(f"expected exactly one {pattern} artifact, found {len(matches)}", file=sys.stderr)
        raise SystemExit(2)
    return matches[0]


def main() -> int:
    dist = Path("dist")
    wheel = one_artifact(dist, "*.whl")
    sdist = one_artifact(dist, "*.tar.gz")

    run([sys.executable, "-m", "twine", "check", str(wheel), str(sdist)])
    for artifact in (wheel, sdist):
        run([sys.executable, "scripts/release_install_smoke.py", str(artifact.resolve())])

    print("distribution checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
