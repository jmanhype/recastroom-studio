---
id: OJ-c1vo
title: "Fail closed when the legacy renderer is disconnected"
status: closed
priority: 1
type: bug
parent: OJ-a7l6
created_at: 2026-10-18T14:53:03Z
created_by: speed
updated_at: 2026-10-18T15:47:09Z
content_hash: "sha256:639b5a5d2610d426643c01b8d03a50df34a5319250caa3a7e4c500a70035c24f"
follows: [OJ-p8rd, OJ-inuo, OJ-xtk4]
assignee: dev-OJ-c1vo
labels: [accepted]
closed_at: 2026-10-18T15:47:09Z
close_reason: "Accepted: independently verified focused tests, hashes, browser receipts, source behavior, and all five ACs; sole pvg bare-pass finding is a documented false positive."
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
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-10-18.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence
Summary: Fail-closed legacy renderer readiness implemented and locally verified.
Commit SHA: 98de3ff703f584755d38c01cb6bb66fc997f0707
Branch: story/OJ-c1vo

### CI/Test Results
PROOF:
Commands run:
- <root>/.venv/bin/python -m pytest -q (twice independently): 63 passed, 1 existing warning both runs; no skips.
- node --check app/web/studio.js: passed.
- git diff --check: passed.
- shasum -a 256 -c docs/evidence/backend-readiness/HASHES.sha256: all OK.
- Browser QA actual CUA interactions: see committed BROWSER_QA.md and browser/receipt.json.
Coverage percentage: not measured; no coverage claim.

### AC Verification
| AC | Verification | Result |
| --- | --- | --- |
| 1 | TestClient real HTTP failures/recovery and sanitized response tests | PASS |
| 2 | Fresh run guard, no status mutation, 404/409, dry_run/SDK tests | PASS |
| 3 | Browser offline/recovery/offline sequence and preserved consent/files | PASS |
| 4 | 63 tests twice; original tests unchanged; warning disclosed | PASS |
| 5 | Parent screenshots, receipt and test logs with SHA256 files | PASS |

Structural verifier observation: pvg verify reports tests/test_backend_readiness.py:118 bare pass as a stub. This is a no-op cleanup finally in a contextmanager after the socket is already closed, not missing implementation. Request independent PM review of that false-positive; do not silently bypass it or claim the command passed.

LEARNINGS:
- Local health is not renderer readiness; preparation can remain available offline.
- A post-submit 503 is not inherently proof that nothing was submitted; retain unknown-state protection except for the explicit local legacy guard.
- Paivot append-notes inserts before legacy top-level contract headings in this issue. This same evidence is mirrored as an append-only comment so the final contract is authoritative without deleting history.

## nd_contract
status: delivered

### evidence
- Local story commit 98de3ff on story/OJ-c1vo, base 7881cb0. No push.
- Worker full pytest twice: 63 passed, 1 existing Starlette/httpx warning.
- Independent parent full pytest twice: 63 passed, 1 warning (77.02s, 337.84s); node syntax and git diff checks passed.
- Parent verified worker HASHES.sha256; browser receipt and screenshots in docs/evidence/backend-readiness/browser; BROWSER_QA.md describes precise limits.
- Real browser + local ASGI app + labelled no-GPU HTTP fixture: offline prepare succeeds/Run blocked, recovery enables Run preserving job/consent, disconnect before click blocks with no run POST. Exactly 3 fixture GETs, zero fixture POSTs, zero app run POSTs; workflow survives/no queued status file.
- Existing test files, media/workflow, dependencies and live8893 unchanged pending acceptance/restart. No GPU or paid API spend.
- bd sync --from-main unavailable because no Beads database; canonical pvg nd retained.

### proof
- [x] AC #1: bounded read-only renderer readiness with sanitized errors, truthful dry_run/unchecked SDK semantics.
- [x] AC #2: independent legacy run guard before mutation, 404/409 preserved; real HTTP TestClient tests pass.
- [x] AC #3: offline Run gating, recoverable prepared state, fresh pre-submit check, unknown-submission safety reviewed.
- [x] AC #4: new 15-case readiness suite; existing 48 tests unchanged; full suite passes twice independently.
- [x] AC #5: parent browser QA without AI, sanitized reports, hashed screenshots/requests/test logs committed.


## Implementation Evidence
Summary: Fail-closed legacy renderer readiness implemented and locally verified.
Commit: 98de3ff703f584755d38c01cb6bb66fc997f0707
Branch: story/OJ-c1vo

### CI/Test Results
PROOF:
Commands run:
- <root>/.venv/bin/python -m pytest -q (twice independently): 63 passed, 1 existing warning both runs; no skips.
- node --check app/web/studio.js: passed.
- git diff --check: passed.
- shasum -a 256 -c docs/evidence/backend-readiness/HASHES.sha256: all OK.
- Browser QA actual CUA interactions: see committed BROWSER_QA.md and browser/receipt.json.
Coverage percentage: not measured; no coverage claim.

LEARNINGS:
- Local health is not renderer readiness; preparation can remain available offline.
- A post-submit 503 is not inherently proof that nothing was submitted; retain unknown-state protection except for the explicit local legacy guard.
- Paivot append-notes inserts before legacy top-level contract headings in this issue. This same evidence is mirrored as an append-only comment so the final contract is authoritative without deleting history.

## nd_contract
status: delivered

### evidence
- Local story commit 98de3ff on story/OJ-c1vo, base 7881cb0. No push.
- Worker full pytest twice: 63 passed, 1 existing Starlette/httpx warning.
- Independent parent full pytest twice: 63 passed, 1 warning (77.02s, 337.84s); node syntax and git diff checks passed.
- Parent verified worker HASHES.sha256; browser receipt and screenshots in docs/evidence/backend-readiness/browser; BROWSER_QA.md describes precise limits.
- Real browser + local ASGI app + labelled no-GPU HTTP fixture: offline prepare succeeds/Run blocked, recovery enables Run preserving job/consent, disconnect before click blocks with no run POST. Exactly 3 fixture GETs, zero fixture POSTs, zero app run POSTs; workflow survives/no queued status file.
- Existing test files, media/workflow, dependencies and live8893 unchanged pending acceptance/restart. No GPU or paid API spend.
- bd sync --from-main unavailable because no Beads database; canonical pvg nd retained.

### proof
- [x] AC #1: bounded read-only renderer readiness with sanitized errors, truthful dry_run/unchecked SDK semantics.
- [x] AC #2: independent legacy run guard before mutation, 404/409 preserved; real HTTP TestClient tests pass.
- [x] AC #3: offline Run gating, recoverable prepared state, fresh pre-submit check, unknown-submission safety reviewed.
- [x] AC #4: new 15-case readiness suite; existing 48 tests unchanged; full suite passes twice independently.
- [x] AC #5: parent browser QA without AI, sanitized reports, hashed screenshots/requests/test logs committed.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Local story commit 98de3ff on story/OJ-c1vo, base 7881cb0. No push.
- Worker full pytest twice: 63 passed, 1 existing Starlette/httpx warning.
- Independent parent full pytest twice: 63 passed, 1 warning (77.02s, 337.84s); node syntax and git diff checks passed.
- Parent verified worker HASHES.sha256; browser receipt and screenshots in docs/evidence/backend-readiness/browser; BROWSER_QA.md describes precise limits.
- Real browser + local ASGI app + labelled no-GPU HTTP fixture: offline prepare succeeds/Run blocked, recovery enables Run preserving job/consent, disconnect before click blocks with no run POST. Exactly 3 fixture GETs, zero fixture POSTs, zero app run POSTs; workflow survives/no queued status file.
- Existing test files, media/workflow, dependencies and live8893 unchanged pending acceptance/restart. No GPU or paid API spend.
- bd sync --from-main unavailable because no Beads database; canonical pvg nd retained.

### proof
- [x] AC #1: bounded read-only renderer readiness with sanitized errors, truthful dry_run/unchecked SDK semantics.
- [x] AC #2: independent legacy run guard before mutation, 404/409 preserved; real HTTP TestClient tests pass.
- [x] AC #3: offline Run gating, recoverable prepared state, fresh pre-submit check, unknown-submission safety reviewed.
- [x] AC #4: new 15-case readiness suite; existing 48 tests unchanged; full suite passes twice independently.
- [x] AC #5: parent browser QA without AI, sanitized reports, hashed screenshots/requests/test logs committed.


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
- 2026-10-18T15:08:17Z status: open -> in_progress
- 2026-10-18T15:08:17Z auto-follows: linked to predecessor OJ-inuo
- 2026-10-18T15:08:17Z claimed by dev-OJ-c1vo
- 2026-10-18T15:40:55Z status: in_progress -> in_progress
- 2026-10-18T15:40:55Z auto-follows: linked to predecessor OJ-xtk4
- 2026-10-18T15:47:09Z status: in_progress -> closed
- 2026-10-18T15:47:09Z dep_removed: no_longer_blocks OJ-yf2c

## Links
- Parent: [[OJ-a7l6]]
- Follows: [[OJ-p8rd]], [[OJ-inuo]], [[OJ-xtk4]]

## Comments

### 2026-10-18T15:41:42Z speed
## Implementation Evidence
Summary: Fail-closed legacy renderer readiness implemented and locally verified.
Commit: 98de3ff703f584755d38c01cb6bb66fc997f0707
Branch: story/OJ-c1vo

### CI/Test Results
PROOF:
Commands run:
- <root>/.venv/bin/python -m pytest -q (twice independently): 63 passed, 1 existing warning both runs; no skips.
- node --check app/web/studio.js: passed.
- git diff --check: passed.
- shasum -a 256 -c docs/evidence/backend-readiness/HASHES.sha256: all OK.
- Browser QA actual CUA interactions: see committed BROWSER_QA.md and browser/receipt.json.
Coverage percentage: not measured; no coverage claim.

LEARNINGS:
- Local health is not renderer readiness; preparation can remain available offline.
- A post-submit 503 is not inherently proof that nothing was submitted; retain unknown-state protection except for the explicit local legacy guard.
- Paivot append-notes inserts before legacy top-level contract headings in this issue. This same evidence is mirrored as an append-only comment so the final contract is authoritative without deleting history.

## nd_contract
status: delivered

### evidence
- Local story commit 98de3ff on story/OJ-c1vo, base 7881cb0. No push.
- Worker full pytest twice: 63 passed, 1 existing Starlette/httpx warning.
- Independent parent full pytest twice: 63 passed, 1 warning (77.02s, 337.84s); node syntax and git diff checks passed.
- Parent verified worker HASHES.sha256; browser receipt and screenshots in docs/evidence/backend-readiness/browser; BROWSER_QA.md describes precise limits.
- Real browser + local ASGI app + labelled no-GPU HTTP fixture: offline prepare succeeds/Run blocked, recovery enables Run preserving job/consent, disconnect before click blocks with no run POST. Exactly 3 fixture GETs, zero fixture POSTs, zero app run POSTs; workflow survives/no queued status file.
- Existing test files, media/workflow, dependencies and live8893 unchanged pending acceptance/restart. No GPU or paid API spend.
- bd sync --from-main unavailable because no Beads database; canonical pvg nd retained.

### proof
- [x] AC #1: bounded read-only renderer readiness with sanitized errors, truthful dry_run/unchecked SDK semantics.
- [x] AC #2: independent legacy run guard before mutation, 404/409 preserved; real HTTP TestClient tests pass.
- [x] AC #3: offline Run gating, recoverable prepared state, fresh pre-submit check, unknown-submission safety reviewed.
- [x] AC #4: new 15-case readiness suite; existing 48 tests unchanged; full suite passes twice independently.
- [x] AC #5: parent browser QA without AI, sanitized reports, hashed screenshots/requests/test logs committed.


### 2026-10-18T15:42:20Z speed
## Implementation Evidence
Summary: Fail-closed legacy renderer readiness implemented and locally verified.
Commit SHA: 98de3ff703f584755d38c01cb6bb66fc997f0707
Branch: story/OJ-c1vo

### CI/Test Results
PROOF:
Commands run:
- <root>/.venv/bin/python -m pytest -q (twice independently): 63 passed, 1 existing warning both runs; no skips.
- node --check app/web/studio.js: passed.
- git diff --check: passed.
- shasum -a 256 -c docs/evidence/backend-readiness/HASHES.sha256: all OK.
- Browser QA actual CUA interactions: see committed BROWSER_QA.md and browser/receipt.json.
Coverage percentage: not measured; no coverage claim.

### AC Verification
| AC | Verification | Result |
| --- | --- | --- |
| 1 | TestClient real HTTP failures/recovery and sanitized response tests | PASS |
| 2 | Fresh run guard, no status mutation, 404/409, dry_run/SDK tests | PASS |
| 3 | Browser offline/recovery/offline sequence and preserved consent/files | PASS |
| 4 | 63 tests twice; original tests unchanged; warning disclosed | PASS |
| 5 | Parent screenshots, receipt and test logs with SHA256 files | PASS |

Structural verifier observation: pvg verify reports tests/test_backend_readiness.py:118 bare pass as a stub. This is a no-op cleanup finally in a contextmanager after the socket is already closed, not missing implementation. Request independent PM review of that false-positive; do not silently bypass it or claim the command passed.

LEARNINGS:
- Local health is not renderer readiness; preparation can remain available offline.
- A post-submit 503 is not inherently proof that nothing was submitted; retain unknown-state protection except for the explicit local legacy guard.
- Paivot append-notes inserts before legacy top-level contract headings in this issue. This same evidence is mirrored as an append-only comment so the final contract is authoritative without deleting history.

## nd_contract
status: delivered

### evidence
- Local story commit 98de3ff on story/OJ-c1vo, base 7881cb0. No push.
- Worker full pytest twice: 63 passed, 1 existing Starlette/httpx warning.
- Independent parent full pytest twice: 63 passed, 1 warning (77.02s, 337.84s); node syntax and git diff checks passed.
- Parent verified worker HASHES.sha256; browser receipt and screenshots in docs/evidence/backend-readiness/browser; BROWSER_QA.md describes precise limits.
- Real browser + local ASGI app + labelled no-GPU HTTP fixture: offline prepare succeeds/Run blocked, recovery enables Run preserving job/consent, disconnect before click blocks with no run POST. Exactly 3 fixture GETs, zero fixture POSTs, zero app run POSTs; workflow survives/no queued status file.
- Existing test files, media/workflow, dependencies and live8893 unchanged pending acceptance/restart. No GPU or paid API spend.
- bd sync --from-main unavailable because no Beads database; canonical pvg nd retained.

### proof
- [x] AC #1: bounded read-only renderer readiness with sanitized errors, truthful dry_run/unchecked SDK semantics.
- [x] AC #2: independent legacy run guard before mutation, 404/409 preserved; real HTTP TestClient tests pass.
- [x] AC #3: offline Run gating, recoverable prepared state, fresh pre-submit check, unknown-submission safety reviewed.
- [x] AC #4: new 15-case readiness suite; existing 48 tests unchanged; full suite passes twice independently.
- [x] AC #5: parent browser QA without AI, sanitized reports, hashed screenshots/requests/test logs committed.


### 2026-10-18T15:47:09Z speed
## PM Decision
ACCEPTED [2026-10-18]: Independent evidence-based review meets all five story ACs.

### Independent PM evidence
- Reviewed story worktree at commit `98de3ff703f584755d38c01cb6bb66fc997f0707` against base `7881cb0762ef53556995f036166bb6a85c95a899`; worktree remained clean. The changed path set is confined to the story-owned app/UI/readiness/test/evidence scope, and `tests/test_backend_readiness.py` is the only test path changed.
- Independently ran `PYTHONPATH=src <root>/.venv/bin/python -m pytest -q tests/test_backend_readiness.py`: **15 passed, 1 existing Starlette/httpx warning in 5.61s** (no skips/failures). This corroborates the worker focused log and the independently recorded two full-suite 63-pass logs.
- Verified all 8 records in `docs/evidence/backend-readiness/HASHES.sha256` and all 6 records in `docs/evidence/backend-readiness/browser/SHA256SUMS`: every file `OK`. Independently ran `node --check app/web/studio.js` and the base-to-HEAD `git diff --check`: both exited 0.
- Read the browser report/receipt and inspected the three hashed screenshots: disconnected prepare leaves Run unavailable; fresh loopback success enables Run while preserving the same job/consent; a final fresh failed check shows `RUN BLOCKED`, preserves prepared files/permissions, and exposes connection retry. Receipt records exactly 3 fixture GETs, 0 fixture generation/upload POSTs, 0 app run POSTs, and no `status.json`.
- Source review confirms health is additive/read-only, legacy uses bounded no-retry/no-redirect `GET /system_stats` with schema and sanitized failure handling; run independently guards before queued status/background submission; 404/409 and dry-run/SDK semantics remain separate; UI performs a fresh check and distinguishes a proven pre-submit/structured guard from unknown post-submit failures.

### Structural verifier finding
`pvg verify app/main.py app/web/studio.js src/openjutsu/readiness.py tests/test_backend_readiness.py` genuinely exited FAILED with its sole finding: `tests/test_backend_readiness.py:118 [stub] bare pass statement`. This is explicitly a verifier false positive, not a claimed pass. In `closed_loopback_url` (lines 109-118), the socket is bound only to reserve an ephemeral port, the port is captured, and `server.close()` runs before `yield`; the `finally: pass` owns no open resource and is a redundant no-op. The surrounding offline-refusal test exercises the URL and passed. No test cleanup/edit is authorized for acceptance.

### AC proof
- [x] AC #1: additive health readiness with safe bounded Comfy protocol checks and truthful dry-run/SDK semantics.
- [x] AC #2: independent fresh run guard returns 503 before mutation/queueing while preserving 404/409.
- [x] AC #3: offline Run gating, visible retry/recovery, fresh pre-submit check, and prepared-state preservation.
- [x] AC #4: focused protocol/API coverage plus two independently recorded full 63-pass runs; only existing warning disclosed.
- [x] AC #5: hashed sanitized browser evidence proves no-generation disconnected/recovery behavior and states its limits.
