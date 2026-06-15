# Release checklist

Use this checklist before tagging a release. It is maintainer guidance, not a trust guarantee.

## Before tagging

1. Confirm the working tree is clean except intentional release edits.
2. Run the base tests:
   ```bash
   uv run pytest -q
   ```
3. Run schema-extra tests when schema files changed:
   ```bash
   uv run --extra schema pytest -q
   ```
4. Run the example smoke script:
   ```bash
   python scripts/smoke_examples.py
   ```
5. Build and check the wheel and source distribution:
   ```bash
   python -m pip install build twine
   python -m build
   python scripts/check_dist.py
   ```
6. Review `CHANGELOG.md`, `README.md`, and `ROADMAP.md` for version wording.
7. Confirm the release tag will be exactly `v<project-version>`.

## After tagging

1. Confirm the GitHub release points to the intended tag and commit, and that
   the publish workflow completed successfully.
2. Download the published wheel and source distribution from the workflow
   evidence surface and verify their GitHub build-provenance attestations:
   ```bash
   gh attestation verify PATH_TO_WHEEL_OR_SDIST \
     -R xodnr927-byte/repro-evidence-kit
   ```
3. Confirm the dependency-audit job produced its CycloneDX SBOM artifact.
   Record the workflow-run URL because workflow artifacts are retention-bound.
4. After PyPI shows the new version, install both the base package and schema
   extra from PyPI in separate fresh environments:
   ```bash
   python -m pip install "repro-evidence-kit==X.Y.Z"
   python -m pip install "repro-evidence-kit[schema]==X.Y.Z"
   ```
5. Check the CLI version:
   ```bash
   repro-evidence --version
   ```
6. Run the README quick-start commands from a directory outside the source
   checkout.
7. Run minimal evidence signing and verification with synthetic local key
   material.
8. Mutate the bundle bytes and confirm verification returns exit code `1`.
9. Confirm the latest `main` Code Scanning analysis includes category
   `repro-evidence-sandbox-policy` with no ingestion error:
   ```bash
   gh api \
     "repos/xodnr927-byte/repro-evidence-kit/code-scanning/analyses?per_page=10" \
     --jq '.[] | select(.category == "repro-evidence-sandbox-policy") |
       {ref, commit_sha, category, error, created_at}'
   ```
   A successful upload proves GitHub accepted the SARIF document. It does not
   prove package correctness or that every future upload will succeed.
10. Record the release URL, publish-workflow URL, PyPI version, attestation
    result, SBOM artifact location, quick-start result, and Code Scanning
    analysis ID in the release notes or maintainer evidence record.
11. Do not publish live keys, private fixtures, proprietary samples, or
    target-specific evidence.

For the one-time Trusted Publisher setup and automated release flow, see
[Publishing to PyPI](publishing.md).
