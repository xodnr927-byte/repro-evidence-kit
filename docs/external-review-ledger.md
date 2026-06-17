# External review ledger

This ledger records external review feedback without treating it as already
implemented or accepted. It is a holding surface for review-window triage, not a
fix list.

## Hold policy

- External-review feedback is collected during the current ownership window.
- Do not merge, close, or implement external-review findings from this ledger
  before **2026-06-18 01:21 UTC** unless the maintainer explicitly lifts the
  hold.
- During the hold, allowed actions are limited to collecting links, classifying
  the claim, preserving attribution, and recording current proof boundaries.
- A Colony-only comment is discovery evidence. Durable project records remain
  GitHub issues, pull requests, discussions, releases, or documented release
  evidence.

## Current repository queue

Snapshot date: 2026-06-16.

| Item | State | Boundary | Next action after hold |
| --- | --- | --- | --- |
| PR #57, manifest provenance boundaries | Open, ready-for-review, behind `main` | External review window remains active until 2026-06-18 01:21 UTC. | Re-check reviews, threads, mergeability, and CI before any merge. |
| PR #58, signer trust policy | Open draft, behind `main` | Design-only. Does not implement signer trust, key rotation, revocation, or identity trust. | Rebase after PR #57, then review against issue #53. |
| PR #60, empty filtered manifest guard | Open draft, clean, CI green | Narrow filter guard only. Not merged or released; does not close the broader provenance/design work. | Decide whether to keep draft, mark ready, or merge after attribution/hold review. |
| Issue #56, manifest determinism and implicit exclusions | Open | Tracks provenance wording, implicit exclusions, schema coverage, and sidecar-boundary docs. | Close only after the merged PR state satisfies the acceptance criteria. |
| Issue #53, signer trust/key rotation/revocation | Open | Design problem; current docs must not imply implementation. | Split implementation tasks only after design review is merged. |

## External feedback queue

| Source | Feedback | Classification | Current status | Deferred action |
| --- | --- | --- | --- | --- |
| Reticuli, The Colony | `--include` filters that match no files produced a successful empty manifest. | Confirmed external finding; false-green risk. | Addressed only in draft PR #60; not merged/released. | Preserve attribution; decide PR #60 after hold. |
| Reticuli, The Colony | `--exclude './reports'` did not match like `--exclude 'reports/'`. | Confirmed external finding; path-normalization risk. | Addressed only in draft PR #60; not merged/released. | Preserve attribution; decide PR #60 after hold. |
| Reticuli, The Colony | Manifest document is not byte-reproducible because `created_at` changes. | Claim-precision/provenance gap. | Tracked by issue #56 and PR #57; `created_at` intentionally remains. | Re-check PR #57 after hold. |
| Reticuli, The Colony | Built-in `.git` and `__pycache__` skips were not disclosed in manifest metadata. | Confirmed provenance disclosure gap. | Tracked by issue #56 and PR #57. | Re-check PR #57 after hold. |
| CauseClaw, The Colony | Raw-clone test path needed clearer dev dependency setup. | Adoption/documentation friction. | Tracked by PR #57 docs changes; not current `main`. | Re-check PR #57 after hold. |
| ∫ΔI Seed / Exori, The Colony | Artifact verification does not prove process provenance or an independent re-runner. | Design gap candidate, not an implemented feature and not an execution-verified defect. | Related to issue #53 / PR #58 design lane. | Keep design-only; require a concrete schema field, command, or verification predicate before implementation. |
| eliza-gemma, The Colony | Windows long path / MAX_PATH behavior may fail in deep artifact trees. | Potential risk; not execution-verified by the reporter. | Existing Windows CI does not prove this exact predicate. | After hold, consider a small Windows-only repro test/report before any broad rewrite. |
| eliza-gemma, The Colony | SARIF schema edge cases may be invalid under strict downstream validation. | Hypothesis until tested against a validator and concrete output. | No current defect claim. | After hold, route through a validator-backed fixture if reopened. |
| voixgrave, The Colony | Voice perception research may be a useful artifact-review use case. | Possible use case, not repo proof and not a defect. | Needs fixture, command, and expected predicate. | Do not count as adoption proof without a runnable example. |

## Validation snapshot

Local checks run on 2026-06-16 from `main` after creating this ledger branch:

- `uv run pytest -q` -> 71 passed
- `uv run --extra schema pytest -q` -> 71 passed
- `python3 scripts/smoke_examples.py` -> passed

GitHub check snapshot for PR #60 on 2026-06-16:

- Python 3.10, 3.11, and 3.12 -> pass
- Windows filesystem contract -> pass
- Static analysis and coverage -> pass
- Dependency audit and SBOM -> pass
- Build package distributions -> pass

## Non-goals before the hold expires

- Do not merge PR #57, PR #58, or PR #60.
- Do not implement Windows long-path, SARIF, process-provenance, or voice-domain
  follow-up work.
- Do not close issues #53 or #56.
- Do not claim external-review findings are resolved on `main` until merged and
  revalidated.
