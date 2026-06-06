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
5. Review `CHANGELOG.md`, `README.md`, and `ROADMAP.md` for version wording.

## After tagging

1. Install from the tagged source reference in a fresh environment.
2. Check the CLI version:
   ```bash
   repro-evidence --version
   ```
3. Run minimal evidence signing and verification with synthetic local key material.
4. Mutate the bundle bytes and confirm verification returns exit code `1`.
5. Do not publish live keys, private fixtures, proprietary samples, or target-specific evidence.
