---
id: OJ-a7l6
title: "Cinematic local Openjutsu studio frontend upgrade"
status: closed
priority: 1
type: epic
labels: [frontend, local]
created_at: 2026-10-18T01:53:45Z
created_by: speed
updated_at: 2026-10-18T19:48:25Z
content_hash: "sha256:34114ad9bfc031dea5206906bdcdf87bc64f6b2bb9c3bf27682a08f51a0d7274"
closed_at: 2026-10-18T19:48:25Z
close_reason: "All child stories accepted; final capstone PM-approved and merged; merged epic suite 105 passed with one disclosed warning."
---

## Description

## Description
## Goal
Upgrade the existing rights-aware vanilla Openjutsu Studio interface into a cinematic, truthful, local-first production surface while preserving the accepted backend/API and generation boundary.

## USER INTENT
An authorized creator can clearly upload owned source material and performer references, understand every production stage, compare output to source, download real artifacts, and recover from local errors without fabricated progress or rights shortcuts.

## Scope
- Static frontend work under `app/web/`, including the owner-approved portrait intrinsic-preview repair in OJ-4rht.
- Owner-approved bounded local media export repairs: paired-review aspect preservation (OJ-xtk4) and source audio layout/loudness preservation (OJ-inuo).
- Local dry-run browser verification and deterministic regressions; all generated evidence stays local.
- Preserve generation/API semantics. These are post-generation export/UI defects, not generation redesign work.

## Global Out Of Scope
- No publication, social posting, remote deployment, push, credentials, GPU/compute spend, or cloud inference.
- No mandatory React migration or new runtime/package dependency.
- No backend/API/generation redesign, generation-workflow change, progress-UX redesign, remote inference, or paid API/GPU spend.
- The coarse-progress dogfood observation is intentionally out of this approved repair epic.

## nd_contract
status: new

### evidence
- Approved local frontend upgrade at main `7ab3b8c`.
- Previous contest epic is closed; baseline full suite is 31 passing tests.

### proof
- [ ] OJ-4rht rework, OJ-xtk4, OJ-inuo, and dependent capstone OJ-yf2c are delivered with local deterministic evidence; no push, GPU, paid API, or cloud inference is used.

## Acceptance Criteria


## Design


## Notes
REVIEW_RESULT: APPROVED
Independent backlog Anchor frontend_backlog_anchor approved current two-story scope after native nd recovery. pvg lint: 0 errors, 2 nonblocking credential-provisioning reviews because all API use is local dry_run with no keys. RTM extracted 0 requirements; not coverage proof. Developer OJ-4rht gate opened. Local commits/merges only; no remote configured.

## History


## Links


## Comments


## Goal
Upgrade the existing rights-aware vanilla Openjutsu Studio interface into a cinematic, truthful, local-first production surface while preserving the accepted backend/API and generation boundary.

## USER INTENT
An authorized creator can clearly upload owned source material and performer references, understand every production stage, compare output to source, download real artifacts, and recover from local errors without fabricated progress or rights shortcuts.

## Scope
- Static frontend work under `app/web/`.
- Local dry-run browser verification and deterministic regressions.
- Preserve backend/API behavior and generation semantics.

## Global Out Of Scope
- No publication, social posting, remote deployment, push, credentials, GPU/compute spend, or cloud inference.
- No mandatory React migration or new runtime/package dependency.
- No backend/API/generation redesign.

## nd_contract
status: new

### evidence
- Approved local frontend upgrade at main `7ab3b8c`.
- Previous contest epic is closed; baseline full suite is 31 passing tests.

### proof
- [ ] The two dependent child stories are delivered with local browser/screenshot evidence and deterministic test output.

## Acceptance Criteria


## Design


## Notes
REVIEW_RESULT: APPROVED
Independent backlog Anchor frontend_backlog_anchor approved current two-story scope after native nd recovery. pvg lint: 0 errors, 2 nonblocking credential-provisioning reviews because all API use is local dry_run with no keys. RTM extracted 0 requirements; not coverage proof. Developer OJ-4rht gate opened. Local commits/merges only; no remote configured.
Owner-approved bounded scope extension: repair false-positive legacy renderer readiness in OJ-c1vo; preserve SDK/generation/media semantics and design. Parent checks existing Colab connection separately; no new render is authorized by this repair story.
## Implementation Evidence
Summary: Completed and integrated the cinematic local Openjutsu studio epic after independent PM acceptance of the final browser capstone.
Commit SHA: 0e8e3fb8808e9518c2ece8224c900378747924cc
Branch: epic/OJ-a7l6

### CI/Test Results
PROOF:
Commands run:
- `PYTHONPATH=src <repo>/.venv/bin/python -m pytest -q` on merged epic commit `0e8e3fb`.
- Result: 105 passed, 1 existing Starlette/httpx warning in 28.92s; no skips.
- Story OJ-yf2c independently passed focused/full suites twice and PM re-review approved commit `11ba30e`.

### AC Verification
| AC | Verification | Result |
|---|---|---|
| 1 | OJ-4rht, OJ-xtk4, OJ-inuo, OJ-p8rd, OJ-c1vo, OJ-krar, OJ-tfyt, and OJ-yf2c completed through Paivot delivery/acceptance | PASS |
| 2 | Final browser capstone proves real dry-run flow, reduced motion, exhaustive focus, recovery, runtime provenance, and cleanup | PASS |
| 3 | Accepted OJ-yf2c merged locally into epic `0e8e3fb`; merged epic suite passes | PASS |
| 4 | No push, publication, GPU/API inference, credential use, or public tunnel | PASS |

LEARNINGS: The final capstone required reconciling its stale health assertion with the accepted additive renderer-readiness contract.
OBSERVATIONS: All child work is accepted; the local epic is ready for main integration.

## nd_contract
status: accepted

### evidence
- Merged epic commit `0e8e3fb8808e9518c2ece8224c900378747924cc`.
- Independent PM approval for final OJ-yf2c fix commit `11ba30ee71cec9ed8872b321cda7dca0e914f2a2`.
- Merged epic full suite: 105 passed, 1 warning.

### proof
- [x] Epic goal and local-only boundary are satisfied.

## History
- 2026-10-18T19:48:25Z status: open -> closed

## Links


## Comments
