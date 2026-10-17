---
id: VK-e98k
title: "QWEN-03 concurrency knee: latency percentiles vs parallelism"
status: closed
priority: 1
type: feature
labels: [qwen-ambassador, contributions, accepted]
parent: VK-5cpt
created_at: 2026-10-03T23:09:00Z
created_by: speed
updated_at: 2026-10-03T23:17:57Z
content_hash: "sha256:31060a1f0eb170f2c54055ee3c3d55b18ab9ea021f94347bf7f34e69968264d4"
follows: [VK-bg91]
closed_at: 2026-10-03T23:17:57Z
close_reason: "4/4 remote artifacts verified: repo public, raw log fetched from raw.githubusercontent.com with non-zero usage tokens, receipts present."
---

## Description
Characterise the concurrency knee of the Qwen Ambassador route: latency
percentiles and error rate as parallel requests increase.

## Acceptance criteria
- Harness issues the same fixed prompt set at parallelism 1, 2, 4, 8.
- Raw logs record per-request latency, http_status and usage tokens.
- results/summary.json reports p50/p95 latency and error rate per level.
- README states where the knee appears and that this measures one endpoint at one
  time of day, not the service's capacity.
- receipts.sha256 covers harness + raw logs.

## Evidence
Pending run.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-10-03.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-03.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- repo: https://github.com/jmanhype/qwen-endpoint-concurrency (PUBLIC, `gh repo view` verified)
- harness: run.py, 4 levels x 8 requests = 32 real calls; py_compile + import smoke test pass
- raw log: results/raw.jsonl, 32 records, 32 with non-zero usage tokens
- remote check: fetched results/raw.jsonl from raw.githubusercontent.com -> 32 records, 32 with usage tokens
- measured result: 32/32 HTTP 200, 0% error rate at every level; p50 8.03 / 8.77 / 8.67 / 7.91 s
- results/raw.jsonl sha256 b33e178125bc9a839cf812af77a31ff8d8d2bf1194202f8f1191c466a3d54fc6

### proof
- [x] AC1 harness issues the fixed prompt set at parallelism 1, 2, 4, 8
- [x] AC2 raw logs record per-request latency, http_status and usage tokens (32/32)
- [x] AC3 summary.json reports p50/p95 latency and error rate per level
- [x] AC4 README states no knee was found in range and explicitly frames it as a
      negative result about the search range, not a capacity claim
- [x] AC5 receipts.sha256 covers harness, client, README and raw logs (5 entries)

## History
- 2026-10-03T23:17:57Z status: open -> in_progress
- 2026-10-03T23:17:57Z auto-follows: linked to predecessor VK-bg91
- 2026-10-03T23:17:57Z status: in_progress -> closed

## Links
- Parent: [[VK-5cpt]]
- Follows: [[VK-bg91]]

## Comments
