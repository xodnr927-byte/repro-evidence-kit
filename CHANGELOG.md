# Changelog

## Unreleased

## 0.4.2 - 2026-06-13

- Update installation documentation after the first verified PyPI publication.
- Reject missing manifest inputs and symbolic links instead of producing ambiguous manifests.
- Prevent CLI outputs from overwriting input files and write file outputs atomically.
- Add executable smoke coverage for documented README command flows.
- Add manifest and sandbox-SARIF schemas plus fail-closed manifest entry, metadata, and duplicate-path validation.
- Add enforced Ruff, Mypy, branch-coverage, and repository-independent test execution gates.
- Add dependency auditing, CycloneDX SBOM artifacts, Dependabot updates, and release build-provenance attestations.
- Add regression coverage for permission failures, interrupted writes, large manifests, Unicode paths, path collisions, and corrupted JSON/YAML/Schema inputs.
- Use one package version source for build metadata and CLI version output.

## 0.4.1 - 2026-06-07

- Add a Python 3.10, 3.11, and 3.12 CI matrix using non-editable package installs.
- Add checked wheel/sdist builds and a release-triggered PyPI Trusted Publishing workflow.

## 0.4.0 - 2026-06-06

- Add signature sidecar JSON Schema validation and packaged-schema regression coverage.
- Improve `evidence verify-signature` with text output, structured error details, and optional sidecar schema checks.
- Add `evidence sign --dry-run` for non-writing sidecar previews.
- Add sandbox required-change checks, SARIF output, and JUnit output for evidence validation.
- Add synthetic signed-bundle examples, use-case docs, release checklist, example smoke script, and release/install smoke script.

## 0.3.0 - 2026-06-05

- Add `evidence sign` and `evidence verify-signature` for local `hmac-sha256` evidence-bundle sidecars.
- Document signed-bundle boundaries: local tamper detection only, unsigned bundles remain supported, and signatures do not prove command execution or artifact semantics.
- Add regression coverage for successful signature verification and payload-mismatch failures.

## 0.2.0 - 2026-06-02

- Add JUnit XML output for `verify sandbox-run` CI report consumers.
- Add a signed evidence bundles design note that defines the sidecar-first support boundary.

## 0.1.2 - 2026-06-02

- Add optional JSON Schema validation for evidence bundles.
- Add include/exclude filters for manifest creation.
- Add Markdown output for `manifest diff` reports.
- Document stable CLI exit-code meanings and add regression coverage.
- Expand GitHub Actions cookbook coverage for schema-backed filtered manifest workflows.
- Clarify source-based installation until a package index release exists.

## 0.1.1 - 2026-05-31

- Add Windows-style path separator normalization for manifest diff and sandbox verification.
- Expand README maintainer positioning.

## 0.1.0 - 2026-05-30

- Initial release candidate.
- Add manifest creation and diffing.
- Add sandbox output verification.
- Add evidence bundle validation.
- Add synthetic examples and documentation.
