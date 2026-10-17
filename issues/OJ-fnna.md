---
id: OJ-fnna
title: "Ship the Openjutsu contest production lane"
status: open
priority: 0
type: epic
labels: [contest, openjutsu]
created_at: 2026-10-17T16:25:53Z
created_by: speed
updated_at: 2026-10-17T22:05:49Z
content_hash: "sha256:d953c38b8013b6efd8324167b8931553deb6395603ec54a924b708ff47dee158"
---

## Description

## Goal

Finish the rights-clean Openjutsu Studio submission with independently verifiable
execution, packaging, deployment, demo, and compliance evidence.

## Global out-of-scope

- No worker publishes the repository, posts socially, or submits the Typeform.
- No worker handles credentials or spends GPU/compute units.
- Those actions remain owner-gated after the evidence gate passes.

## nd_contract
status: new

### evidence
- Initialized from `docs/CONTEST.md`, `docs/SUBMISSION_CHECKLIST.md`, and `STATUS.md`.
- Baseline repository commit: `d9ff276` (`Openjutsu Studio v0.1.1`).

### proof
- [ ] AC #1: All six child stories are closed with command output, artifact paths, and hashes where applicable.
- [ ] AC #2: The final gate proves the public package uses only rights-clean material and passes the contest checklist without publishing.


## Acceptance Criteria


## Design


## Notes
## ANCHOR REVIEW (MILESTONE_REVIEW)
REVIEW_RESULT: GAPS_FOUND

### Gaps
1. Boundary-reference preflight fails: capstone OJ-mbn5 retains `was_blocked_by: OJ-b71t`, but `pvg issues show OJ-b71t` and `pvg nd show OJ-b71t` both return not-found. `pvg nd search OJ-b71t` confirms the unresolved reference in `issues/OJ-mbn5.md` history/links. (Impact: milestone ordering/capstone evidence cites an issue that cannot be resolved or accepted; Fix: repair the live dependency history/link using a supported nd/pvg maintenance path—restore or replace the phantom reference with the actual OJ-2gs4 repair relationship, or remove the stale historical edge without altering accepted story statuses—then rerun cycle/reference preflight.)
2. New-module quality gate fails: `pvg gates app src scripts tools` exits 1 with `src/openjutsu/evidence.py:verify_manifest` CCN 74 (threshold 30) at line 240 and the same file at 417 non-blank lines (threshold 400). (Impact: the fail-closed evidence verifier is too concentrated for safe maintenance and violates the active production quality gate; Fix: decompose manifest/approval/keeper/artifact/path verification into focused helpers while retaining public signatures and all fail-closed tests, then require `pvg gates app src scripts tools` to pass.)

### Missing Story Types
- None identified. The epic has a capstone/final gate, real local API/browser E2E wiring, rights/security scanning, packaging, deployment-boundary documentation, and owner-gated external actions.

### Evidence Expectations
- Repair evidence must show every issue ID referenced by epic-subtree CONSUMES/blocked-by/capstone links resolving via `pvg issues show`, `pvg nd dep cycles` clean, and no stale issues.
- Repair evidence must show production quality gates passing (`pvg gates app src scripts tools`) plus the existing full suite and final gate.
- Production type coverage passed an AST scan of 37 changed Python files: 149 public functions found, 0 production signature gaps; the 18 unannotated functions are tests/helpers only.
- Owner-gated publication/live-SDK/fresh-install items are not classified as epic gaps. At integrated main 0685930, hash-verified final-gate evidence reports release audit errors=[], tests exit 0 (31 passed/1 disclosed warning), pip check exit 0, and matrix PASS=11/FAIL=0/OWNER_BLOCKED=8.
- Verified at review: epic and all seven children are closed/accepted; no dependency cycles; no stale issues; `pvg verify --check-e2e` passes with two e2e files; independent full pytest=31 passed/1 disclosed warning and pip check clean; keeper verifier=11 keepers/48 artifacts; worktree clean.

## History
- 2026-10-17T21:32:35Z status: open -> closed
- 2026-10-17T21:35:23Z status: closed -> open (reopened)
- 2026-10-17T21:51:57Z status: open -> closed
- 2026-10-17T22:05:49Z status: closed -> open (reopened)

## Links


## Comments
