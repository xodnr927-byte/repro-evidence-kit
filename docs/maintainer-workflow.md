# Maintainer workflow

`repro-evidence-kit` is designed for maintainers who need small, reviewable proof around generated artifacts.

## Pull request review

A maintainer can ask contributors to include:

- a baseline manifest for relevant inputs,
- an after-run manifest for generated outputs,
- a diff report,
- an evidence bundle describing the command and artifacts.

This keeps PR review focused on declared byte changes instead of large raw logs.

## CI checks

Recommended checks:

```bash
python -m unittest discover -s tests
python -m repro_evidence_kit evidence validate examples/evidence-bundle.yaml
python -m repro_evidence_kit manifest create examples/dummy-binary -o /tmp/manifest.json
```

This repository's CI runs these checks after a non-editable package install on
Python 3.10, 3.11, and 3.12. It also runs a leakage audit that rejects
project-specific or proprietary-sample markers.

For copyable GitHub Actions snippets, see the [GitHub Actions cookbook](github-actions.md).

## Codex-assisted maintenance

Useful Codex tasks for this project include:

- issue triage,
- documentation drafts,
- changelog drafts,
- CI failure diagnosis,
- narrow test proposals.

Codex-assisted work must not introduce private datasets, proprietary samples,
credentials, target-specific reverse-engineering artifacts, or expanded
trust/security claims. A human maintainer must review release, publishing, and
security-sensitive changes before merge.

## Releases and publishing

Use the [release checklist](release-checklist.md) for the maintained pre-tag and
post-tag validation steps instead of reproducing them here.

See [Publishing to PyPI](publishing.md) for the Trusted Publishing setup and
release flow. PyPI publishing is triggered by a release and uses tokenless
Trusted Publishing/OIDC credentials. This authorization mechanism does not
prove package correctness.
