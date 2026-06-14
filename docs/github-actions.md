# GitHub Actions cookbook

These snippets use synthetic paths and generic artifact names. Replace the paths with outputs from your own repository, but do not commit private source data or proprietary samples.

## Choose a workflow

| Need | Use | Output |
| --- | --- | --- |
| Validate evidence metadata | `repro-evidence evidence validate` | exit code, optional text/JUnit |
| Validate evidence metadata against JSON Schema | `repro-evidence evidence validate --schema` | stricter validation result |
| Create an artifact manifest | `repro-evidence manifest create` | JSON manifest |
| Diff generated outputs | `repro-evidence manifest diff` | added/removed/changed/unchanged paths |
| Gate sandbox outputs | `repro-evidence verify sandbox-run` | policy exit code and optional report |
| Publish CI-readable sandbox failures | `verify sandbox-run --format junit` | JUnit XML artifact |
| Publish SARIF-compatible sandbox failures | `verify sandbox-run --format sarif` | SARIF JSON artifact |
| Check local tamper detection | `evidence sign` and `evidence verify-signature` | local HMAC sidecar result |
| Smoke-test synthetic examples | `python scripts/smoke_examples.py` | example command pass/fail |

Use the smallest recipe that matches the review question. These workflows provide compact review artifacts; they do not prove command safety, semantic correctness, public signer identity, or full supply-chain provenance.

## Validate evidence bundles

```yaml
name: Evidence

on:
  pull_request:

jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
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
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: python -m repro_evidence_kit manifest create examples/dummy-binary -o manifest.json
      - uses: actions/upload-artifact@v7
        with:
          name: manifest
          path: manifest.json
```

## Combine schema validation with filtered manifests

Use this recipe when a workflow produces a large artifact tree but reviewers only need a compact manifest for stable outputs plus schema-backed evidence metadata. The example creates synthetic files during the job and keeps the manifest target-neutral.

```yaml
name: Filtered evidence workflow

on:
  pull_request:

jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - run: python -m pip install -e ".[schema]"
      - name: Create synthetic artifact tree
        run: |
          mkdir -p artifacts/reports artifacts/tmp
          printf '%s\n' '{"ok": true}' > artifacts/reports/result.json
          printf '%s\n' 'transient' > artifacts/tmp/cache.tmp
      - name: Create filtered manifest
        run: |
          python -m repro_evidence_kit manifest create artifacts \
            --include reports \
            --exclude "*.tmp" \
            -o filtered-manifest.json
      - name: Validate evidence bundle with schema
        run: |
          python -m repro_evidence_kit evidence validate \
            examples/evidence-bundle.yaml \
            --schema
      - uses: actions/upload-artifact@v7
        with:
          name: filtered-evidence
          path: filtered-manifest.json
```

The schema extra installs `jsonschema` for `--schema`. The filtered manifest records only paths selected by the include/exclude rules, so large or transient directories can stay out of the review artifact without weakening the evidence-bundle validation step.

## Gate sandbox output changes

```yaml
name: Sandbox verification

on:
  pull_request:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
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

## Upload sandbox verification as JUnit XML

Use this when your CI dashboard or a test-report action can display JUnit XML. GitHub Actions does not render JUnit XML by itself, so this recipe uploads the report as an artifact and leaves rendering to your chosen report consumer.

```yaml
name: Sandbox verification report

on:
  pull_request:

jobs:
  verify-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: mkdir -p sandbox && printf 'input\n' > sandbox/input.txt
      - run: python -m repro_evidence_kit manifest create sandbox -o before.json
      - run: printf '{"ok": true}\n' > sandbox/report.json
      - run: python -m repro_evidence_kit manifest create sandbox -o after.json
      - name: Write JUnit report
        run: |
          python -m repro_evidence_kit verify sandbox-run before.json after.json \
            --allow-added report.json \
            --require-added report.json \
            --format junit \
            -o sandbox-verification.xml
      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: sandbox-verification-junit
          path: sandbox-verification.xml
```

The JUnit output keeps the same exit-code behavior as JSON: unexpected changes still return `1` and fail the job. The XML report contains one testcase and one failure when the sandbox predicate fails.

## Verify a signed evidence bundle sidecar

This recipe uses a synthetic key created during the job. It is for local tamper-detection plumbing only, not public signer identity.

```yaml
name: Signed evidence smoke

on:
  pull_request:

jobs:
  signed-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - run: python -m pip install -e ".[schema]"
      - run: printf 'synthetic local test key only\n' > local-test.key
      - run: |
          python -m repro_evidence_kit evidence sign examples/evidence-bundle.yaml \
            --key local-test.key \
            --key-hint local-synthetic \
            -o evidence-bundle.yaml.sig.json
      - run: |
          python -m repro_evidence_kit evidence verify-signature examples/evidence-bundle.yaml \
            --signature evidence-bundle.yaml.sig.json \
            --key local-test.key \
            --schema \
            --format text
```

## Run synthetic examples as a smoke test

```yaml
name: Example smoke

on:
  pull_request:

jobs:
  examples:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: python scripts/smoke_examples.py
```

## Upload sandbox verification as SARIF

Use this when a downstream code-scanning integration accepts SARIF. The SARIF report is a compact policy-failure adapter for sandbox output verification.

The repository's optional `.github/workflows/sandbox-sarif.yml` workflow
generates a synthetic passing report and uploads it to GitHub Code Scanning on
pushes to `main`. It grants `security-events: write` only to the upload job and
does not run on pull requests, where untrusted forks do not receive write
permissions.

This integration publishes sandbox allowlist/required-output findings. It is
not vulnerability analysis, source-code scanning, or evidence that an artifact
is safe.

```yaml
name: Sandbox SARIF

on:
  pull_request:

jobs:
  sandbox-sarif:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: mkdir -p sandbox && printf 'input\n' > sandbox/input.txt
      - run: python -m repro_evidence_kit manifest create sandbox -o before.json
      - run: printf '{"ok": true}\n' > sandbox/report.json
      - run: python -m repro_evidence_kit manifest create sandbox -o after.json
      - run: |
          python -m repro_evidence_kit verify sandbox-run before.json after.json \
            --allow-added report.json \
            --require-added report.json \
            --format sarif \
            -o sandbox-verification.sarif
      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: sandbox-verification-sarif
          path: sandbox-verification.sarif
```

## Evidence validation as JUnit XML

```yaml
- run: |
    python -m repro_evidence_kit evidence validate examples/evidence-bundle.yaml \
      --format junit \
      -o evidence-validation.xml
- uses: actions/upload-artifact@v7
  if: always()
  with:
    name: evidence-validation-junit
    path: evidence-validation.xml
```
