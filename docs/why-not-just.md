# Why not just ...?

`repro-evidence-kit` is intentionally small. It does not try to replace Git, CI artifacts, signed commits, SBOMs, SLSA provenance, or a full supply-chain attestation system.

Its purpose is narrower: provide a low-friction review surface for generated or artifact-heavy work.

## Why not just `sha256sum`?

`sha256sum` is useful for one file or a simple list of files, but it does not provide a review workflow by itself.

`repro-evidence-kit` adds:

- deterministic directory manifests,
- include/exclude filtering,
- added/removed/changed/unchanged classification,
- evidence-bundle metadata,
- sandbox output predicates,
- optional CI report formats.

A hash still proves only byte identity. It does not prove semantic correctness.

## Why not just `git diff`?

`git diff` is strong for tracked source files, but generated artifacts are often untracked, too large, produced in CI, or not suitable for direct repository commits.

`repro-evidence-kit` is useful when reviewers need compact metadata about generated outputs without storing private inputs, large output directories, or noisy logs in the repository.

It does not replace source review. It complements source review when generated artifacts need a smaller evidence surface.

## Why not just JSON Schema?

JSON Schema can validate the shape of evidence metadata, but it cannot decide whether the generated output set changed in expected ways.

`repro-evidence-kit` uses schema validation as one layer. It also records file hashes, compares manifests, and checks sandbox output changes against explicit allowlists.

Schema validity does not prove artifact correctness or command execution.

## Why not just upload GitHub Actions artifacts?

Uploading artifacts stores files from a workflow, but it does not automatically explain which paths were expected, which paths changed, or whether an unexpected output should fail the job.

`repro-evidence-kit` can generate compact manifests, JUnit XML, or SARIF-compatible reports that summarize the review question.

GitHub artifact upload is a transport mechanism. It is not a review policy by itself.

## Why not just signed commits or signed tags?

Signed commits and tags can help verify who pushed or released repository history, but they do not prove that a generated evidence bundle remained unchanged after local review.

Local HMAC sidecars in this project are narrower: they detect exact-byte changes to an evidence bundle when the same local key is available.

They do not provide public signer identity, a certificate chain, command-execution proof, or artifact semantic proof.

## Why not full SLSA or supply-chain provenance?

Full provenance frameworks are valuable for mature release pipelines, but they can be heavy for small maintainer workflows, synthetic examples, and early-stage generated-artifact review.

`repro-evidence-kit` deliberately stays smaller:

- local CLI first,
- target-neutral examples,
- explicit trust boundaries,
- compact review artifacts,
- no claim of full supply-chain attestation.

A project that needs full provenance can still use this toolkit for narrow artifact review, but should not treat it as a replacement for a complete provenance system.

## Design boundary

This project should remain honest about what it proves:

- manifests prove byte identity for listed files,
- diffs classify observed manifest changes,
- sandbox checks evaluate observed file changes against explicit predicates,
- evidence bundles preserve review metadata,
- local HMAC sidecars detect exact-bundle tampering under local-key assumptions.

It should not claim to prove semantic correctness, command safety, public signer identity, package correctness, or full reproducibility without independent rerun evidence.
