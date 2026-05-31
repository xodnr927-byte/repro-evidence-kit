# CLI reference

## Exit codes

All commands use the same top-level exit-code contract:

| Code | Meaning | Examples |
| --- | --- | --- |
| `0` | The command completed and the checked predicate passed. | Manifest written, manifests diffed, evidence bundle valid, sandbox output contains only allowed changes. |
| `1` | The command completed and found an expected validation or verification failure. | Evidence bundle is structurally invalid, sandbox output contains unexpected added/changed/removed paths. |
| `2` | The command could not complete because of an input, parsing, filesystem, or runtime error. | Missing JSON file, malformed manifest JSON, unreadable evidence file. |

Use `1` as a CI policy failure and `2` as an infrastructure or invocation failure.

## `manifest create`

Create a JSON manifest for a file or directory.

```bash
repro-evidence manifest create PATH -o manifest.json
```

Each file entry includes relative path, byte size, and SHA-256.

Manifest paths are serialized with `/` separators so manifests stay reviewable across platforms.

## `manifest diff`

Compare two manifests.

```bash
repro-evidence manifest diff before.json after.json -o diff.json
```

The report groups paths into `added`, `removed`, `changed`, and `unchanged`.

When comparing manifests, Windows-style `\` separators are treated as the same logical path separators as `/`.

## `verify sandbox-run`

Verify that only explicitly allowed paths changed.

```bash
repro-evidence verify sandbox-run before.json after.json \
  --allow-added report.json \
  --allow-changed output.bin
```

Comma-separated allowlists are accepted for added, changed, and removed paths.

Allowlist paths use the same normalization as manifest diffs, so `reports\summary.json` and `reports/summary.json` match the same logical artifact.

## `evidence validate`

Validate a YAML or JSON evidence bundle.

```bash
repro-evidence evidence validate examples/evidence-bundle.yaml
```

Exit code `1` means the file was read successfully but the bundle failed validation. Exit code `2` means the file could not be read or parsed.
