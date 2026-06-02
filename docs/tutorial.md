# Tutorial: verify a small artifact-producing run

This walkthrough uses only synthetic files from the repository.

## 1. Create a baseline manifest

```bash
repro-evidence manifest create examples/sandbox-run -o before.json
```

The manifest records relative paths, file sizes, and SHA-256 hashes.

For a larger tree, narrow the manifest with include/exclude filters:

```bash
repro-evidence manifest create examples/sandbox-run \
  --include "*.txt" \
  --exclude "*.tmp" \
  -o before.json
```

Includes are applied first, excludes second, and the active filter patterns are written into manifest metadata for reproducibility.

## 2. Run an experiment

For a real workflow, this would be a build, parser, analysis script, or sandboxed automation step. For a minimal local example:

```bash
printf 'reviewable report\n' > examples/sandbox-run/report.txt
repro-evidence manifest create examples/sandbox-run -o after.json
```

## 3. Review the diff

```bash
repro-evidence manifest diff before.json after.json
```

The diff separates added, removed, changed, and unchanged paths.

For a report that can be pasted into an issue or pull request, write Markdown:

```bash
repro-evidence manifest diff before.json after.json --format markdown -o diff.md
```

## 4. Verify allowed changes

If `report.txt` is the only expected new artifact:

```bash
repro-evidence verify sandbox-run before.json after.json --allow-added report.txt
```

The verifier exits with status `0` only when every change is explicitly allowed.

## 5. Attach an evidence bundle

Use `examples/evidence-bundle.yaml` as a small reviewable record of inputs, commands, and outputs:

```bash
repro-evidence evidence validate examples/evidence-bundle.yaml
```

Evidence bundles prove byte identity for listed artifacts. They do not prove semantic correctness by themselves.
