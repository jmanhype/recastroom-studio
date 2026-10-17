---
id: VK-bg91
title: "QWEN-02 fail-closed structured critic contract"
status: closed
priority: 1
type: feature
labels: [qwen-ambassador, contributions, accepted]
parent: VK-5cpt
created_at: 2026-10-03T23:09:00Z
created_by: speed
updated_at: 2026-10-03T23:17:57Z
content_hash: "sha256:49e4741b04f954ecda05f52e59594a44f331e62425bd0339c6c87d5be87d3311"
follows: [VK-9v3a]
closed_at: 2026-10-03T23:17:57Z
close_reason: "4/4 remote artifacts verified: repo public, raw log fetched from raw.githubusercontent.com with non-zero usage tokens, receipts present."
led_to: [VK-e98k, VK-s9zz, VK-1o9n]
---

## Description
Ship a fail-closed structured critic contract for Qwen3.8-Max: a judge that is
allowed to say "I don't know" instead of inventing a score.

## Acceptance criteria
- Harness sends adversarial judge inputs (hedged, truncated, off-schema, valid).
- Parser returns parse_ok=false when no numeric score is present; never fabricates one.
- Raw logs preserve every model response verbatim with usage tokens.
- results/summary.json reports parse_ok rate per input class.
- README states the contract and the honest limitation (prompt-level enforcement only).
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
- repo: https://github.com/jmanhype/qwen-fail-closed-judge (PUBLIC, `gh repo view` verified)
- harness: run.py, 2 protocols x 5 cases = 10 real calls; py_compile + import smoke test pass
- raw log: results/raw.jsonl, 10 records, 10 with non-zero usage tokens
- remote check: fetched results/raw.jsonl from raw.githubusercontent.com -> 10 records, 10 with usage tokens
- measured result: implicit protocol leaked once (hedge_no_number emitted "SCORE: 0");
  explicit_escape protocol leaked 0 times and used the declared NO_SCORE path twice
- results/raw.jsonl sha256 b740211295b23af0cfa8fc531189eb436b0745b8d42b42854e7d0321e22f3a61

### proof
- [x] AC1 harness sends adversarial judge inputs (clear pass, clear fail, hedge, prose-only, truncated)
- [x] AC2 parser returns parse_ok=false when no score is present; fabricated_scores=0 by construction
- [x] AC3 raw logs preserve every model response verbatim plus usage tokens (10/10)
- [x] AC4 summary.json reports leak/abstention counts per protocol
- [x] AC5 README states the contract, the measured leak, and the prompt-level-only limitation
- [x] AC6 receipts.sha256 covers harness, client, README and raw logs (5 entries)

## History
- 2026-10-03T23:17:57Z status: open -> in_progress
- 2026-10-03T23:17:57Z auto-follows: linked to predecessor VK-9v3a
- 2026-10-03T23:17:57Z status: in_progress -> closed

## Links
- Parent: [[VK-5cpt]]
- Follows: [[VK-9v3a]]
- Led to: [[VK-e98k]], [[VK-s9zz]], [[VK-1o9n]]

## Comments
