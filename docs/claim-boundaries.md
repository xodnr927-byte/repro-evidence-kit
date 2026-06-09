# Claim boundaries

This document defines what `repro-evidence-kit` claims to prove and what it deliberately does not claim to prove.

Use it as a consistency reference for README text, examples, pull requests, release notes, and security documentation.

## Summary table

| Feature | Reasonable claim | Do not claim |
| --- | --- | --- |
| SHA-256 manifests | Byte identity for listed files | Semantic correctness, safety, authorship, or completeness |
| Manifest diffs | Added, removed, changed, and unchanged paths between two manifests | Whether a change is meaningful, safe, or intended |
| Sandbox verification | Observed file changes matched explicit allow/require predicates | The command was safe, isolated, harmless, or correctly executed |
| Evidence bundles | Review metadata for declared commands, inputs, outputs, and hashes | The command actually ran, the environment was identical, or outputs are correct |
| JSON Schema validation | Evidence metadata has the expected structure | The metadata is truthful or the artifacts are correct |
| JUnit output | CI-readable policy/test report format | A real unit test suite for the generated artifact semantics |
| SARIF output | SARIF-compatible policy-failure report for sandbox verification | Full static analysis, code scanning coverage, or vulnerability proof |
| Local HMAC sidecars | Exact-bundle tamper detection under local-key assumptions | Public signer identity, certificate validation, command execution, or public authenticity |
| Trusted Publishing | Package was published by an authorized workflow | Package correctness, code safety, or artifact semantic validity |

## Manifests

A manifest records file paths, sizes, and SHA-256 digests for files selected by the command.

It is valid to say that a manifest records byte identity for the listed files.

It is not valid to say that a manifest proves:

- the files are correct,
- the files are safe,
- the files are complete,
- the files were produced by a specific command,
- omitted files were irrelevant.

## Manifest diffs

A manifest diff compares two manifests and classifies paths as added, removed, changed, or unchanged.

It is valid to say that the diff separates observed byte-level changes.

It is not valid to say that the diff proves the change was intended, meaningful, harmless, or semantically correct.

## Sandbox verification

Sandbox verification checks observed file changes against explicit allow and require predicates.

It is valid to say that a passing sandbox check means the observed manifest difference matched the configured predicate.

It is not valid to say that a passing sandbox check proves:

- the command was safe,
- the command was sandboxed by this tool,
- the environment was isolated,
- no private data was touched,
- the output content is correct.

## Evidence bundles

Evidence bundles preserve review metadata such as command context, declared inputs, declared outputs, and hashes.

It is valid to say that they make a review surface explicit and portable.

It is not valid to say that an evidence bundle proves the command actually ran. That requires independent rerun evidence, CI evidence, or other external validation.

## JSON Schema validation

Schema validation checks metadata shape and required fields.

It is valid to say that schema validation catches malformed or structurally incomplete evidence metadata.

It is not valid to say that schema validation proves the metadata is truthful.

## JUnit and SARIF outputs

JUnit and SARIF outputs are reporting adapters.

It is valid to say that they make policy failures easier to consume in CI or downstream report tools.

It is not valid to say that they turn sandbox verification into semantic test coverage, full code scanning, or vulnerability analysis.

## Local HMAC sidecars

Signed sidecars are local HMAC sidecars for exact evidence-bundle bytes.

It is valid to say that verification detects whether the bundle bytes match the sidecar under the same local key.

It is not valid to say that sidecars prove:

- public signer identity,
- public trust,
- a certificate chain,
- command execution,
- artifact correctness,
- package correctness.

Do not commit real keys. Use synthetic keys only in examples and CI smoke tests.

## Trusted Publishing

Trusted Publishing helps publish packages without a long-lived PyPI token and ties publishing to an authorized repository workflow.

It is valid to say that a package was published through the configured workflow.

It is not valid to say that Trusted Publishing proves the package content is correct, safe, complete, or semantically valid.

## Preferred wording

Prefer wording like:

- "records byte identity"
- "classifies observed changes"
- "checks the observed output set against an explicit allowlist"
- "preserves review metadata"
- "provides local exact-bundle tamper detection"
- "uses Trusted Publishing for tokenless PyPI release workflow"

Avoid wording like:

- "proves correctness"
- "proves safety"
- "proves command execution"
- "proves authenticity" without a local-key qualifier
- "secure signing" without explaining the local HMAC boundary
- "full provenance" or "supply-chain attestation"
