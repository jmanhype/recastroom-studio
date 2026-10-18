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
content_hash: "sha256:20af07dad1af97097eeadec9a8aa77c7bae5dc268af1eda839f5c2e8511ef49f"
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
