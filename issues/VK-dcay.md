---
id: VK-dcay
title: "QWEN-08 agent-diff: tracer + divergence engine for local vs cloud agent runs"
status: closed
priority: 1
type: feature
labels: [qwen-ambassador, contributions, accepted]
parent: VK-5cpt
created_at: 2026-10-04T00:31:36Z
created_by: speed
updated_at: 2026-10-04T00:47:27Z
content_hash: "sha256:b750b55811c6fee6306080701a5d5a402a4ccd8605c60a03473adac1f1b2fc42"
assignee: dev-VK-dcay
follows: [VK-1o9n, VK-s9zz]
closed_at: 2026-10-04T00:47:27Z
close_reason: "Remote-verified 5 diff reports across 3 classes with refusal localisation; clean-checkout re-run reproduced all three classes. Includes honest record of the false 'auth flap' diagnosis disproven by probe_ab/probe_flap."
led_to: [VK-ic1j]
---

## Description
Ship `agent-diff`: a tracer + divergence engine that records two runs of the same
task against any OpenAI-compatible endpoint and reports the exact points where they
diverge in completion tokens, latency and refusal outcome.

Motivation: the current local-agent pain is not accuracy, it is opaque divergence —
one setup burns 8x the tokens, or fails to abstain, and nobody can point at where it
went wrong. This makes that divergence a first-class, diffable artifact.

## Acceptance criteria
- tracer.py streams from any OpenAI-compatible endpoint and records a per-token
  timeline (index, relative time, delta text) plus token counts, latency,
  finish_reason and refusal signal.
- diff.py consumes two traces and emits a machine-readable report naming the class,
  the token/latency deltas, and the first divergent token index.
- run_demo.py produces at least 4 diff reports spanning three classes:
  equal outcome with >=2x token delta, equal outcome with near-equal cost, and a
  divergent refusal outcome localising the local-spiral-vs-cloud-abstention failure.
- Both a local llama-server endpoint and the ModelScope cloud route appear in the traces.
- Public repo under jmanhype with receipts.sha256 and a README.
- Verified by re-running the end-to-end command from a clean checkout and by
  remote-fetching the committed diff reports from raw.githubusercontent.com.

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
- repo: https://github.com/jmanhype/agent-diff (PUBLIC, `gh repo view` verified)
- tracer.py: streams any OpenAI-compatible endpoint, records per-event timeline
  (index, elapsed, kind, delta text) plus completion/prompt tokens, latency,
  finish_reason, emitted_answer_line and answer_index. Exercised against BOTH
  local-3090-q4km and cloud-qwen38-max.
- diff.py: machine-readable report with class, token ratio, latency delta,
  first divergent stream index and a refusal_localisation block.
- 5 committed diff reports spanning all three required classes:
  * equal_outcome_cost_divergence: 35B-A3B vs Max (13.4x), 122B-A10B vs 27B (14.5x)
  * equal_outcome_parity: local Q4_K_M vs Max (1.16x)
  * divergent_refusal: local Q4_K_M 1500 tok / 43.7 s / no ANSWER / finish=length
    vs Max 129 tok / 4.6 s / abstained / ANSWER at stream event 38
- refusal localisation block present and correct on that report
  (`resolved_answer_index: 38`, `stalled_finish_reason: "length"`)

### verification
- remote fetch: all five `diffs/*.json` fetched from raw.githubusercontent.com;
  all three classes present; refusal diff localised = True
- clean checkout: `git clone` to a fresh dir + `python3 run_demo.py` against the live
  endpoints produced 5 pairs, 4 matches, all three expected classes present, and the
  refusal pair still classified divergent_refusal
- honest variance note: the `refusal-parity-local-vs-max-grains` pair classified as
  `equal_outcome_cost_divergence` (2.30x) in the committed run and
  `equal_outcome_mild_divergence` (1.44x) in the clean re-run. Classifications are
  deterministic given traces; the traces themselves vary between runs.

### bug found and fixed in this repo
- first demo run returned `401 Authentication failed` on every cloud call. Cause was a
  bug in tracer.py: `"api_key": _ms_key` (function object) instead of `_ms_key()`, so
  the header became `Bearer <function _ms_key at 0x...>`.
- an initial diagnosis of "intermittent auth flap" was DISPROVEN by probe_ab.py and
  probe_flap.py (all variants 401 while curl and the working client returned 200 in the
  same minute). Both probes are committed as the record of eliminating that answer.
- fix: `resolve_key()` accepts a literal or a zero-arg callable; bounded retry retained
  for genuinely transient failures.

### proof
- [x] AC1 tracer records per-token/per-event timeline + token, latency and refusal signals
- [x] AC2 diff engine emits machine-readable report with class, deltas and first divergent index
- [x] AC3 >=4 committed diff reports spanning the three required classes (5 reports, 3 classes)
- [x] AC4 both the local llama-server endpoint and the ModelScope cloud route appear in traces
- [x] AC5 public repo under jmanhype with receipts.sha256 and a README
- [x] AC6 verified by clean-checkout re-run AND remote fetch of the committed diffs

## History
- 2026-10-04T00:31:37Z status: open -> in_progress
- 2026-10-04T00:31:37Z auto-follows: linked to predecessor VK-1o9n
- 2026-10-04T00:31:37Z claimed by dev-VK-dcay
- 2026-10-04T00:47:27Z status: in_progress -> in_progress
- 2026-10-04T00:47:27Z auto-follows: linked to predecessor VK-s9zz
- 2026-10-04T00:47:27Z status: in_progress -> closed

## Links
- Parent: [[VK-5cpt]]
- Follows: [[VK-1o9n]], [[VK-s9zz]]
- Led to: [[VK-ic1j]]

## Comments
