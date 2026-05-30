# repro-evidence-kit

A small command-line toolkit for reproducible artifact verification in binary analysis, security research, and automation workflows.

It creates hash manifests, compares experiment outputs, and validates evidence bundles so results can be reviewed without relying on private source data.

## Features

- Create deterministic SHA-256 manifests for files or directories.
- Diff two manifests to identify added, removed, changed, and unchanged artifacts.
- Verify sandbox/experiment outputs against explicit allowlists.
- Validate simple YAML or JSON evidence bundles.
- Includes only synthetic public examples.

## Install

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

Sandbox verification compares a baseline manifest with an after-run manifest:

```bash
repro-evidence verify sandbox-run before.json after.json --allow-added report.json
```

The command exits `0` when all changes are allowed and `1` when unexpected changes are present.

## Evidence bundle format

See [`docs/evidence-bundle-format.md`](docs/evidence-bundle-format.md) and [`schemas/evidence-bundle.schema.json`](schemas/evidence-bundle.schema.json).

## Data policy

This repository is for generic reproducibility tooling. Do not add proprietary binaries, private datasets, copyrighted samples, live credentials, forensic case data, or project-specific reverse-engineering targets. Public examples must be synthetic or clearly redistributable.

## Status

`0.1.0` is an initial release candidate. The CLI and schema are intentionally small and conservative.
