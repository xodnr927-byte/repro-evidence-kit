# Publishing to PyPI

This repository is prepared for tokenless PyPI publishing with GitHub Actions
Trusted Publishing. Publishing is release-triggered; pull requests and ordinary
branch pushes cannot upload distributions.

## One-time maintainer setup

Before the first PyPI release:

1. Sign in to PyPI and create a pending Trusted Publisher for the project
   `repro-evidence-kit`.
2. Configure the GitHub publisher with:
   - owner: `xodnr927-byte`
   - repository: `repro-evidence-kit`
   - workflow: `publish.yml`
   - environment: `pypi`
3. Create a GitHub environment named `pypi`. Add required reviewers if desired.
4. Do not create a `PYPI_TOKEN` secret. The publish job requests a short-lived
   OIDC credential with job-scoped `id-token: write` permission.

The PyPI publisher configuration must exactly match the workflow filename and
environment name.

## Release flow

1. Update the version and changelog through a reviewed pull request.
2. Run the release checklist.
3. Tag the exact release commit as `v<project-version>`.
4. Publish the matching GitHub release.
5. The `Publish to PyPI` workflow:
   - confirms the tag matches `pyproject.toml`,
   - builds one wheel and one source distribution,
   - runs `twine check`,
   - smoke-installs and exercises both distributions,
   - generates GitHub build-provenance attestations for the wheel and source distribution,
   - passes only the checked distributions to the OIDC-enabled publish job.
6. Confirm the project and files appear on PyPI before changing README install
   instructions from tagged-source installation to package-index installation.

The workflow does not prove package semantics beyond its tests and smoke checks.
Trusted Publishing identifies the authorized release workflow; it does not make
the package or its outputs inherently trustworthy.

## Dependency automation

CI audits the project dependency graph with `pip-audit` and uploads a CycloneDX
dependency SBOM as a workflow artifact. Dependabot checks both Python and
GitHub Actions dependencies weekly. These controls report known dependency
issues and update opportunities; they do not prove that dependencies or the
resulting package are free of unknown vulnerabilities.

Release artifacts can be verified against their GitHub build provenance with:

```bash
gh attestation verify PATH_TO_WHEEL_OR_SDIST -R xodnr927-byte/repro-evidence-kit
```
