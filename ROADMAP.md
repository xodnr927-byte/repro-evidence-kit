# Roadmap

## Recently completed

These are implemented on `main` after `v0.2.0` and are candidates for the next release:

- Markdown output for `manifest diff` reports.
- Include/exclude filters for large artifact-tree manifests.
- Optional JSON Schema validation for evidence bundles.
- Stable CLI exit-code documentation and regression coverage.
- GitHub Actions cookbook and CI leakage audit.
- Minimal signed evidence bundle sidecar prototype.

## Near-term polish

- Keep examples synthetic-only.
- Improve README, tutorials, and cookbook examples as new workflows land.
- Prepare compact release notes for the next release.
- Expand CI cookbook coverage for schema validation and filtered manifest workflows.

## Later ideas

- SARIF output for CI code-scanning integrations.
- Richer signed bundle trust policies after the sidecar contract is stable.

## Non-goals

- Storing private source data.
- Shipping proprietary binary samples.
- Becoming a target-specific reverse-engineering framework.
- Claiming semantic correctness from hashes alone.
