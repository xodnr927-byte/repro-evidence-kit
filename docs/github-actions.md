# GitHub Actions cookbook

These snippets use synthetic paths and generic artifact names. Replace the paths with outputs from your own repository, but do not commit private source data or proprietary samples.

## Validate evidence bundles

```yaml
name: Evidence

on:
  pull_request:

jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: python -m repro_evidence_kit evidence validate examples/evidence-bundle.yaml
```

`evidence validate` exits `0` when the bundle is valid, `1` when the bundle is readable but invalid, and `2` when the command cannot read or parse the input.

## Create and upload a manifest

```yaml
name: Artifact manifest

on:
  pull_request:

jobs:
  manifest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: python -m repro_evidence_kit manifest create examples/dummy-binary -o manifest.json
      - uses: actions/upload-artifact@v4
        with:
          name: manifest
          path: manifest.json
```

## Gate sandbox output changes

```yaml
name: Sandbox verification

on:
  pull_request:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: mkdir -p sandbox && printf 'input\n' > sandbox/input.txt
      - run: python -m repro_evidence_kit manifest create sandbox -o before.json
      - run: printf '{"ok": true}\n' > sandbox/report.json
      - run: python -m repro_evidence_kit manifest create sandbox -o after.json
      - run: python -m repro_evidence_kit verify sandbox-run before.json after.json --allow-added report.json
```

Unexpected added, changed, or removed paths produce exit code `1`, which fails the job as a policy failure.
