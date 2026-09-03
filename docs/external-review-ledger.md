# External review ledger

This ledger records external review feedback without treating it as broader than
its evidence. It separates collected comments, merged fixes, design-only work,
and still-unproven risks.

## Review-window policy

- The external-review ownership window ran through **2026-06-18 01:21 UTC**.
- During that window, external feedback was collected and classified rather than
  immediately merged or closed.
- After the window, each finding still needs a current GitHub/CI check before it
  can be merged, closed, or promoted into a release claim.
- A Colony-only or Moltbook-only comment is discovery evidence. Durable project
  records remain GitHub issues, pull requests, discussions, releases, or
  documented release evidence.

## Current repository state

Snapshot date: 2026-09-03.

At this snapshot, `main` matches `origin/main` at `3f14153f`, with no open pull
requests or issues. Historical merge records below remain useful evidence, but
they are not an active queue.

| Item | State | Boundary | Next action |
| --- | --- | --- | --- |
| PR #57, manifest provenance boundaries | Merged after fresh CI | Narrows manifest determinism wording, records implicit directory exclusions, updates schema copies, and documents the sidecar-boundary wording. | Use merged `main` evidence when deciding issue #56 closure. |
| PR #60, empty filtered manifest guard | Merged after conflict resolution and fresh CI | Narrow filter guard only: zero-file filtered selections fail by default and `--allow-empty` is explicit. | Include in the next release notes as a false-green fix. |
| PR #61, external review ledger | Merged after fresh CI | Documentation-only holding and classification surface. | Keep this ledger current when review state changes. |
| PR #58, signer trust policy | Merged after fresh CI | Design-only documentation. Does not itself implement signer trust, key rotation, revocation, process provenance, or identity trust. | Keep its design claims separate from the later #62-#65 implementation slices. |
| Issue #56, manifest determinism and implicit exclusions | Closed after PR #57 | Provenance wording, implicit exclusions, schema coverage, and sidecar-boundary docs landed on `main`. | Do not claim byte-reproducible manifest documents; `created_at` intentionally remains. |
| Issue #53, signer trust/key rotation/revocation | Closed after PR #58 | Issue closure records the design boundary; later parser, resolver, verification, and signing work landed as separate slices. | Preserve the implementation and non-goal boundaries recorded for #62-#65. |
| PR #79, Windows long-path manifest contract | Merged after fresh CI | Adds one synthetic manifest test whose artifact path exceeds 260 characters and is exercised by the Windows filesystem CI job. | Treat this as narrow runner-backed coverage, not universal Windows path support. |

## External feedback queue

| Source | Feedback | Classification | Current status | Follow-up |
| --- | --- | --- | --- | --- |
| Reticuli, The Colony | `--include` filters that match no files produced a successful empty manifest. | Confirmed external finding; false-green risk. | Merged via PR #60. | Preserve external attribution in release notes. |
| Reticuli, The Colony | `--exclude './reports'` did not match like `--exclude 'reports/'`. | Confirmed external finding; path-normalization risk. | Merged via PR #60. | Preserve external attribution in release notes. |
| Reticuli, The Colony | Manifest document is not byte-reproducible because `created_at` changes. | Claim-precision/provenance gap. | Addressed by PR #57 wording; `created_at` intentionally remains. | Do not claim byte-reproducible manifest documents. |
| Reticuli, The Colony | Built-in `.git` and `__pycache__` skips were not disclosed in manifest metadata. | Confirmed provenance disclosure gap. | Merged via PR #57 as `implicit_excluded_directories`. | Verify schema/readers before closing issue #56. |
| CauseClaw, The Colony | Raw-clone test path needed clearer dev dependency setup. | Adoption/documentation friction. | Addressed by PR #57 docs changes on `main`. | Keep README setup wording scoped to actual dev dependencies. |
| ∫ΔI Seed / Exori, The Colony | Artifact verification does not prove process provenance or an independent re-runner. | Design gap candidate, not an implemented feature and not an execution-verified defect. | Related to issue #53 / PR #58 design lane. | Keep design-only; require a concrete schema field, command, or verification predicate before implementation. |
| eliza-gemma, The Colony | Windows long path / MAX_PATH behavior may fail in deep artifact trees. | The broad report was a potential risk; one narrow predicate now has execution-backed coverage. | PR #79 added a synthetic path-over-260 manifest test, and the Windows filesystem CI job passed before merge. | Keep the result scoped to this test and runner configuration; other Windows path modes remain unproven. |
| eliza-gemma, The Colony | SARIF schema edge cases may be invalid under strict downstream validation. | Hypothesis until tested against a validator and concrete output. | No current defect claim. | Route through a validator-backed fixture if reopened. |
| voixgrave, The Colony | Voice perception research may be a useful artifact-review use case. | Possible use case, not repo proof and not a defect. | Needs fixture, command, and expected predicate. | Do not count as adoption proof without a runnable example. |

## Validation snapshot

Local checks run on 2026-06-18 after merging `main` into this ledger branch:

- `uv run pytest -q` -> 77 passed
- `uv run --extra schema pytest -q` -> 77 passed
- `python3 scripts/smoke_examples.py` -> passed

GitHub check snapshots used before merge:

- PR #57 after branch update: all required checks passed, then merged.
- PR #60 after conflict resolution against PR #57: all required checks passed,
  then merged.
- PR #61 after ledger update: all required checks passed, then merged.
- PR #58 after rebase onto merged manifest/ledger work: all required checks
  passed, then merged.

Current ledger refresh checks run on 2026-09-03:

- `uv run pytest -q` -> 118 passed, 32 subtests passed
- `uv run --extra schema pytest -q` -> 118 passed, 32 subtests passed
- `uv run python3 scripts/smoke_examples.py` -> passed

## Completed follow-up implementations

| Issue | Merged implementation | Implemented scope | Boundary retained |
| --- | --- | --- | --- |
| #62 | PR #69 | Synthetic-only signer trust policy schema and parser. | No key resolution, signing, verification, public identity, or secret material. |
| #63 | PR #70 | Local `env:`/`file:` key resolver interfaces with synthetic fixtures and fail-closed errors. | Resolution does not authorize policy state, sign, verify, or establish signer identity. |
| #64 | PR #71 | Policy-aware signature verification with caller-selected policy/key identity and stable result categories. | No policy-aware signing, public identity, trusted signing-time proof, or artifact-correctness claim. |
| #65 | PR #72 | Policy-aware signing for caller-selected active policy keys with unchanged version 1 sidecars. | No public identity, certificate chain, transparency log, trusted signing time, or artifact-correctness claim. |

## Non-goals still active

- Do not broaden the narrow Windows long-path test into a universal Windows
  support claim, or implement further SARIF, process-provenance, or voice-domain
  work from this ledger without a separate scoped issue or PR.
- Do not turn the local policy controls into claims of public signer identity,
  trusted signing time, artifact correctness, process provenance, or disjoint
  re-runner identity.
- Do not count external comments as adoption proof without a durable artifact,
  issue, PR, release evidence, or runnable example.
