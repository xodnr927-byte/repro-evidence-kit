# Contributing

Contributions are welcome when they keep `repro-evidence-kit` general-purpose, target-neutral, and reviewable.

This project is a maintainer-focused toolkit for small proof surfaces around generated or artifact-heavy work. It is not a place to publish private samples, proprietary targets, live investigation data, or project-specific reverse-engineering artifacts.

## Accepted contribution types

Good contributions include:

- documentation improvements,
- CLI behavior fixes or narrowly scoped CLI improvements,
- evidence-bundle or signature-sidecar validation improvements,
- JSON Schema corrections or compatibility tests,
- synthetic examples,
- unit tests and regression tests,
- CI/reporting adapter polish,
- packaging metadata or release-documentation polish.

Keep changes small and reviewable. Prefer one focused pull request over a broad mixed change.

## Examples and fixtures

Examples and fixtures must be synthetic or clearly redistributable.

Do not add:

- proprietary binaries,
- copyrighted samples without a clear redistribution basis,
- private datasets,
- forensic case data,
- client or user data,
- credentials, tokens, keys, or secrets,
- target-specific reverse-engineering artifacts,
- generated logs that disclose sensitive paths or private inputs.

When adding a new fixture, document what it is intended to test and why it can be safely redistributed.

## Proof-boundary wording

Documentation, examples, and pull requests must preserve the project's trust boundaries:

- Hash manifests prove byte identity for the listed files; they do not prove semantic correctness.
- Manifest diffs separate observed byte changes; they do not prove the changes are meaningful or safe.
- Sandbox-output checks verify the observed file-change predicate against an allowlist; they do not prove the command was safe.
- Evidence bundles preserve command context and artifact metadata for review; they do not prove the command actually ran unless an external reviewer validates that separately.
- Local HMAC sidecars provide exact-bundle tamper detection only; they do not prove signer identity, public trust, command execution, or artifact semantics.
- Trusted Publishing identifies an authorized release workflow; it does not prove package correctness.

Avoid wording that expands these claims.

## Tests and validation

Before opening a pull request, run the relevant checks for your change.

For most changes:

```bash
python -m unittest discover -s tests
python -m repro_evidence_kit evidence validate examples/evidence-bundle.yaml
```

When schema behavior changes, also run schema-extra tests:

```bash
python -m pip install -e ".[schema]"
python -m unittest discover -s tests
python -m repro_evidence_kit evidence validate examples/evidence-bundle.yaml --schema
```

When examples or CLI examples change, run the smoke script:

```bash
python scripts/smoke_examples.py
```

When packaging metadata, package data, or release files change, build and check distributions:

```bash
python -m pip install build twine
python -m build
python scripts/check_dist.py
twine check dist/*
```

## Maintainer-review requirements

Human maintainer review is required before merging changes that affect:

- release behavior,
- PyPI publishing behavior,
- package metadata,
- security-sensitive validation behavior,
- signature-sidecar behavior,
- evidence-bundle schemas or trust-boundary wording,
- examples that could be confused with private or target-specific data.

Automation may help draft, test, or triage these changes, but it must not merge them without human review.

## Pull request checklist

A good pull request should state:

- what changed,
- why the change is needed,
- which files are intentionally touched,
- which validation commands were run,
- whether the change affects trust boundaries, packaging, or release behavior.

If a check was not run, say so explicitly and explain why.
