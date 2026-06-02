# Roadmap

## Recently completed

These are implemented on `main` and are candidates for the next `v0.1.x` release:

- Markdown output for `manifest diff` reports.
- Include/exclude filters for large artifact-tree manifests.
- Optional JSON Schema validation for evidence bundles.
- Stable CLI exit-code documentation and regression coverage.
- GitHub Actions cookbook and CI leakage audit.

## Near-term polish

- Keep examples synthetic-only.
- Improve README, tutorials, and cookbook examples as new workflows land.
- Prepare compact release notes for the next `v0.1.x` release.
- Expand CI cookbook coverage for schema validation and filtered manifest workflows.

## Later ideas

- SARIF or JUnit output for CI integrations.
- Signed evidence bundle support.

## Non-goals

- Storing private source data.
- Shipping proprietary binary samples.
- Becoming a target-specific reverse-engineering framework.
- Claiming semantic correctness from hashes alone.
