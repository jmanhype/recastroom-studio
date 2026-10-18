---
id: OJ-p8rd
title: "Fix non-atomic status persistence observed during browser retry"
status: in_progress
priority: 1
type: bug
parent: OJ-a7l6
created_at: 2026-10-18T13:42:26Z
created_by: speed
updated_at: 2026-10-18T13:56:09Z
content_hash: "sha256:53354a9b2f6e0ffcd5f259b1d0eb9ae6a10621d196655e9bab40496587812e9e"
blocks: [OJ-yf2c]
assignee: dev-OJ-p8rd
follows: [OJ-inuo]
---

## Description
Observed during OJ-yf2c CUA on source 2b22504: real dry_run retry GET status returned HTTP500 JSONDecodeError line1col1 at app/main.py330. _set_status truncates status.json with write_text while status endpoint reads concurrently. UI safely locks duplicate run and Check status again recovers to COMPLETE. Scope: app/main.py persistence/read contract and deterministic concurrent-reader regression. AC: publish complete JSON atomically; readers never see partial JSON under bounded writer stress; preserve missing-job404 and job-state semantics; real local browser retry has no status500. No UI redesign, GPU, external API, or workflow changes. Requires bounded concurrency review before implementation. Evidence: docs/evidence/frontend-upgrade/browser/status-race-500.png and REPORT.md (capstone pending).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T13:55:48Z dep_added: blocks OJ-yf2c
- 2026-10-18T13:56:09Z status: open -> in_progress
- 2026-10-18T13:56:09Z auto-follows: linked to predecessor OJ-inuo
- 2026-10-18T13:56:09Z claimed by dev-OJ-p8rd

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]
- Follows: [[OJ-inuo]]

## Comments
