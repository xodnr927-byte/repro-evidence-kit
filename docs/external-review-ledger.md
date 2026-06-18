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

## Current repository queue

Snapshot date: 2026-06-18.

| Item | State | Boundary | Next action |
| --- | --- | --- | --- |
| PR #57, manifest provenance boundaries | Merged after fresh CI | Narrows manifest determinism wording, records implicit directory exclusions, updates schema copies, and documents the sidecar-boundary wording. | Use merged `main` evidence when deciding issue #56 closure. |
| PR #60, empty filtered manifest guard | Merged after conflict resolution and fresh CI | Narrow filter guard only: zero-file filtered selections fail by default and `--allow-empty` is explicit. | Include in the next release notes as a false-green fix. |
| PR #61, external review ledger | Merged after fresh CI | Documentation-only holding and classification surface. | Keep this ledger current when review state changes. |
| PR #58, signer trust policy | Merged after fresh CI | Design-only documentation. Does not implement signer trust, key rotation, revocation, process provenance, or identity trust. | Implementation split into follow-up issues #62-#65. |
| Issue #56, manifest determinism and implicit exclusions | Closed after PR #57 | Provenance wording, implicit exclusions, schema coverage, and sidecar-boundary docs landed on `main`. | Do not claim byte-reproducible manifest documents; `created_at` intentionally remains. |
| Issue #53, signer trust/key rotation/revocation | Closed after PR #58 | Design issue only; no runtime/schema/resolver/CLI implementation is claimed by closure. | Follow implementation issues #62-#65 separately. |

## External feedback queue

| Source | Feedback | Classification | Current status | Follow-up |
| --- | --- | --- | --- | --- |
| Reticuli, The Colony | `--include` filters that match no files produced a successful empty manifest. | Confirmed external finding; false-green risk. | Merged via PR #60. | Preserve external attribution in release notes. |
| Reticuli, The Colony | `--exclude './reports'` did not match like `--exclude 'reports/'`. | Confirmed external finding; path-normalization risk. | Merged via PR #60. | Preserve external attribution in release notes. |
| Reticuli, The Colony | Manifest document is not byte-reproducible because `created_at` changes. | Claim-precision/provenance gap. | Addressed by PR #57 wording; `created_at` intentionally remains. | Do not claim byte-reproducible manifest documents. |
| Reticuli, The Colony | Built-in `.git` and `__pycache__` skips were not disclosed in manifest metadata. | Confirmed provenance disclosure gap. | Merged via PR #57 as `implicit_excluded_directories`. | Verify schema/readers before closing issue #56. |
| CauseClaw, The Colony | Raw-clone test path needed clearer dev dependency setup. | Adoption/documentation friction. | Addressed by PR #57 docs changes on `main`. | Keep README setup wording scoped to actual dev dependencies. |
| ∫ΔI Seed / Exori, The Colony | Artifact verification does not prove process provenance or an independent re-runner. | Design gap candidate, not an implemented feature and not an execution-verified defect. | Related to issue #53 / PR #58 design lane. | Keep design-only; require a concrete schema field, command, or verification predicate before implementation. |
| eliza-gemma, The Colony | Windows long path / MAX_PATH behavior may fail in deep artifact trees. | Potential risk; not execution-verified by the reporter. | Existing Windows CI does not prove this exact predicate. | Consider a small Windows-only repro test/report before any broad rewrite. |
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

## Follow-up implementation queue

| Issue | Scope | Boundary |
| --- | --- | --- |
| #62 | Signer trust policy schema and parser | No key resolution, signing, verification, public identity, or secret material. |
| #63 | Local key resolver interfaces with synthetic fixtures | No policy-aware signing/verification or live secrets. |
| #64 | Policy-aware signature verification | No policy-aware signing, public identity, signing-time proof, or safety claims. |
| #65 | Policy-aware signing after verification behavior is reviewed | Waits for #64; no public identity, certificate chain, transparency log, or artifact correctness claims. |

## Non-goals still active

- Do not implement Windows long-path, SARIF, process-provenance, or voice-domain
  follow-up work from this ledger without a separate scoped issue or PR.
- Do not claim signer trust, key rotation, revocation, process provenance, or
  disjoint re-runner identity as implemented until code and verification exist.
- Do not count external comments as adoption proof without a durable artifact,
  issue, PR, release evidence, or runnable example.
