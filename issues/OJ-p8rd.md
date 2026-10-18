---
id: OJ-p8rd
title: "Fix non-atomic status persistence observed during browser retry"
status: closed
priority: 1
type: bug
parent: OJ-a7l6
created_at: 2026-10-18T13:42:26Z
created_by: speed
updated_at: 2026-10-18T14:12:13Z
content_hash: "sha256:c9951f89ef874541bedd154552127ccdc70fc3bf1c97e8cde3cfe4fa1729df4f"
assignee: dev-OJ-p8rd
follows: [OJ-inuo, OJ-xtk4]
labels: [accepted]
closed_at: 2026-10-18T14:11:21Z
close_reason: "Accepted: a7ed346 atomically replaces same-directory status snapshots, preserves 404/state behavior, passes focused and legacy-control verification, all recorded hashes/browser receipts match, and scope remains app/main.py plus dedicated tests/evidence."
led_to: [OJ-yf2c, OJ-c1vo]
---

## Description
Observed during OJ-yf2c CUA on source 2b22504: real dry_run retry GET status returned HTTP500 JSONDecodeError line1col1 at app/main.py330. _set_status truncates status.json with write_text while status endpoint reads concurrently. UI safely locks duplicate run and Check status again recovers to COMPLETE. Scope: app/main.py persistence/read contract and deterministic concurrent-reader regression. AC: publish complete JSON atomically; readers never see partial JSON under bounded writer stress; preserve missing-job404 and job-state semantics; real local browser retry has no status500. No UI redesign, GPU, external API, or workflow changes. Requires bounded concurrency review before implementation. Evidence: docs/evidence/frontend-upgrade/browser/status-race-500.png and REPORT.md (capstone pending).

## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-10-18]: Independent evidence review at story HEAD a7ed346407ad0f97cdf80795132c6655995e5a9b meets the bounded story bar.

## nd_contract
status: accepted

### evidence
- Reviewed pm_acceptor requirements, OJ-p8rd notes, delivery preflight (9/9), and the exact story diff from base 2b225041402b155ad3ed42582d6e0d63cbf99946; non-evidence scope is only app/main.py and tests/test_status_atomic.py.
- Independently ran PYTHONPATH=src with the root project virtualenv: tests/test_status_atomic.py => 7 passed, 1 disclosed preexisting Starlette/httpx deprecation warning, 0 failed (0.59s); git diff --check clean; stub/TODO scan clean.
- Independently ran the committed source-Ast legacy control: exit 1 as expected because base 2b22504 truncating writer yields HTTP 500 while the repaired publication boundary requires HTTP 200.
- Verified all 9 entries in docs/evidence/status-atomic/OJ-p8rd/SHA256SUMS and all 5 entries in browser/SHA256SUMS.json. Current app/main.py SHA-256 is ace2ab9e2a658fdb60e9f75594a53271f8adc3f40b53430ecfce9e8649b24aa1, matching REPORT.md and browser receipt.
- Reaggregated browser/requests.jsonl: 21 local requests, 4 status GETs all HTTP 200, 0 status HTTP 500, and exactly 1 intentional run HTTP 404; receipt reports dry_run, inference_spend 0, downloaded final hash match, and synthetic-source fixture use.
- Did not rerun the already-recorded full suite or perform browser/network/GPU operations. Accepted limits: in-process atomic visibility only; no multiprocess coordinator, queue-admission redesign, fsync/crash durability, or live 8893 deployment claim.

### proof
- [x] AC #1: app/main.py:138-163 serializes read/merge/publish, writes a unique same-directory temporary snapshot, and atomically replaces status.json before updating memory; failure tests preserve disk/memory and clean temporary files.
- [x] AC #2: The base-source control deterministically fails with the old truncation HTTP 500; the fixed boundary/concurrent tests pass, including 3 writers/3 readers/180 coherent requests plus invalid/missing-job 404 behavior.
- [x] AC #3: Committed real-browser receipts show retry reaches COMPLETE with four status GETs all 200/zero 500, deliberate missing-job 404, keyboard recovery, and byte-identical final download.
- [x] AC #4: Scope, tests, sanitized local-only evidence, and all recorded hash manifests were independently verified at a7ed346.

## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-10-18.

### proof
- [x] Story closed after accepted label was applied.


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
- Led to: [[OJ-yf2c]], [[OJ-c1vo]]

## Comments
