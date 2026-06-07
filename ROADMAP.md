# Roadmap

## Recently completed

These are available in `v0.4.0`:

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
- Add SARIF or additional JUnit adapters only after the JSON/text contracts stay stable.

## Later ideas

- SARIF output for CI code-scanning integrations.
- Richer signed bundle trust policies after the sidecar contract is stable.

## Non-goals

- Storing private source data.
- Shipping proprietary binary samples.
- Becoming a target-specific reverse-engineering framework.
- Claiming semantic correctness from hashes alone.
