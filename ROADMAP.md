# Roadmap

## Recently completed

### v0.4.1

- PyPI publication completed.
- Trusted Publishing/OIDC release flow completed.
- Package-index installation documentation completed.
- Wheel/sdist build and check completed.
- Schema extra and package-data verification completed.
- Fresh-install smoke validation completed.
- Node 24 GitHub Actions hygiene completed via PR #36.

### v0.4.0

- Markdown output for `manifest diff` reports.
- Include/exclude filters for large artifact-tree manifests.
- Optional JSON Schema validation for evidence bundles.
- Stable CLI exit-code documentation and regression coverage.
- GitHub Actions cookbook and CI leakage audit.
- Minimal signed evidence bundle sidecar prototype.
- Signature sidecar JSON Schema and packaged schema regression tests.
- Reviewer-friendly `verify-signature --format text` output and structured JSON error details.
- `evidence sign --dry-run` for non-writing sidecar preview.
- Synthetic signed-bundle example, release checklist, use-cases page, and example smoke script.
- Sandbox SARIF output, required-change checks, and evidence-validation JUnit output.
- Fresh-environment release/install smoke script for tagged source references.

## Near-term polish

- Keep examples synthetic-only.
- Expand CI recipes for signed-bundle verification and example smoke checks.
- Add contract and schema tests for the existing SARIF output.

## Later ideas

- Optional GitHub code scanning integration for the existing SARIF output.
- Richer signed bundle trust policies after the sidecar contract is stable.

## Non-goals

- Storing private source data.
- Shipping proprietary binary samples.
- Becoming a target-specific reverse-engineering framework.
- Claiming semantic correctness from hashes alone.
