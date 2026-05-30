# CLI reference

## `manifest create`

Create a JSON manifest for a file or directory.

```bash
repro-evidence manifest create PATH -o manifest.json
```

Each file entry includes relative path, byte size, and SHA-256.

## `manifest diff`

Compare two manifests.

```bash
repro-evidence manifest diff before.json after.json -o diff.json
```

The report groups paths into `added`, `removed`, `changed`, and `unchanged`.

## `verify sandbox-run`

Verify that only explicitly allowed paths changed.

```bash
repro-evidence verify sandbox-run before.json after.json \
  --allow-added report.json \
  --allow-changed output.bin
```

Comma-separated allowlists are accepted for added, changed, and removed paths.

## `evidence validate`

Validate a YAML or JSON evidence bundle.

```bash
repro-evidence evidence validate examples/evidence-bundle.yaml
```
