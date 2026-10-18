---
id: OJ-c1vo
title: "Fail closed when the legacy renderer is disconnected"
status: open
priority: 1
type: bug
parent: OJ-a7l6
created_at: 2026-10-18T14:53:03Z
created_by: speed
updated_at: 2026-10-18T15:04:15Z
content_hash: "sha256:b7dfc4e0f6aaf27a1b250d9f295b20052e4024ff09779457ff6e198ced212d34"
blocks: [OJ-yf2c]
follows: [OJ-p8rd]
---

## Description
# Block legacy runs when ComfyUI is unreachable

## USER INTENT
The owner approved a fix after job b358c5cfebdd failed against offline localhost8189 despite the studio health endpoint reporting ok. Keep the current design and prepared data; distinguish local app liveness from the configured legacy renderer connection.

## Scope and boundary
Base epic/OJ-a7l6 commit7881cb0, current accepted preview. Own app/main.py, app/web/studio.js, optional minimal app/web/index.html wording, a narrow new src/openjutsu/readiness.py if useful, NEW tests/test_backend_readiness.py, docs/evidence/backend-readiness/. No other edits. No models, workflow/media alterations, package changes, GPU, credentials, external calls, publication, commits/merges by the worker, or process changes on8893. Parent handles real Colab reconnection and browser QA separately. Existing SDK execution semantics remain unchanged; no unsupported claims of SDK reachability. Preserve dry_run.

CONSUMES:
- app/main.py health() -> GET /api/health currently ok/workflow/workflow_exists/backend, all existing fields retained; ok remains local app liveness.
- run_job(job_id, background_tasks) -> POST /api/jobs/{job_id}/run checks job and duplicate state, queues a runner. Guard legacy submission BEFORE status mutation or background task when renderer unavailable.
- src/openjutsu/config.py Settings.comfy_url (trusted configured URL); no UI/user-supplied URL feature.
- app/web/studio.js checkHealth(), controls(), run event: use actual health readiness with recheck/recovery; preserve job inputs and consent.
PRODUCES:
- explicit additive legacy connection state with safe actionable text, fail-closed Run button and HTTP503 guard; local preparation can still proceed offline.

## Acceptance Criteria
1. GET health retains existing contract and adds renderer readiness. For legacy, use a side-effect-free HTTP GET /system_stats with short connect/read timeouts, no retries, no redirect-following, plausible Comfy schema validation (system object/devices list). Failure/refusal/timeout/HTTPerror/malformed/schema mismatch returns not ready with sanitized actionable code/message; never return raw credential-bearing URL/exception. Successful connection only establishes reachability, not model availability, GPU spend, QC, or successful generation. Dry_run remains explicitly local/noAI. SDK remains explicitly unchecked, not falsely marked verified, and preserves existing behavior.
2. The legacy run endpoint independently rechecks and returns503 when disconnected BEFORE queue/status/upload/submission. Existing job files/status preserved; missing jobs404 and active jobs409 preserved. No rendering POST in health. Recovery requires a successful fresh check; no stale success reliance. Existing dry_run and SDK behavior unchanged.
3. UI for legacy disables Run until verified reachable, shows Renderer disconnected/connection checking with a visible Check connection again button, allows safe prepare, and preserves prepared job/files/rights on reconnection. A fresh check before submitting plus server guard handles post-load disconnects; an unavailable503 must not falsely show queued/running or wipe prepared state. Existing duplicate prevention, status error recovery, and honest cost/location warning stay intact.
4. New tests pin offline refusal, timeout, malformed/nonComfy/HTTPerror responses, recovery, no queue or status mutation when disconnected, invalid/missing404 and active409, plus dry_run preservation. Use actual TestClient and a clearly labelled loopback HTTP protocol fixture for transport tests; unit mocks permitted only for bounded failure branches, not misrepresented as live Comfy. No existing test weakened/changed, no skipped tests. Full suite passes twice; disclose existing Starlette/httpx warning.
5. Parent browser QA must show disconnected Run disabled and successful check/recovery with no AI generation. Worker supplies sanitized report, exact commands/results and hashed evidence; no tokens or absolute private paths in checked-in text.

Testing: PYTHONPATH=src <root>/.venv/bin/python -m pytest -q; root=/Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio. Existing baseline48 tests on epic (capstone4 extra stay on its own branch). Parent verifies diff, commits locally after evidence, independent PM accepts; worker reports uncommitted patch only.

## nd_contract
status: new
### evidence
- Parent verified legacy connection refused at8189 and unconditional health ok at8893; user agrees to correction.
### proof
- [ ] AC1-5 implementation, transport/API tests and browser evidence.

## Acceptance Criteria


## Design


## Notes
Research-first checkpoint, 2026-10-18:
Owner answered the fresh-G4 decision with 'do research on how this should go'. No GPU allocated and no new render. colab status/usage returned no active sessions, 58.65 CU, 0.00/hr, zero assignments. Parent researched official Colab restrictions/lifecycle and Comfy custom API deployments/SDK v2. Research artifact: /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/frontend-evidence/readiness-20261018/RESEARCH.md; SHA256 293852cd5f754530142f1670579023cdcf2ce171af980f05d01dccdc4c95abaf.
Recommended next architectural evaluation: versioned exact-workflow Comfy API deployment, min0/max1, durable asset uploads/provider-job recovery/result storage, subject to provider policy, hardware compatibility and cost approval. Colab FAQ includes a creating-deepfakes restriction for all managed runtimes; no consensual-recasting exception was established. Do not automatically start a Colab recasting runtime from this story.
Worker /root/renderer_ready_c1vo was stopped at the research-first boundary. Story checkout verified clean at base7881cb0; no implementation edits or deployment. Worker reported baseline48 tests with the existing warning; this checkpoint does not promote that report to implementation proof. Live8893 remains unchanged and still lacks the renderer Run guard. Prior app/video outputs preserved.

## nd_contract
status: new
### evidence
- Official-source research saved with the SHA256 above; no spend.
- Parent git status --porcelain verified no story edits; child interrupted; story claim released for later continuation.
- bd sync --from-main reports no Beads database; canonical shared pvg nd vault retained, no competing tracker initialized.
### proof
- [ ] AC1-5 remain unimplemented/unaccepted; no readiness fix or production migration claimed.


## History
- 2026-10-18T14:53:03Z dep_added: blocks OJ-yf2c
- 2026-10-18T14:53:04Z status: open -> in_progress
- 2026-10-18T14:53:04Z auto-follows: linked to predecessor OJ-p8rd
- 2026-10-18T14:53:04Z claimed by dev-OJ-c1vo
- 2026-10-18T15:04:15Z status: in_progress -> open
- 2026-10-18T15:04:15Z released by speed

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]
- Follows: [[OJ-p8rd]]

## Comments
