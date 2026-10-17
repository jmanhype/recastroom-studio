---
id: VK-1o9n
title: "QWEN-07 Qwen family Pareto eval: accuracy, cost, latency, fabrication"
status: closed
priority: 1
type: feature
labels: [qwen-ambassador, contributions, accepted]
parent: VK-5cpt
created_at: 2026-10-03T23:37:00Z
created_by: speed
updated_at: 2026-10-03T23:55:03Z
content_hash: "sha256:ab9453a27f64e2d876f1f5a635f53cd573ee926d11f52df4443de950dd67a849"
assignee: dev-VK-1o9n
follows: [VK-s9zz, VK-bg91]
closed_at: 2026-10-03T23:55:03Z
close_reason: "Remote-verified: 5 cloud tiers x 16 records all with non-zero usage tokens; local arm published with identical grader; Pareto computed; fail-closed failure characterised by budget-escalation probe."
led_to: [VK-dcay]
---

## Description
Publish the Qwen-family Pareto evaluation: accuracy, completion tokens, latency and
fail-closed (fabrication) behaviour for the five callable tiers on one fixed,
deterministically-graded task set.

Tiers: Qwen/Qwen3.8-27B, Qwen/Qwen3.5-35B-A3B, Qwen/Qwen3.5-122B-A10B,
Qwen/Qwen3.5-397B-A17B, Qwen-Ambassador/Qwen3.8-Max.

## Acceptance criteria
- Harness runs 16 tasks (12 objectively answerable, 4 that cannot be answered with
  certainty) against all five tiers and writes results/raw.jsonl.
- Every raw record carries http_status and non-zero usage token counts.
- results/summary.json reports per-tier accuracy, completion tokens, median latency,
  fabrication rate and the non-dominated Pareto set.
- README states the measured frontier, the fabrication finding, and the sample-size caveat.
- Public repo under jmanhype with receipts.sha256 covering harness, client, README, raw logs.
- Verified by fetching results/raw.jsonl from raw.githubusercontent.com: non-zero usage
  tokens present for all five tiers.

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
- repo: https://github.com/jmanhype/qwen-family-pareto (PUBLIC, `gh repo view` verified)
- cloud arm: run.py, 5 tiers x 16 tasks = 80 real calls; py_compile + import smoke test pass
- local arm: run_local.py, 16 real calls to llama-server (Qwen3.8-27B Q4_K_M) on the 3090
  over Tailscale, reusing the identical task set and grader
- remote check: fetched results/raw.jsonl from raw.githubusercontent.com ->
  80 records; every one of the 5 tiers has 16 records and non-zero completion tokens
  (Max 2653, 27B 3056, 35B-A3B 20912, 122B-A10B 15031, 397B-A17B 16397)
- remote check: results/raw_local.jsonl -> 16 records, 3320 completion tokens
- measured frontier: all six arms 12/12 on answerable tasks; only
  Qwen-Ambassador/Qwen3.8-Max is non-dominated (tied accuracy, fewest tokens)
- measured fail-closed: all 5 cloud tiers abstain 4/4; local arm abstains 3/4 and
  spirals (1500->1500 tokens, 4000->4000 tokens, no ANSWER line, 111s at the larger cap)
- results/final_summary.json sha256 recorded in receipts.sha256

### proof
- [x] AC1 harness runs 16 graded tasks across all five tiers and writes results/raw.jsonl (80 rows)
- [x] AC2 every raw record carries http_status and non-zero usage tokens (80/80 verified remotely)
- [x] AC3 summary reports per-tier accuracy, tokens, median latency, fabrication/abstention and the Pareto set
- [x] AC4 README states the measured frontier, the fail-closed failure, and sample-size caveats
- [x] AC5 public repo with receipts.sha256 covering harnesses, client, README and results (12 entries)
- [x] AC6 goal verification command `sh verify_pareto_remote.sh` returns
      "ALL FIVE TIERS HAVE NON-ZERO USAGE TOKENS: True"

## History
- 2026-10-03T23:37:00Z status: open -> in_progress
- 2026-10-03T23:37:00Z auto-follows: linked to predecessor VK-s9zz
- 2026-10-03T23:37:00Z claimed by dev-VK-1o9n
- 2026-10-03T23:55:02Z status: in_progress -> in_progress
- 2026-10-03T23:55:02Z auto-follows: linked to predecessor VK-bg91
- 2026-10-03T23:55:03Z status: in_progress -> closed

## Links
- Parent: [[VK-5cpt]]
- Follows: [[VK-s9zz]], [[VK-bg91]]
- Led to: [[VK-dcay]]

## Comments
