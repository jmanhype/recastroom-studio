---
id: VK-s9zz
title: "QWEN-04 reproducible ambassador client + verified auth receipts"
status: closed
priority: 1
type: feature
labels: [qwen-ambassador, contributions, accepted]
parent: VK-5cpt
created_at: 2026-10-03T23:09:00Z
created_by: speed
updated_at: 2026-10-03T23:17:58Z
content_hash: "sha256:10f6cac7c16f67e9418b130d37f2812dc37e5c38e174e80633f9e7bff7f52521"
follows: [VK-bg91]
closed_at: 2026-10-03T23:17:58Z
close_reason: "4/4 remote artifacts verified: repo public, raw log fetched from raw.githubusercontent.com with non-zero usage tokens, receipts present."
led_to: [VK-1o9n, VK-dcay]
---

## Description
Publish a reproducible client + verified endpoint receipt for the Qwen
Ambassador ModelScope route, including the auth gotchas found while building.

## Acceptance criteria
- Client pins base URL and model id; credential read from env or secret file, never logged.
- A verification script proves which endpoints are public vs auth-gated, with raw HTTP codes.
- Findings include: GET /v1/models is unauthenticated; POST /v1/chat/completions requires a
  valid token; the correct host for this route is api-inference.modelscope.ai.
- README documents the client and the gotchas.
- receipts.sha256 covers scripts + captured evidence logs.

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
- repo: https://github.com/jmanhype/qwen-modelscope-endpoint-receipts (PUBLIC, `gh repo view` verified)
- harness: verify.py, 5 HTTP probes; py_compile + import smoke test pass
- evidence: evidence/auth_probes.json + evidence/findings.json
- remote check: fetched evidence/auth_probes.json from raw.githubusercontent.com -> 5 probes present
- measured result: GET /v1/models = 200 with NO token and with a bogus token;
  POST /v1/chat/completions = 401 with bogus, 200 with real on .ai, 401 with real on .cn
- evidence/auth_probes.json sha256 34d7e206cec03e744c2d122646bbb3384eb76defb1c2979b6f1a876f1b0c9ef9

### proof
- [x] AC1 client pins base URL and model id; credential read from env or secret file, never logged
- [x] AC2 verification script proves public vs auth-gated endpoints with raw HTTP codes
- [x] AC3 findings include models-listing-is-public, chat-requires-valid-token, and the .ai/.cn host split
- [x] AC4 README documents the client and the gotchas
- [x] AC5 receipts.sha256 covers scripts, README and evidence (5 entries)
- [x] AC6 secret scan: no credential bytes present in any published file (only the deliberate bogus control token)

## History
- 2026-10-03T23:17:57Z status: open -> in_progress
- 2026-10-03T23:17:57Z auto-follows: linked to predecessor VK-bg91
- 2026-10-03T23:17:58Z status: in_progress -> closed

## Links
- Parent: [[VK-5cpt]]
- Follows: [[VK-bg91]]
- Led to: [[VK-1o9n]], [[VK-dcay]]

## Comments
