# Roadmap

## Recently completed

These are available in `v0.3.0`:

- Markdown output for `manifest diff` reports.
- Include/exclude filters for large artifact-tree manifests.
- Optional JSON Schema validation for evidence bundles.
- Stable CLI exit-code documentation and regression coverage.
- GitHub Actions cookbook and CI leakage audit.
- Minimal signed evidence bundle sidecar prototype.

## Near-term polish

- Keep examples synthetic-only.
- Add a signature sidecar JSON Schema for the current prototype.
- Improve `verify-signature` error output and reviewer-facing UX.
- Keep release/install smoke checklists current as source installs evolve.

## Later ideas

- SARIF output for CI code-scanning integrations.
- Richer signed bundle trust policies after the sidecar contract is stable.

## Non-goals

- Storing private source data.
- Shipping proprietary binary samples.
- Becoming a target-specific reverse-engineering framework.
- Claiming semantic correctness from hashes alone.
