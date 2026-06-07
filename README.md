# repro-evidence-kit

[![CI](https://github.com/xodnr927-byte/repro-evidence-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/xodnr927-byte/repro-evidence-kit/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/xodnr927-byte/repro-evidence-kit)](https://github.com/xodnr927-byte/repro-evidence-kit/releases)
[![PyPI](https://img.shields.io/pypi/v/repro-evidence-kit)](https://pypi.org/project/repro-evidence-kit/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/xodnr927-byte/repro-evidence-kit)](LICENSE)

A small command-line toolkit for reproducible artifact verification in binary analysis, security research, and automation workflows.

It creates hash manifests, compares experiment outputs, and validates evidence bundles so results can be reviewed without relying on private source data.

## Why this matters

Generated artifacts are hard to review when the only proof is a large log, a private input tree, or a verbal claim that "nothing important changed." `repro-evidence-kit` keeps the review surface small: it records byte hashes, separates expected output changes from unexpected ones, and stores enough command context for another maintainer to rerun or challenge the evidence.

The project is intentionally target-neutral. It should help maintainers in CI, security research, binary-analysis, data-processing, and automation workflows without requiring them to publish proprietary samples or project-specific case files.

## Use cases

- Review what changed during artifact-heavy CI or release automation.
- Verify that a sandboxed experiment only produced explicitly allowed outputs.
- Attach compact, hash-backed evidence bundles to pull requests or research notes.
- Keep generated reports reviewable without publishing private input data.

## What this proves

- File manifests prove byte identity for the files they list.
- Manifest diffs separate expected artifact changes from unexpected ones.
- Sandbox verification proves the observed output set stayed inside an explicit allowlist.
- Evidence bundles preserve command context, inputs, outputs, and hashes for review.
- Signed sidecars add local tamper detection for exact bundle bytes.

## What this does not prove

- Hashes do not prove that generated outputs are semantically correct.
- A passing sandbox check does not prove that a command was safe.
- Signed sidecars do not prove signer identity, key trust, command execution, or artifact semantics.
- Private or proprietary inputs still require reviewer judgment outside this repository.

## Features

- Create deterministic SHA-256 manifests for files or filtered directory trees.
- Diff two manifests to identify added, removed, changed, and unchanged artifacts.
- Verify sandbox/experiment outputs against explicit allowlists, with optional JUnit XML for CI report consumers.
- Validate simple YAML or JSON evidence bundles, with optional JSON Schema checks.
- Sign and verify evidence bundle sidecars with a local-key tamper-detection prototype.
- Includes only synthetic public examples.

## Install

Install the latest release from PyPI:

```bash
pip install repro-evidence-kit
```

For local development:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Quick start

```bash
repro-evidence manifest create examples/dummy-binary -o before.json
repro-evidence manifest diff before.json before.json
repro-evidence evidence validate examples/evidence-bundle.yaml
```

For larger artifact trees, filter manifests with explicit include/exclude patterns:

```bash
repro-evidence manifest create artifacts --include reports --exclude "*.tmp" -o manifest.json
```

For stricter evidence-bundle checks, install the optional schema extra and validate against the checked-in JSON Schema:

```bash
pip install "repro-evidence-kit[schema]"
repro-evidence evidence validate examples/evidence-bundle.yaml --schema
```


Signed bundle sidecars are optional. For a local tamper-detection prototype, create or provide local trust material and keep it out of git:

```bash
printf 'synthetic local test key only\n' > local-test.key
repro-evidence evidence sign examples/evidence-bundle.yaml --key local-test.key -o evidence-bundle.yaml.sig.json
repro-evidence evidence verify-signature examples/evidence-bundle.yaml --signature evidence-bundle.yaml.sig.json --key local-test.key
```

Sandbox verification compares a baseline manifest with an after-run manifest:

```bash
repro-evidence verify sandbox-run before.json after.json --allow-added report.json
```

The command exits `0` when all changes are allowed and `1` when unexpected changes are present.

## Documentation

- [CLI reference](docs/cli.md)
- [CLI exit codes](docs/cli-exit-codes.md)
- [Tutorial](docs/tutorial.md)
- [Evidence bundle format](docs/evidence-bundle-format.md)
- [Use cases](docs/use-cases.md)
- [Signed evidence bundles design note](docs/signed-bundles.md)
- [Maintainer workflow](docs/maintainer-workflow.md)
- [Release checklist](docs/release-checklist.md)
- [PyPI publishing](docs/publishing.md)
- [GitHub Actions cookbook](docs/github-actions.md) — CI recipes for validation, manifests, sandbox checks, and schema-backed filtered workflows.
- [Design principles](docs/design-principles.md)
- [Roadmap](ROADMAP.md)

## Data policy

This repository is for generic reproducibility tooling. Do not add proprietary binaries, private datasets, copyrighted samples, live credentials, forensic case data, or project-specific reverse-engineering targets. Public examples must be synthetic or clearly redistributable.

## Status

`0.4.x` is an early maintainer-tooling release series. The CLI and schema stay intentionally small, conservative, and synthetic-example-only.
