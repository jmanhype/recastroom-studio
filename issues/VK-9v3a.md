---
id: VK-9v3a
title: "QWEN-01 effort curve: reasoning cost vs accuracy for Qwen3.8-Max"
status: closed
priority: 1
type: feature
labels: [qwen-ambassador, contributions, accepted]
parent: VK-5cpt
created_at: 2026-10-03T23:09:00Z
created_by: speed
updated_at: 2026-10-03T23:17:57Z
content_hash: "sha256:8430a3a8c1c6674801898deab103178e109bd1bc6dd5a888a370a65e88234950"
closed_at: 2026-10-03T23:17:56Z
close_reason: "4/4 remote artifacts verified: repo public, raw log fetched from raw.githubusercontent.com with non-zero usage tokens, receipts present."
led_to: [VK-bg91]
---

## Description
Measure how reasoning effort changes cost and accuracy for Qwen3.8-Max on a
fixed short-answer task set.

## Acceptance criteria
- Harness runs N tasks across efforts low/medium/high/xhigh and writes raw.jsonl.
- Every raw record contains http_status, latency_s and non-zero usage token counts.
- results/summary.json reports per-effort accuracy, mean completion tokens, median latency.
- README states the finding honestly, including that an 8-task set is too easy to
  discriminate accuracy and that the result is a cost/latency characterisation.
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
- repo: https://github.com/jmanhype/qwen3-max-effort-curve (PUBLIC, `gh repo view` verified)
- harness: run.py, 32 real calls to Qwen-Ambassador/Qwen3.8-Max; py_compile + import smoke test pass
- raw log: results/raw.jsonl, 32 records, 32 with non-zero prompt+completion tokens
- remote check: fetched results/raw.jsonl from raw.githubusercontent.com -> 32 records, 32 with usage tokens
- results/summary.json sha256 bf3e9399ba5b526291e130541d1852bf7b3efa22598599939760464bab70e17b
- results/raw.jsonl   sha256 a938600a94491981d4e3296675dc9ff705ecc0fc0a7e95ad26445f284efd6cd5

### proof
- [x] AC1 harness runs tasks across low/medium/high/xhigh and writes raw.jsonl (32 rows present)
- [x] AC2 every record carries http_status, latency_s and non-zero usage tokens (32/32)
- [x] AC3 summary.json reports per-effort accuracy, mean completion tokens, median latency
- [x] AC4 README states the finding honestly (1.000 accuracy at all efforts; 84.6 -> 132.4 token spread)
      and states the 8-task set cannot discriminate accuracy
- [x] AC5 receipts.sha256 covers harness, client, README and raw logs (5 entries)

## History
- 2026-10-03T23:17:56Z status: open -> in_progress
- 2026-10-03T23:17:56Z status: in_progress -> closed

## Links
- Parent: [[VK-5cpt]]
- Led to: [[VK-bg91]]

## Comments
