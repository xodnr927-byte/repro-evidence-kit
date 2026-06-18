# Maintainer workflow

`repro-evidence-kit` is designed for maintainers who need small, reviewable proof around generated artifacts.

## External review hold

Use the [external review ledger](external-review-ledger.md) to collect outside feedback during review windows. The ledger is a holding surface: do not convert external comments into implementation, merge, release, or issue-closure claims until the active hold expires and the relevant PRs are rechecked.

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

## Repository governance evidence

Repository settings are live control-plane state and can drift independently
of tracked files. Before a release or external governance review, query the
current settings instead of relying on this document alone:

```bash
gh api repos/xodnr927-byte/repro-evidence-kit/branches/main/protection
gh api repos/xodnr927-byte/repro-evidence-kit \
  --jq '{delete_branch_on_merge,allow_squash_merge,allow_merge_commit,allow_rebase_merge}'
```

The verified June 15, 2026 snapshot required pull requests, strict up-to-date
status checks, conversation resolution, linear history, stale-review
dismissal, and seven CI contexts. Force pushes and branch deletion were
disabled. The required approving-review count was `0`, administrator
enforcement was disabled, and automatic deletion of merged branches was
enabled. The approval and administrator-bypass settings must not be described
as independent-review enforcement.

GitHub Actions currently use maintained major-version tags rather than immutable
commit SHAs. This keeps Dependabot updates readable and avoids manually
maintaining action hashes, but it accepts the upstream risk that a mutable major
tag can move. Treat SHA pinning or an action allowlist as future hardening,
especially if the repository gains additional maintainers or handles more
sensitive release credentials.

The sandbox SARIF workflow uses job-scoped `security-events: write`. Verify
actual ingestion through the Code Scanning analyses API; workflow existence or
a successful generation step alone is not ingestion proof.
