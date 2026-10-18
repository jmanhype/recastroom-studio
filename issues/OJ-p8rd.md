---
id: OJ-p8rd
title: "Fix non-atomic status persistence observed during browser retry"
status: closed
priority: 1
type: bug
parent: OJ-a7l6
created_at: 2026-10-18T13:42:26Z
created_by: speed
updated_at: 2026-10-18T14:11:21Z
content_hash: "sha256:6c37edf4a6474ffab9c87eddd90f3b7616c09b5d2696603318d1663749292858"
assignee: dev-OJ-p8rd
follows: [OJ-inuo, OJ-xtk4]
labels: [accepted]
closed_at: 2026-10-18T14:11:21Z
close_reason: "Accepted: a7ed346 atomically replaces same-directory status snapshots, preserves 404/state behavior, passes focused and legacy-control verification, all recorded hashes/browser receipts match, and scope remains app/main.py plus dedicated tests/evidence."
---

## Description
Observed during OJ-yf2c CUA on source 2b22504: real dry_run retry GET status returned HTTP500 JSONDecodeError line1col1 at app/main.py330. _set_status truncates status.json with write_text while status endpoint reads concurrently. UI safely locks duplicate run and Check status again recovers to COMPLETE. Scope: app/main.py persistence/read contract and deterministic concurrent-reader regression. AC: publish complete JSON atomically; readers never see partial JSON under bounded writer stress; preserve missing-job404 and job-state semantics; real local browser retry has no status500. No UI redesign, GPU, external API, or workflow changes. Requires bounded concurrency review before implementation. Evidence: docs/evidence/frontend-upgrade/browser/status-race-500.png and REPORT.md (capstone pending).

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

### CI/Test Results
Commands run:
  - PYTHONPATH=src <repo>/.venv/bin/python docs/evidence/status-atomic/OJ-p8rd/verify.py
  - PYTHONPATH=src <repo>/.venv/bin/python -m pytest tests/test_status_atomic.py -q
  - shasum -a 256 -c docs/evidence/status-atomic/OJ-p8rd/SHA256SUMS
  - git diff --check
Summary: focused7 PASSx3; full48 PASS; parent focused7 PASS; original-code control500 vs expected200 FAIL as intended; all recorded hashes PASS; CUA retry COMPLETE, zero500.
- Coverage: no statement/branch percentage claimed.

### Commit
- Branch: story/OJ-p8rd
- SHA: a7ed346

### AC Verification
| AC # | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Atomic coherent publication and cleanup | app/main.py _set_status; barrier/failure tests | PASS |
| 2 | Old fail, new concurrent reads pass and404/schema preserved | tests/test_status_atomic.py; legacy-control/full-suite logs | PASS |
| 3 | Real browser retry without500 | BROWSER.md; browser/events.json; requests.jsonl | PASS |
| 4 | Bounded scope, tests and sanitized evidence | committed diff; SHA256SUMS; browser manifest | PASS |

## nd_contract
status: delivered

### evidence
- Source scope: app/main.py only; dedicated in-process status lock, copy-on-write snapshots, same-directory unique temporary file and os.replace. No UI/media/workflow changes.
- New tests/test_status_atomic.py: 7 passed on three worker runs and coordinator rerun (0.52s); full suite48 passed, one existing warning. Actual base-commit writer fails controlled regression with500, fixed200.
- docs/evidence/status-atomic/OJ-p8rd/REPORT.md, BROWSER.md, captured outputs, SHA256SUMS and browser/ receipts independently checked. Real CUA retry job85b97f14514e completes; four status GETs all200, zero500; deliberate missing-job run404 and keyboard recovery succeeds. Download byte verified.
- Local-only, no inference/GPU spend. Tests use isolated data; production8893 untouched. No multiprocess coordinator or crash-durability promise.

### proof
- [x] AC #1: Status publication is atomic; serialized in-process updates publish coherent disk/memory snapshots, unique same-directory temps, exception cleanup.
- [x] AC #2: Old writer deterministically fails; fixed barrier, 3writers/3readers180requests, failure preservation, schema and missing/invalid404 tests pass repeatedly.
- [x] AC #3: Real local browser retry completes without status500; duplicate-prevention and missing-job recovery remain functional.
- [x] AC #4: Patch scope preserved, full suite passes, sanitized logs/screenshots/hash evidence exists; no UI/GPU/external changes.

LEARNINGS: Atomic rename removes the exposed truncation window; serial client tests alone missed this defect.

OBSERVATIONS: Local preview8893 restart and capstone acceptance pending independent PM review. No full release claim.

## Implementation Evidence (DELIVERED)

### CI/Test Results
- Commands run:
  - PYTHONPATH=src <repo>/.venv/bin/python docs/evidence/status-atomic/OJ-p8rd/verify.py
  - PYTHONPATH=src <repo>/.venv/bin/python -m pytest tests/test_status_atomic.py -q
  - shasum -a 256 -c docs/evidence/status-atomic/OJ-p8rd/SHA256SUMS
  - git diff --check
- Summary: focused7 PASSx3; full48 PASS; parent focused7 PASS; original-code control500 vs expected200 FAIL as intended; all recorded hashes PASS; CUA retry COMPLETE, zero500.
- Coverage: no statement/branch percentage claimed.

### Commit
- Branch: story/OJ-p8rd
- SHA: a7ed346

### AC Verification
| AC # | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Atomic coherent publication and cleanup | app/main.py _set_status; barrier/failure tests | PASS |
| 2 | Old fail, new concurrent reads pass and404/schema preserved | tests/test_status_atomic.py; legacy-control/full-suite logs | PASS |
| 3 | Real browser retry without500 | BROWSER.md; browser/events.json; requests.jsonl | PASS |
| 4 | Bounded scope, tests and sanitized evidence | committed diff; SHA256SUMS; browser manifest | PASS |

## nd_contract
status: delivered

### evidence
- Source scope: app/main.py only; dedicated in-process status lock, copy-on-write snapshots, same-directory unique temporary file and os.replace. No UI/media/workflow changes.
- New tests/test_status_atomic.py: 7 passed on three worker runs and coordinator rerun (0.52s); full suite48 passed, one existing warning. Actual base-commit writer fails controlled regression with500, fixed200.
- docs/evidence/status-atomic/OJ-p8rd/REPORT.md, BROWSER.md, captured outputs, SHA256SUMS and browser/ receipts independently checked. Real CUA retry job85b97f14514e completes; four status GETs all200, zero500; deliberate missing-job run404 and keyboard recovery succeeds. Download byte verified.
- Local-only, no inference/GPU spend. Tests use isolated data; production8893 untouched. No multiprocess coordinator or crash-durability promise.

### proof
- [x] AC #1: Status publication is atomic; serialized in-process updates publish coherent disk/memory snapshots, unique same-directory temps, exception cleanup.
- [x] AC #2: Old writer deterministically fails; fixed barrier, 3writers/3readers180requests, failure preservation, schema and missing/invalid404 tests pass repeatedly.
- [x] AC #3: Real local browser retry completes without status500; duplicate-prevention and missing-job recovery remain functional.
- [x] AC #4: Patch scope preserved, full suite passes, sanitized logs/screenshots/hash evidence exists; no UI/GPU/external changes.

LEARNINGS: Atomic rename removes the exposed truncation window; serial client tests alone missed this defect.

OBSERVATIONS: Local preview8893 restart and capstone acceptance pending independent PM review. No full release claim.

## nd_contract
status: delivered

### evidence
- Source scope: app/main.py only; dedicated in-process status lock, copy-on-write snapshots, same-directory unique temporary file and os.replace. No UI/media/workflow changes.
- New tests/test_status_atomic.py: 7 passed on three worker runs and coordinator rerun (0.52s); full suite48 passed, one existing warning. Actual base-commit writer fails controlled regression with500, fixed200.
- docs/evidence/status-atomic/OJ-p8rd/REPORT.md, BROWSER.md, captured outputs, SHA256SUMS and browser/ receipts independently checked. Real CUA retry job85b97f14514e completes; four status GETs all200, zero500; deliberate missing-job run404 and keyboard recovery succeeds. Download byte verified.
- Local-only, no inference/GPU spend. Tests use isolated data; production8893 untouched. No multiprocess coordinator or crash-durability promise.

### proof
- [x] AC #1: Status publication is atomic; serialized in-process updates publish coherent disk/memory snapshots, unique same-directory temps, exception cleanup.
- [x] AC #2: Old writer deterministically fails; fixed barrier, 3writers/3readers180requests, failure preservation, schema and missing/invalid404 tests pass repeatedly.
- [x] AC #3: Real local browser retry completes without status500; duplicate-prevention and missing-job recovery remain functional.
- [x] AC #4: Patch scope preserved, full suite passes, sanitized logs/screenshots/hash evidence exists; no UI/GPU/external changes.

LEARNINGS: Atomic rename removes the exposed truncation window; serial client tests alone missed this defect.

OBSERVATIONS: Local preview8893 restart and capstone acceptance pending independent PM review. No full release claim.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-10-18T13:55:48Z dep_added: blocks OJ-yf2c
- 2026-10-18T13:56:09Z status: open -> in_progress
- 2026-10-18T13:56:09Z auto-follows: linked to predecessor OJ-inuo
- 2026-10-18T13:56:09Z claimed by dev-OJ-p8rd
- 2026-10-18T14:06:13Z status: in_progress -> in_progress
- 2026-10-18T14:06:13Z auto-follows: linked to predecessor OJ-xtk4
- 2026-10-18T14:11:21Z status: in_progress -> closed
- 2026-10-18T14:11:21Z dep_removed: no_longer_blocks OJ-yf2c

## Links
- Parent: [[OJ-a7l6]]
- Follows: [[OJ-inuo]], [[OJ-xtk4]]

## Comments
