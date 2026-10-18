---
id: OJ-p8rd
title: "Fix non-atomic status persistence observed during browser retry"
status: in_progress
priority: 1
type: bug
parent: OJ-a7l6
created_at: 2026-10-18T13:42:26Z
created_by: speed
updated_at: 2026-10-18T14:06:13Z
content_hash: "sha256:f03298f7ba8a508b5a691048be05d4c0ad509d20b81eb105e7cf163d3ae11db7"
blocks: [OJ-yf2c]
assignee: dev-OJ-p8rd
follows: [OJ-inuo, OJ-xtk4]
labels: [delivered]
---

## Description
Observed during OJ-yf2c CUA on source 2b22504: real dry_run retry GET status returned HTTP500 JSONDecodeError line1col1 at app/main.py330. _set_status truncates status.json with write_text while status endpoint reads concurrently. UI safely locks duplicate run and Check status again recovers to COMPLETE. Scope: app/main.py persistence/read contract and deterministic concurrent-reader regression. AC: publish complete JSON atomically; readers never see partial JSON under bounded writer stress; preserve missing-job404 and job-state semantics; real local browser retry has no status500. No UI redesign, GPU, external API, or workflow changes. Requires bounded concurrency review before implementation. Evidence: docs/evidence/frontend-upgrade/browser/status-race-500.png and REPORT.md (capstone pending).

## Acceptance Criteria


## Design


## Notes
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

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]
- Follows: [[OJ-inuo]], [[OJ-xtk4]]

## Comments
