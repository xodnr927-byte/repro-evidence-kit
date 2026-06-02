# Signed evidence bundles design note

Signed bundle support should let a maintainer check that an evidence bundle record has not changed since it was signed. It must not imply that the recorded command was run correctly, that artifacts are semantically correct, or that a private input can be trusted without review.

## Current status

This is a design note, not an implemented signing backend. Unsigned evidence bundles remain fully supported.

## Goals

- Add an optional workflow for signing an evidence bundle after it has been authored and validated.
- Let a reviewer verify the signed bundle bytes against a public key or trusted local key reference.
- Keep the workflow target-neutral and usable with synthetic examples.
- Keep failure modes explicit: invalid structure, invalid signature, missing key material, and unsupported signing metadata should be distinguishable.

## Non-goals

- No live private keys, real maintainer keys, or committed secrets.
- No external keyserver requirement.
- No claim that signatures prove artifact semantics or command correctness.
- No requirement that all evidence bundles be signed.
- No target-specific policy, private path, proprietary sample, or reverse-engineering fixture.

## What signing proves

A valid signature can prove that the exact canonical bundle payload was signed by the holder of the matching private key.

It can help answer:

- Did this evidence bundle change after the signer approved it?
- Does this bundle match the public key or local trust material used by the reviewer?
- Is the bundle metadata stable enough to attach to a pull request, release note, or audit record?

## What signing does not prove

A valid signature does not prove:

- the command actually ran;
- the command was safe;
- the outputs are semantically correct;
- the hashes correspond to private data the reviewer cannot inspect;
- the signer identity is trustworthy without an external trust decision;
- the signing key has not been compromised.

## Proposed bundle shape

Unsigned bundles should keep the existing format. A signed workflow can write a sidecar first, avoiding a breaking change to the bundle schema:

```text
evidence-bundle.yaml
evidence-bundle.yaml.sig.json
```

A sidecar keeps signatures optional and avoids mutating the payload after signing.

Candidate sidecar fields:

```json
{
  "signature_version": "1.0",
  "payload_path": "evidence-bundle.yaml",
  "payload_sha256": "<sha256 of canonical payload bytes>",
  "algorithm": "<algorithm identifier>",
  "key_hint": "<local or public key identifier>",
  "signature": "<encoded signature bytes>"
}
```

## Canonical payload rule

The first implementation should sign exact file bytes or a clearly documented canonical serialization, not an implicit Python object. Exact file bytes are simpler and reduce surprise, but they make whitespace and key ordering part of the signed payload. If canonical serialization is chosen later, it must be documented and covered by round-trip tests before release.

## CLI sketch

Potential commands:

```bash
repro-evidence evidence sign evidence-bundle.yaml \
  --key local-test-key.pem \
  -o evidence-bundle.yaml.sig.json

repro-evidence evidence verify-signature evidence-bundle.yaml \
  --signature evidence-bundle.yaml.sig.json \
  --key local-test-public-key.pem
```

The command names are provisional. The implementation should keep `evidence validate` unchanged and allow unsigned bundles to keep passing validation.

## Test fixture policy

If tests need key material, use local synthetic test keys only. Test keys must be labeled as fixtures and must not be suitable for real trust decisions.

## Recommended implementation path

1. Add parser and data model support for signature sidecars without changing unsigned bundle validation.
2. Add synthetic fixture tests for malformed sidecars and payload hash mismatches.
3. Add one signing backend with local test keys only.
4. Document reviewer setup and limitations before adding release notes.
5. Consider richer trust policies only after the sidecar contract is stable.
