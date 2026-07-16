# Signer trust, rotation, and revocation policy

This document is the design boundary for issue
[#53](https://github.com/xodnr927-byte/repro-evidence-kit/issues/53) and its
implementation slices. Issue [#62](https://github.com/xodnr927-byte/repro-evidence-kit/issues/62)
adds the local policy schema/parser only; it does not add a new verification
mode or change the current `signature_version: "1.0"` sidecar format.

## Decision summary

- The caller, not sidecar metadata, selects the expected key identity.
- `key_hint` remains advisory and must never authorize a signer or select a key.
- Policy files contain non-secret key references, never HMAC key bytes.
- Key states are `active`, `verify_only`, and `revoked`.
- Revocation fails closed for every sidecar checked under that policy.
- Rotation can preserve verification with a `verify_only` key, but a version 1
  sidecar cannot prove when it was created.
- The existing `--key` workflow remains a local tamper-detection mode and does
  not become an identity claim.

## Threat model

### Trusted inputs

- The policy file selected by the caller.
- The expected `key_id` selected by the caller or trusted CI configuration.
- Key material returned by a local resolver for the policy's non-secret
  `key_ref`.
- The verifier executable and its local runtime environment.
- The current time source when evaluating policy activation boundaries.

### Attacker-controlled inputs

- The evidence bundle and every byte in it.
- The complete signature sidecar, including `payload_path`, `key_hint`,
  `payload_sha256`, `algorithm`, and `signature_version`.
- Repository content, pull-request content, uploaded artifacts, and command-line
  paths that are not supplied by trusted CI configuration.

The current HMAC is computed over the exact evidence-bundle bytes. It does not
authenticate the sidecar envelope. A verifier may check envelope fields for
consistency, but those fields cannot establish signer identity.

### Security goals

- Require an out-of-band expected key identity before making an authorization
  decision.
- Reject unknown, ambiguous, inactive-for-signing, or revoked keys.
- Keep secret key material outside repository policy files.
- Make policy, parsing, key-resolution, and signature failures distinguishable.
- Preserve the current byte-level tamper-detection claim without expanding it
  into artifact correctness or public identity.

### Non-goals

- Public-key identity, certificates, transparency logs, or remote key services.
- Proof of command execution, artifact safety, semantic correctness, or signing
  time.
- Recovery of trust after HMAC key disclosure.
- Automatic trust based on `key_hint`, filenames, repository ownership, or
  GitHub account names.

## Proposed policy format

The first policy version should be a local YAML or JSON document. This synthetic
example contains references only:

```yaml
policy_version: "1.0"
policy_id: "synthetic-maintainer-policy"
keys:
  - key_id: "maintainer-2026-a"
    algorithm: "hmac-sha256"
    key_ref: "env:REPRO_EVIDENCE_KEY_2026_A"
    state: "verify_only"
    not_before: "2026-01-01T00:00:00Z"
  - key_id: "maintainer-2026-b"
    algorithm: "hmac-sha256"
    key_ref: "file:/run/secrets/repro-evidence-key-2026-b"
    state: "active"
    not_before: "2026-06-01T00:00:00Z"
```

Required top-level fields:

| Field | Contract |
| --- | --- |
| `policy_version` | Exact supported policy schema version. |
| `policy_id` | Stable operator-chosen identifier for diagnostics and audit records. |
| `keys` | Non-empty list of unique key records. |

Required key fields:

| Field | Contract |
| --- | --- |
| `key_id` | Stable, unique, non-secret identifier selected out of band. |
| `algorithm` | Must match a supported algorithm; initially `hmac-sha256`. |
| `key_ref` | Non-secret resolver reference. It must not contain key bytes. |
| `state` | One of `active`, `verify_only`, or `revoked`. |
| `not_before` | Earliest policy time at which the key may be used. |

Optional key fields may include `revoked_at` and a short `comment`. The #62
parser rejects unknown fields rather than silently ignoring them. It also
rejects duplicate document keys, duplicate `key_id` values, embedded key
bytes, unsupported resolver schemes, malformed timestamps, and contradictory
state/timestamp combinations. It returns parsed data only; it does not resolve
key material or authorize a signer.

## Key selection and authorization

A future policy-aware verification command should require both the policy and
the expected key identity:

```bash
repro-evidence evidence verify-signature evidence-bundle.yaml \
  --signature evidence-bundle.yaml.sig.json \
  --trust-policy trust-policy.yaml \
  --key-id maintainer-2026-b
```

The verifier must:

1. Parse and validate the policy.
2. Find exactly one record matching the caller-supplied `key_id`.
3. Confirm that the algorithm and current state permit verification.
4. Resolve key material through the record's `key_ref`.
5. Verify the existing sidecar and exact payload bytes.
6. Report `key_hint` only as untrusted diagnostic metadata.

The verifier must not choose a key from `key_hint`, try every configured key
until one succeeds, or treat a matching hint as authorization. Those behaviors
would move signer selection into attacker-controlled input.

Signing should require an `active` key. Verification may use `active` or
`verify_only`; it must reject `revoked`.

## Local key resolvers

`repro_evidence_kit.key_resolver` resolves only parser-approved `env:` and
`file:` references. Environment values become UTF-8 bytes; files are read as
exact bytes without trimming or decoding. Empty material, missing references,
unreadable files, malformed references, unsupported schemes, and multiple
resolvers claiming the same scheme fail closed with stable
`KeyResolutionError.code` values.

Absolute file references use the default file resolver. A relative file
reference requires an explicit `FileKeyResolver(base_directory=...)`; it never
falls back to the process working directory.

Resolution returns key bytes only. It does not select a policy key, authorize a
key state, verify a signature, or permit signing. Fixtures remain synthetic;
policy files and repository content must not contain live key material.

## Rotation

Rotation uses an explicit overlap period:

| Step | Old key | New key | Result |
| --- | --- | --- | --- |
| 1. Prepare | `active` | absent | Old key signs and verifies. |
| 2. Overlap | `active` or `verify_only` | `active` | Callers explicitly select either allowed key. |
| 3. Retire old signing | `verify_only` | `active` | Old sidecars remain verifiable; new signing uses the new key. |
| 4. Revoke if required | `revoked` | `active` | Old-key verification fails closed. |

`verify_only` is a local policy control, not cryptographic proof that no new
sidecar was created with the old key. Anyone retaining the shared HMAC key can
still compute signatures.

## Revocation

Revocation is intentionally strict:

- A `revoked` key cannot sign or verify.
- `revoked_at` is diagnostic policy metadata, not a trusted signing-time test.
- A version 1 sidecar has no authenticated signing timestamp.
- Therefore the verifier cannot safely distinguish a sidecar created before
  revocation from one created after compromise.

Under this proposal, revocation invalidates all sidecars checked with that key.
Grandfathering old sidecars would require a separate trusted timestamp,
append-only observation record, or new authenticated sidecar design. That is
outside this HMAC policy version.

## Fail-closed CLI contract

Policy-aware commands should preserve the existing top-level exit convention:

| Exit | Policy-aware meaning |
| --- | --- |
| `0` | Policy allowed the selected key and the exact payload signature verified. |
| `1` | Expected trust or verification failure: unknown key, disallowed state, revoked key, algorithm mismatch, inactive key, payload mismatch, or signature mismatch. |
| `2` | Invocation or infrastructure failure: malformed policy, unreadable policy/key reference, unsupported resolver, malformed sidecar JSON, or dependency/runtime failure. |

Machine-readable results should add stable categories rather than requiring
callers to parse prose. Candidate categories are:

- `unknown_key_id`
- `key_not_active`
- `key_revoked`
- `policy_algorithm_mismatch`
- `policy_version_unsupported`
- `policy_invalid`
- `key_resolution_failed`

No policy failure may fall back to `key_hint`, another policy key, or the legacy
`--key` path.

## Version 1 sidecar compatibility

Existing sidecars remain structurally unchanged.

- Legacy `--key PATH` verification remains supported as local byte-level
  tamper detection.
- Policy-aware verification may validate a version 1 sidecar when the caller
  supplies an allowed `key_id` whose resolved key verifies the payload.
- `payload_path` and `key_hint` remain envelope metadata. They are not promoted
  to authenticated identity claims.
- Existing sidecars gain no signing-time, rotation, revocation, or public
  identity proof merely because a policy file is used.
- A future sidecar version that authenticates envelope fields requires a
  separate compatibility and migration proposal.

## Review gates before implementation

Implementation should remain split into independently reviewable work:

1. Freeze the threat model, policy state machine, and version 1 compatibility
   rules.
2. Add a schema and parser for non-secret policy documents only. This is
   implemented by `repro_evidence_kit.trust_policy` and the packaged
   `trust-policy.schema.json` copies; resolver and authorization behavior remain
   separate follow-up work.
3. Add resolver interfaces with synthetic environment/file fixtures. This is
   implemented by `repro_evidence_kit.key_resolver`; authorization, signing,
   and verification remain separate.
4. Add policy-aware verification and stable structured error categories. This
   is implemented by `repro_evidence_kit.policy_verification` and the
   `verify-signature --trust-policy ... --key-id ...` CLI mode.
5. Add policy-aware signing only after verification behavior is reviewed.

Each implementation slice must retain synthetic-only fixtures and must not claim
signer identity, artifact correctness, or trusted signing time.
