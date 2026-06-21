# Release/PyPI evidence records

This file records narrow release-to-PyPI consistency checks. It is not an
adoption record, a trust guarantee, or proof of package semantics beyond the
listed evidence.

## v0.4.2

Checked on 2026-06-21.

| Surface | Evidence | Result |
| --- | --- | --- |
| Package version source | `src/repro_evidence_kit/__init__.py` at tag `v0.4.2` contains `__version__ = "0.4.2"`; `pyproject.toml` uses Hatch dynamic versioning from that file. | Consistent |
| Git tag | `refs/tags/v0.4.2` points to commit `e2faa2729b13bd7c69c828547f317c1f2c6f0bd7`. | Present |
| GitHub release | <https://github.com/xodnr927-byte/repro-evidence-kit/releases/tag/v0.4.2> was published on 2026-06-13. | Present |
| Publish workflow | <https://github.com/xodnr927-byte/repro-evidence-kit/actions/runs/27451154155> completed successfully for release `v0.4.2`. | Passed |
| PyPI version | <https://pypi.org/project/repro-evidence-kit/0.4.2/> lists version `0.4.2`. | Present |
| PyPI files | PyPI has `repro_evidence_kit-0.4.2-py3-none-any.whl` and `repro_evidence_kit-0.4.2.tar.gz`. | Present |
| PyPI long description | PyPI long description SHA-256 `8d642f9faaa095c55328fb1879e397ba593c24954215ad0969c6a7f2c53c9567` matches `README.md` at tag `v0.4.2`. | Consistent |

Boundary: this record only closes the release/PyPI consistency surface for
`v0.4.2`. It does not claim adoption, independent trust, command-execution
provenance, semantic correctness, or that later `main` documentation is already
published to PyPI.
