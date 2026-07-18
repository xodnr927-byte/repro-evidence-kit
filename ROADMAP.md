# Roadmap

## Recently completed

### Post-v0.4.2 repository hardening

- Protected `main` with pull-request, required-CI, linear-history, and
  conversation-resolution gates.
- Enabled Dependabot security updates and private vulnerability reporting.
- Added the canonical Apache License 2.0 text, support guidance, and a code of
  conduct.
- Added required Windows/Python 3.12 filesystem-contract CI.
- Proved GitHub Code Scanning consumption of the synthetic sandbox-policy SARIF
  output with job-scoped upload permissions.

### v0.4.2

- Fail-closed manifest input, symlink, duplicate-path, and metadata validation.
- Atomic file outputs and input-overwrite protection.
- Manifest and sandbox-SARIF schemas with packaged contract checks.
- Executable README command smoke coverage.
- Ruff, Mypy, branch-coverage, and arbitrary-working-directory quality gates.
- Dependency auditing, CycloneDX SBOM artifacts, Dependabot, and release build provenance.
- Boundary coverage for permission failures, large trees, Unicode paths, and corrupted structured inputs.

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
- Review future changes against the v0.4.2 file-safety and validation contracts.
- Design signer trust, key rotation, and revocation policy in
  [issue #53](https://github.com/xodnr927-byte/repro-evidence-kit/issues/53)
  before expanding the signed-sidecar prototype. The policy parser and local
  synthetic `env:`/`file:` resolver interfaces and caller-selected policy-aware
  verification are documented in
  [docs/signer-trust-policy.md](docs/signer-trust-policy.md). Policy-aware
  signing now permits only caller-selected `active` keys while preserving the
  version 1 sidecar boundary.

## Later ideas

- Publish bounded contributor issues only when their acceptance criteria and
  trust boundaries are concrete.

## Non-goals

- Storing private source data.
- Shipping proprietary binary samples.
- Becoming a target-specific reverse-engineering framework.
- Claiming semantic correctness from hashes alone.
