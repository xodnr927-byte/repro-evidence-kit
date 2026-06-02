# repro-evidence-kit

[![CI](https://github.com/xodnr927-byte/repro-evidence-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/xodnr927-byte/repro-evidence-kit/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/xodnr927-byte/repro-evidence-kit)](https://github.com/xodnr927-byte/repro-evidence-kit/releases)
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

## Features

- Create deterministic SHA-256 manifests for files or filtered directory trees.
- Diff two manifests to identify added, removed, changed, and unchanged artifacts.
- Verify sandbox/experiment outputs against explicit allowlists.
- Validate simple YAML or JSON evidence bundles.
- Includes only synthetic public examples.

## Install

Until a package index release is published, install from the repository:

```bash
pip install "git+https://github.com/xodnr927-byte/repro-evidence-kit.git@v0.1.1"
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

Sandbox verification compares a baseline manifest with an after-run manifest:

```bash
repro-evidence verify sandbox-run before.json after.json --allow-added report.json
```

The command exits `0` when all changes are allowed and `1` when unexpected changes are present.

## Documentation

- [CLI reference](docs/cli.md)
- [Tutorial](docs/tutorial.md)
- [Evidence bundle format](docs/evidence-bundle-format.md)
- [Maintainer workflow](docs/maintainer-workflow.md)
- [GitHub Actions cookbook](docs/github-actions.md)
- [Design principles](docs/design-principles.md)
- [Roadmap](ROADMAP.md)

## Data policy

This repository is for generic reproducibility tooling. Do not add proprietary binaries, private datasets, copyrighted samples, live credentials, forensic case data, or project-specific reverse-engineering targets. Public examples must be synthetic or clearly redistributable.

## Status

`0.1.x` is an early release series. The CLI and schema are intentionally small and conservative.
