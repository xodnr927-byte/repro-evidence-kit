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

- triaging issues into schema, CLI, docs, or test work,
- drafting changelog entries from merged PRs,
- reviewing whether examples are synthetic and redistributable,
- debugging CI failures,
- proposing narrow tests for manifest and verifier behavior.

Codex should not add private datasets, proprietary samples, credentials, or target-specific reverse-engineering artifacts.

## Release checklist

Before a release:

1. Run unit tests.
2. Validate example evidence bundles.
3. Run the leakage audit.
4. Confirm README examples still work.
5. Update `CHANGELOG.md` and tag the release.
