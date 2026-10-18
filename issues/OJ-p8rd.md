---
id: OJ-p8rd
title: "Fix non-atomic status persistence observed during browser retry"
status: open
priority: 1
type: bug
parent: OJ-a7l6
created_at: 2026-10-18T13:42:26Z
created_by: speed
updated_at: 2026-10-18T13:42:26Z
content_hash: "sha256:7ddcb9c95f960797b57b0e0dee138579ab6170d00580e8f80d434ea89dc87fb8"
blocks: [OJ-yf2c]
---

## Description
Observed during OJ-yf2c CUA on source 2b22504: real dry_run retry GET status returned HTTP500 JSONDecodeError line1col1 at app/main.py330. _set_status truncates status.json with write_text while status endpoint reads concurrently. UI safely locks duplicate run and Check status again recovers to COMPLETE. Scope: app/main.py persistence/read contract and deterministic concurrent-reader regression. AC: publish complete JSON atomically; readers never see partial JSON under bounded writer stress; preserve missing-job404 and job-state semantics; real local browser retry has no status500. No UI redesign, GPU, external API, or workflow changes. Requires bounded concurrency review before implementation. Evidence: docs/evidence/frontend-upgrade/browser/status-race-500.png and REPORT.md (capstone pending).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T13:55:48Z dep_added: blocks OJ-yf2c

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]

## Comments
