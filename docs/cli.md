# CLI reference

## Exit codes

See [CLI exit codes](cli-exit-codes.md) for the shared `0`/`1`/`2` contract.

## `manifest create`

Create a JSON manifest for a file or directory.

```bash
repro-evidence manifest create PATH -o manifest.json
```

Each file entry includes relative path, byte size, and SHA-256.

Manifest paths are serialized with `/` separators so manifests stay reviewable across platforms.

Use `--include` and `--exclude` to filter large artifact trees by manifest-relative path:

```bash
repro-evidence manifest create artifacts \
  --include reports \
  --include "*.json" \
  --exclude "*.tmp" \
  -o manifest.json
```

Filters are deterministic and use POSIX-style manifest-relative globs or subtree paths. Includes run first; when at least one include is supplied, only matching files remain. Excludes run after includes and remove matching files. Repeated flags and comma-separated values are accepted. When filters are used, the manifest records normalized include/exclude patterns in a `filters` metadata object.

## `manifest diff`

Compare two manifests.

```bash
repro-evidence manifest diff before.json after.json -o diff.json
```

The report groups paths into `added`, `removed`, `changed`, and `unchanged`.

When comparing manifests, Windows-style `\` separators are treated as the same logical path separators as `/`.

Use `--format markdown` when you want a review-friendly Markdown report instead of JSON:

```bash
repro-evidence manifest diff before.json after.json --format markdown -o diff.md
```

## `verify sandbox-run`

Verify that only explicitly allowed paths changed.

```bash
repro-evidence verify sandbox-run before.json after.json \
  --allow-added report.json \
  --allow-changed output.bin
```

Comma-separated allowlists are accepted for added, changed, and removed paths. Use `--require-added`, `--require-changed`, or `--require-removed` when an expected output must appear; a missing required change returns exit code `1`.

Allowlist paths use the same normalization as manifest diffs, so `reports\summary.json` and `reports/summary.json` match the same logical artifact.

Use `--format junit` when a CI system or test-report action expects JUnit XML, or `--format sarif` when a code-scanning adapter expects SARIF results:

```bash
repro-evidence verify sandbox-run before.json after.json \
  --allow-added report.json \
  --format junit \
  -o sandbox-verification.xml
```

The JUnit report has one testcase named `sandbox-run`. Unexpected added, changed, removed, or missing required paths are rendered as one failure. SARIF output uses `unexpected-sandbox-change` and `missing-required-sandbox-change` rule IDs. These are CI reporting adapters for the sandbox verification predicate; they are not full test suites and do not change the JSON output contract.

## `evidence validate`

Validate a YAML or JSON evidence bundle.

```bash
repro-evidence evidence validate examples/evidence-bundle.yaml
```

The default validator is lightweight and has no dependency beyond the base package. It checks required top-level fields, artifact `path`/`sha256` presence, and command shape. Use it for fast local checks and low-friction CI.

For stricter JSON Schema validation, install the optional schema extra and pass `--schema`:

```bash
pip install "repro-evidence-kit[schema]"
repro-evidence evidence validate examples/evidence-bundle.yaml --schema
```

Schema-backed validation uses `schemas/evidence-bundle.schema.json` and additionally enforces constraints such as SHA-256 hex format and numeric size bounds. Use `--schema-path custom.schema.json` with `--schema` to test a local schema variant.

Use `--format junit` to write a one-testcase XML report while preserving validation exit-code behavior. Exit code `1` means the file was read successfully but the bundle failed validation. Exit code `2` means the file could not be read, parsed, or schema validation was requested without the optional dependency.


## `evidence sign`

Sign the exact evidence bundle file bytes with a local HMAC key and write a sidecar JSON file.

```bash
repro-evidence evidence sign examples/evidence-bundle.yaml \
  --key local-test.key \
  --key-hint local-test \
  -o examples/evidence-bundle.yaml.sig.json
```

The key file is local trust material. Do not commit live secrets or real maintainer private keys. The prototype algorithm is `hmac-sha256`, intended for local tamper detection and synthetic examples. Use `--dry-run` to print the sidecar that would be written without creating an output file.

## `evidence verify-signature`

Verify that a sidecar signature still matches the exact evidence bundle bytes and local key.

```bash
repro-evidence evidence verify-signature examples/evidence-bundle.yaml \
  --signature examples/evidence-bundle.yaml.sig.json \
  --key local-test.key
```

Use `--format text` for maintainer-friendly CI logs, or keep the default JSON for machine-readable output. JSON results include `errors` plus structured `error_details` with stable categories such as `payload_hash_mismatch`, `signature_mismatch`, `unsupported_signature_version`, `unsupported_algorithm`, `missing_signature`, and parse/read failures as exit code `2`.

Use `--schema` to validate the sidecar shape against `schemas/signature-sidecar.schema.json` when the optional `jsonschema` dependency is installed.

Exit code `0` means the sidecar signature matches. Exit code `1` means the sidecar was read but the payload hash, signature, version, algorithm, or optional schema check failed. Exit code `2` means the command could not read or parse an input. A valid signature does not prove command execution, artifact semantics, or signer identity beyond the reviewer's trust in the local key.
