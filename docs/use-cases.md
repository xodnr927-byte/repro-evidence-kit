# Use cases

`repro-evidence-kit` is for small, reviewable proof surfaces around generated or artifact-heavy work. All examples should stay synthetic or clearly redistributable.

The common pattern is:

1. create a compact artifact description,
2. attach it to a pull request, CI run, release note, or maintainer handoff,
3. let reviewers check what changed without publishing private inputs or noisy logs.

## Generated artifact review

### Problem

Generated outputs are difficult to review when the only evidence is a large log, a private input directory, or a claim that no important files changed.

### When to use this

Use this when a tool, script, model, build step, or automation job emits files that reviewers need to inspect indirectly.

### Minimal workflow

```bash
repro-evidence manifest create artifacts -o manifest.json
repro-evidence manifest diff before.json manifest.json
repro-evidence evidence validate examples/evidence-bundle.yaml
```

### What reviewers can verify

Reviewers can inspect file paths, SHA-256 digests, added/removed/changed status, and evidence-bundle metadata. They can also decide whether the produced files match the expected review surface.

### What this does not prove

This does not prove that generated artifacts are semantically correct, useful, safe, or complete. It only gives reviewers a compact, hash-backed surface to challenge.

### Reviewer warnings

Do not include private source data, proprietary samples, credentials, forensic case files, or large raw logs in the evidence bundle.

## Artifact-heavy CI or release automation

### Problem

CI and release jobs often produce many files, but reviewers usually need to know whether the stable outputs changed in expected ways.

### When to use this

Use filtered manifests when the relevant outputs are a subset of a larger working directory. Use sandbox verification when a job should produce only an explicit set of output paths.

### Minimal workflow

```bash
repro-evidence manifest create artifacts --include reports --exclude "*.tmp" -o filtered-manifest.json
repro-evidence verify sandbox-run before.json after.json --allow-added report.json
```

### What reviewers can verify

Reviewers can check that the recorded artifact tree includes only the selected outputs and that unexpected sandbox changes fail the job.

### What this does not prove

This does not prove that the CI command was safe. A passing sandbox check means the observed file-change predicate matched the allowlist.

### Reviewer warnings

Avoid broad include patterns that accidentally capture private working directories or transient cache files.

## Security or binary-analysis research outputs

### Problem

Security and binary-analysis work can produce reports, traces, generated metadata, and intermediate files that should be reviewable without publishing private or proprietary inputs.

### When to use this

Use this when you can publish synthetic or redistributable outputs, but not the original target material or private runtime logs.

### Minimal workflow

```bash
repro-evidence manifest create reports -o reports-manifest.json
repro-evidence evidence validate evidence-bundle.yaml
```

### What reviewers can verify

Reviewers can inspect which report files exist, which hashes are claimed, which command context was recorded, and whether the evidence-bundle metadata is structurally valid.

### What this does not prove

This does not prove vulnerability impact, reverse-engineering correctness, exploitability, authorship, command execution, or the semantic truth of a report.

### Reviewer warnings

Keep examples target-neutral. Do not add proprietary binaries, private traces, exploit material, credentials, or target-specific reverse-engineering artifacts.

## Signed evidence bundle review

### Problem

Maintainers may want to detect whether a reviewed evidence bundle has changed after local review.

### When to use this

Use signed sidecars for local exact-byte tamper detection when the same maintainers control the local key material.

### Minimal workflow

```bash
printf 'synthetic local test key only\n' > local-test.key
repro-evidence evidence sign examples/evidence-bundle.yaml --key local-test.key -o evidence-bundle.yaml.sig.json
repro-evidence evidence verify-signature examples/evidence-bundle.yaml --signature evidence-bundle.yaml.sig.json --key local-test.key
```

### What reviewers can verify

Reviewers can verify that the evidence-bundle bytes match a local HMAC sidecar created with the same local key.

### What this does not prove

This does not prove signer identity, public trust, certificate-chain validity, command execution, artifact semantics, or package correctness.

### Reviewer warnings

Do not commit real keys. Do not treat local sidecars as public authenticity guarantees.

## Documentation or report generation

### Problem

Documentation and report-generation jobs can create noisy diffs or many intermediate files, even when reviewers only care about stable generated outputs.

### When to use this

Use manifests to record stable generated reports or documentation outputs. Use evidence bundles to describe the generation command and inputs at a high level.

### Minimal workflow

```bash
repro-evidence manifest create generated-docs -o docs-manifest.json
repro-evidence manifest diff previous-docs-manifest.json docs-manifest.json
```

### What reviewers can verify

Reviewers can verify which generated files changed and whether the output set stayed within the expected documentation or report directory.

### What this does not prove

This does not prove that the prose, chart, or report content is accurate.

### Reviewer warnings

Avoid storing private source documents or proprietary generated reports unless they are intentionally redistributable.

## Maintainer handoff and reproducibility notes

### Problem

A reviewer may need to understand what was generated, from which declared inputs, and which outputs should be checked, without rerunning a private or expensive process immediately.

### When to use this

Use evidence bundles with manifests when handing off generated artifacts between maintainers or across CI jobs.

### Minimal workflow

```bash
repro-evidence manifest create outputs -o outputs-manifest.json
repro-evidence evidence validate handoff-evidence.yaml
```

### What reviewers can verify

Reviewers can inspect the declared command context, inputs, outputs, hashes, and evidence metadata.

### What this does not prove

This does not prove that the command was actually executed, that the environment was identical, or that a result is reproducible without independent rerun evidence.

### Reviewer warnings

Keep handoff metadata concise. Do not use evidence bundles as a dumping ground for private logs or internal-only notes.
