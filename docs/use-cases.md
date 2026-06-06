# Use cases

`repro-evidence-kit` is for small, reviewable proof surfaces around generated or artifact-heavy work. All examples should stay synthetic or redistributable.

## AI-generated artifacts

Use manifests and evidence bundles to record which files an automation run produced, which command was intended, and which hashes reviewers can compare. This helps reviewers challenge outputs without needing private prompts, source data, or logs in the repository.

## Binary-analysis or security research outputs

Use sandbox verification to distinguish expected reports from unexpected files created by a tool run. This does not prove semantic correctness; it proves the observed file-change predicate against the explicit allowlist.

## Release and documentation automation

Use filtered manifests for generated docs, reports, or release assets. Upload the manifest or a JUnit sandbox verification report to CI so reviewers can inspect compact artifacts instead of noisy working directories.

## Signed evidence bundle review

Use signed sidecars when maintainers need local tamper detection for exact evidence-bundle bytes. The current `hmac-sha256` prototype is a local-key workflow only; it is not signer identity, keyserver, certificate-chain, command-execution, or artifact-semantics proof.
