---
id: OJ-yf2c
title: "E2e: prove the cinematic local studio upgrade"
status: open
priority: 1
type: task
labels: [capstone, e2e, frontend, external-integration]
parent: OJ-a7l6
created_at: 2026-10-18T01:53:57Z
created_by: speed
updated_at: 2026-10-18T14:22:12Z
content_hash: "sha256:0eab6cd741f2403ba629e8a1741d65df87d270d0dc28b8a69bc3aff948ee26c7"
was_blocked_by: [OJ-4rht, OJ-xtk4, OJ-inuo, OJ-p8rd, OJ-c1vo]
follows: [OJ-4rht, OJ-xtk4, OJ-inuo, OJ-p8rd]
blocked_by: [OJ-tfyt]
---

## Description

## Description
## USER INTENT
As the studio owner, I want reproducible local browser proof that the upgraded frontend guides a synthetic rights-clean job through dry-run and remains usable under real failure/stale conditions, so I can accept the interface based on artifacts rather than text claims.

## Embedded Context
- Depends on OJ-4rht, OJ-xtk4, and OJ-inuo; do not start until all blockers are delivered/accepted. OJ-inuo is serialized after OJ-xtk4 because both edit `src/openjutsu/media.py`.
- Baseline main is `7ab3b8c`; baseline suite is 31 passing tests. Use parent venv: `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest`.
- Required synthetic fixtures already exist: `tests/fixtures/synthetic_source.mp4`, `tests/fixtures/synthetic_reference.png`, and `tests/fixtures/word_timings.json`.
- `scripts/local_trial.py` can start a loopback-only dry-run trial and record evidence; a new browser-specific runner may use its loopback safety conventions but must not expose the app beyond localhost.
- The API contracts are those delivered by OJ-4rht: health, prepare, run, status, and artifact routes. Browser evidence must use the real backend in `dry_run`, with no external service, cloud inference, GPU, credentials, or mocked backend.

## Historical Boundary Map (superseded 2026-10-17; original text unchanged)
PRODUCES:
- `tests/test_frontend_regression.py` -> deterministic pytest static/API regressions covering guided controls, truthfulness, artifact availability, error/retry, and stale state
- `docs/evidence/frontend-upgrade/` -> local browser run log, desktop screenshot, mobile screenshot, reduced-motion screenshot, and SHA-256 manifest

CONSUMES:
- OJ-4rht: `app/web/index.html` -> complete guided studio flow
  endpoint: `POST /api/prepare`; fields: `source`, `reference_1`, `reference_2`, `words`, `identity`, `seed`, `rights_attested`; returns `job_id`, `scene.recommended`, `manifest`, `workflow_url`, `prompt_url`
- OJ-4rht: `app/web/studio.js` -> `window.StudioUI.setStage(stage: string): void`
  endpoint: `POST /api/jobs/{job_id}/run`; returns `job_id`, `state="queued"`; 409 means already active
- OJ-4rht: `app/web/studio.js` -> `window.StudioUI.renderStatus(status: object): void`
  endpoint: `GET /api/jobs/{job_id}/status`; states `queued|uploading|generating|downloading|complete|error`; complete artifacts `generated|final|side_by_side`

## Boundary Map (authoritative reconciliation, 2026-10-17)
PRODUCES:
- `tests/test_frontend_regression.py` -> deterministic pytest static/API regressions covering guided controls, truthfulness, artifact availability, error/retry, stale state, and dependent media-export invariants
- `docs/evidence/frontend-upgrade/` -> local browser run log, desktop/mobile/reduced-motion screenshots, SHA-256 manifest, and any bounded dependent export checks

CONSUMES:
- OJ-4rht: `app/web/index.html` -> complete real guided flow and semantic controls
  source: app/web/index.html
  event: real DOM interaction; do not call nonexistent mutation methods
- OJ-4rht: `app/web/studio.js` -> real user-driven DOM/event flow
  source: app/web/studio.js
  spec: `setStage`, `renderStatus`, `renderPrepareResult`, and `resetStaleJob` are not public methods
- OJ-4rht: `app/web/studio.js` -> frozen read-only observation seam
  source: app/web/studio.js
  spec: `window.StudioUI.errorText(value): string`; `window.StudioUI.getState(): { epoch, jobId, busy, running, recommended, backend }`
  endpoint: `POST /api/prepare`; `POST /api/jobs/{job_id}/run`; `GET /api/jobs/{job_id}/status`
- OJ-xtk4: `src/openjutsu/media.py` -> accepted aspect-preserving `make_side_by_side`
  source: src/openjutsu/media.py
- OJ-inuo: `src/openjutsu/media.py` -> accepted source-layout/loudness-preserving restored audio
  source: src/openjutsu/media.py

## Story Acceptance Criteria
1. Manual verification/smoke test: a real local CUA browser E2E run uses the real dry-run backend and all three synthetic fixtures to complete upload, rights consent, prepare, run, status transitions, compare, and artifact download without mocks or external inference.
2. Browser evidence includes actual desktop and mobile screenshots of the finished cinematic flow, plus a reduced-motion screenshot; each is a nonempty image artifact with SHA-256 recorded in evidence, not merely a string assertion.
3. Keyboard-only operation reaches every interactive control with visible focus, submits the guided flow, and activates download/recovery controls; reduced-motion evidence proves motion is suppressed when the browser preference is set.
4. Negative browser scenarios cover missing consent, prepare failure, terminal `error`, retry/new-job recovery, active/unknown/stale job handling, and no state that fabricates percent, ETA, QC verdict, or artifact availability.
5. Deterministic pytest regressions encode static UI invariants and real TestClient API behavior (no mocked backend) and pass repeatedly on the repository venv; the full suite also passes with the prior 31 tests intact and no skipped regressions.
6. Evidence identifies the local browser engine/version, viewport sizes, exact server/test commands, loopback bind address, fixture hashes, and clean process teardown; private raw evidence outside the repository may retain absolute local paths for provenance, while checked-in receipts sanitize user-specific/public paths and contain no credentials, public leakage, or public-safe claims not actually tested.
7. The capstone changes only local deterministic tests/evidence plus CUA browser artifacts and any minimal frontend test hook required by OJ-4rht; it does not alter backend semantics, add a mandatory browser dependency, initialize the loop, or create source branches.

## Testing Requirements
- Browser evidence: use the operator-approved local CUA/browser workflow against the real loopback `dry_run` backend; no external endpoint, no mocked backend, and no new browser Python harness or package dependency.
- Pytest regressions: deterministic static/unit/API-integration coverage may use FastAPI `TestClient` against the real app, but must not mock the backend; do not skip when the browser is unavailable.
- Commands to run: `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest tests/test_frontend_regression.py`, then `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest`.
- Run the deterministic pytest regressions at least twice and include both outputs; retain CUA browser evidence separately.

- Screenshot/artifact evidence must be checked into the local repository evidence directory with hashes.

## OUT OF SCOPE
- Visual redesign: consume the accepted interface from OJ-4rht; report defects rather than reopening broad design scope.
- Backend/API/generation work: this story proves the existing contract, not changes it.
- Cloud/GPU/credential/publication: owner-gated and forbidden.
- Framework/package migration: use existing local tooling; a dependency is not mandatory.

## DIFF BUDGET
- About 3-8 files (frontend evidence plus one focused E2E test file), under 700 changed source/test LOC, excluding generated PNG evidence.

## MANDATORY SKILLS
- `frontend-design`: evaluate intended cinematic hierarchy and visual fidelity.
- `design-taste-frontend`: adversarial UI-quality review.
- `frontend-responsive-ui`: responsive, keyboard, and reduced-motion verification.

## Delivery Requirements
- Paste both repeated pytest outputs and browser-runner output.
- Include screenshot paths, dimensions, and SHA-256 hashes.
- Include an AC verification table.
- Include a nonempty `LEARNINGS:` block and `OBSERVATIONS:` (write `None` only if truly none).

## nd_contract
status: new

### evidence
- Created as the dependent local browser capstone for OJ-4rht.

### proof
- [ ] AC #1: Real dry-run browser E2E completes with synthetic fixtures and no mocks.
- [ ] AC #2: Desktop, mobile, and reduced-motion screenshot artifacts and hashes exist.
- [ ] AC #3: Keyboard and reduced-motion behavior is proven in a browser.
- [ ] AC #4: Error, retry, active, unknown, and stale states are proven without fiction.
- [ ] AC #5: Focused and full deterministic pytest suites pass twice.
- [ ] AC #6: Local browser/runtime/fixture evidence is complete, public-safe, and cleanly torn down.
- [ ] AC #7: Capstone scope and local-only boundary are preserved.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T01:53:57Z dep_added: blocked_by OJ-4rht

## Links
- Parent: [[OJ-a7l6]]
- Blocked by: [[OJ-4rht]]

## Comments

## nd_contract
status: new

### evidence
- 2026-10-17 dogfood intake reconciled the StudioUI contract to read-only `getState`/`errorText` plus real user-driven events, and extended dependencies to OJ-4rht, OJ-xtk4, and OJ-inuo.

### proof
- [ ] AC #1-7 remain satisfied after all blockers, with no nonexistent StudioUI mutation methods invoked.
- [ ] Dependency proof shows OJ-4rht, OJ-xtk4, and OJ-inuo were delivered/accepted before capstone execution.


## USER INTENT
As the studio owner, I want reproducible local browser proof that the upgraded frontend guides a synthetic rights-clean job through dry-run and remains usable under real failure/stale conditions, so I can accept the interface based on artifacts rather than text claims.

## Embedded Context
- Depends on OJ-4rht; do not start until that story is delivered/accepted.
- Baseline main is `7ab3b8c`; baseline suite is 31 passing tests. Use parent venv: `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest`.
- Required synthetic fixtures already exist: `tests/fixtures/synthetic_source.mp4`, `tests/fixtures/synthetic_reference.png`, and `tests/fixtures/word_timings.json`.
- `scripts/local_trial.py` can start a loopback-only dry-run trial and record evidence; a new browser-specific runner may use its loopback safety conventions but must not expose the app beyond localhost.
- The API contracts are those delivered by OJ-4rht: health, prepare, run, status, and artifact routes. Browser evidence must use the real backend in `dry_run`, with no external service, cloud inference, GPU, credentials, or mocked backend.

## Boundary Map
PRODUCES:
- `tests/test_frontend_regression.py` -> deterministic pytest static/API regressions covering guided controls, truthfulness, artifact availability, error/retry, and stale state
- `docs/evidence/frontend-upgrade/` -> local browser run log, desktop screenshot, mobile screenshot, reduced-motion screenshot, and SHA-256 manifest

CONSUMES:
- OJ-4rht: `app/web/index.html` -> complete guided studio flow
  endpoint: `POST /api/prepare`; fields: `source`, `reference_1`, `reference_2`, `words`, `identity`, `seed`, `rights_attested`; returns `job_id`, `scene.recommended`, `manifest`, `workflow_url`, `prompt_url`
- OJ-4rht: `app/web/studio.js` -> `window.StudioUI.setStage(stage: string): void`
  endpoint: `POST /api/jobs/{job_id}/run`; returns `job_id`, `state="queued"`; 409 means already active
- OJ-4rht: `app/web/studio.js` -> `window.StudioUI.renderStatus(status: object): void`
  endpoint: `GET /api/jobs/{job_id}/status`; states `queued|uploading|generating|downloading|complete|error`; complete artifacts `generated|final|side_by_side`

## Story Acceptance Criteria
1. Manual verification/smoke test: a real local CUA browser E2E run uses the real dry-run backend and all three synthetic fixtures to complete upload, rights consent, prepare, run, status transitions, compare, and artifact download without mocks or external inference.
2. Browser evidence includes actual desktop and mobile screenshots of the finished cinematic flow, plus a reduced-motion screenshot; each is a nonempty image artifact with SHA-256 recorded in evidence, not merely a string assertion.
3. Keyboard-only operation reaches every interactive control with visible focus, submits the guided flow, and activates download/recovery controls; reduced-motion evidence proves motion is suppressed when the browser preference is set.
4. Negative browser scenarios cover missing consent, prepare failure, terminal `error`, retry/new-job recovery, active/unknown/stale job handling, and no state that fabricates percent, ETA, QC verdict, or artifact availability.
5. Deterministic pytest regressions encode static UI invariants and real TestClient API behavior (no mocked backend) and pass repeatedly on the repository venv; the full suite also passes with the prior 31 tests intact and no skipped regressions.
6. Evidence identifies the local browser engine/version, viewport sizes, exact server/test commands, loopback bind address, fixture hashes, and clean process teardown; private raw evidence outside the repository may retain absolute local paths for provenance, while checked-in receipts sanitize user-specific/public paths and contain no credentials, public leakage, or public-safe claims not actually tested.
7. The capstone changes only local deterministic tests/evidence plus CUA browser artifacts and any minimal frontend test hook required by OJ-4rht; it does not alter backend semantics, add a mandatory browser dependency, initialize the loop, or create source branches.

## Testing Requirements
- Browser evidence: use the operator-approved local CUA/browser workflow against the real loopback `dry_run` backend; no external endpoint, no mocked backend, and no new browser Python harness or package dependency.
- Pytest regressions: deterministic static/unit/API-integration coverage may use FastAPI `TestClient` against the real app, but must not mock the backend; do not skip when the browser is unavailable.
- Commands to run: `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest tests/test_frontend_regression.py`, then `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest`.
- Run the deterministic pytest regressions at least twice and include both outputs; retain CUA browser evidence separately.

- Screenshot/artifact evidence must be checked into the local repository evidence directory with hashes.

## OUT OF SCOPE
- Visual redesign: consume the accepted interface from OJ-4rht; report defects rather than reopening broad design scope.
- Backend/API/generation work: this story proves the existing contract, not changes it.
- Cloud/GPU/credential/publication: owner-gated and forbidden.
- Framework/package migration: use existing local tooling; a dependency is not mandatory.

## DIFF BUDGET
- About 3-8 files (frontend evidence plus one focused E2E test file), under 700 changed source/test LOC, excluding generated PNG evidence.

## MANDATORY SKILLS
- `frontend-design`: evaluate intended cinematic hierarchy and visual fidelity.
- `design-taste-frontend`: adversarial UI-quality review.
- `frontend-responsive-ui`: responsive, keyboard, and reduced-motion verification.

## Delivery Requirements
- Paste both repeated pytest outputs and browser-runner output.
- Include screenshot paths, dimensions, and SHA-256 hashes.
- Include an AC verification table.
- Include a nonempty `LEARNINGS:` block and `OBSERVATIONS:` (write `None` only if truly none).

## nd_contract
status: new

### evidence
- Created as the dependent local browser capstone for OJ-4rht.

### proof
- [ ] AC #1: Real dry-run browser E2E completes with synthetic fixtures and no mocks.
- [ ] AC #2: Desktop, mobile, and reduced-motion screenshot artifacts and hashes exist.
- [ ] AC #3: Keyboard and reduced-motion behavior is proven in a browser.
- [ ] AC #4: Error, retry, active, unknown, and stale states are proven without fiction.
- [ ] AC #5: Focused and full deterministic pytest suites pass twice.
- [ ] AC #6: Local browser/runtime/fixture evidence is complete, public-safe, and cleanly torn down.
- [ ] AC #7: Capstone scope and local-only boundary are preserved.

## Acceptance Criteria


## Design


## Notes
2026-10-17 evidence-path policy: AC6 distinguishes private raw CUA/browser evidence from checked-in receipts. Raw local evidence outside Git may preserve absolute paths for provenance; checked-in receipts must sanitize user-specific paths and prevent public leakage while retaining hashes, artifact identity, commands, and reference to the private source.
2026-10-17 evidence-path policy: AC6 distinguishes private raw CUA/browser evidence from checked-in receipts. Raw local evidence outside Git may preserve absolute paths for provenance; checked-in receipts must sanitize user-specific paths and prevent public leakage while retaining hashes, artifact identity, commands, and reference to the private source.

## nd_contract
status: new

### evidence
- Partial local checkpoint baa28bc6bb5da5a8fddec4c308bf5422dd1328a6; no delivery, acceptance, or capstone/epic merge. OJ-yf2c released open for remaining browser proof.
- Accepted OJ-p8rd source a7ed346 locally merged epic 7881cb0; repaired status retry has four real status GETs HTTP200, zero status500. Separate true missing-job run404 recovery proved.
- Combined suite on 5bc83e8: 52 passed twice (17.31s / 16.67s), one existing Starlette/httpx warning, no skipped regressions. Logs committed in docs/evidence/frontend-upgrade/followup/.
- Independently verified 47 screenshot originals/copies/hashes/dimensions and text manifests. Keyboard traversed three native players and six subcontrols each; downloads, reset, status recovery and health recovery exercised. This uses isolated synthetic QA fixtures, not the approved creative reference.
- Final authoritative report: docs/evidence/frontend-upgrade/followup/COORDINATOR_CHECKPOINT.md; LIVE_CHECK.json and COORDINATOR_SHA256SUMS.json record local liveness and unchanged approved artifact hashes.
- pvg loop recover removed the serving preview checkout/epic ref; coordinator restored exact 7881cb0 from retained history and restarted identical config/data as PID49984. Page/health/original job status200, workflow exists. QA ports8894/8895 stopped; two new QA tabs explicitly closed before teardown; original8893 intentionally running.
- Two native Chrome capture failures -3811 leave actual #result reduced-motion suppression unproven. Earlier body-only CSS is insufficient. Exact IAB patch version and exhaustive native-control focus-indicator proof remain open.
- No design/render change, GPU/API inference spend, push, publication, or public tunnel. bd sync --from-main unavailable: no beads database; shared Paivot nd remains the existing tracker, no competing database initialized.

### proof
- [x] AC #1: Real local dry-run flow, repaired retry and byte-identical downloaded final demonstrated.
- [x] AC #2: Existing desktop/mobile/motion screenshots retained; follow-up hashes and dimensions verified.
- [ ] AC #3: Keyboard traversal demonstrated, but every-control visible-focus audit and actual reduced-motion suppression still require browser proof.
- [x] AC #4: Earlier negative/stale evidence retained; repaired retry and genuine health recovery added without invented progress.
- [x] AC #5: Focused evidence retained; combined full suite52 passes twice with one disclosed warning.
- [ ] AC #6: New QA cleanup/commands/hashes proven; exact IAB patch engine version still not established by reduced UA Chrome/155.0.0.0.
- [x] AC #7: This checkpoint changes evidence only; atomic backend repair was separately accepted as OJ-p8rd.

LEARNINGS: A completed traversal is not exhaustive visual focus proof. Body CSS cannot prove a child animation is suppressed. Recovery tooling can delete a serving worktree; preserve commit history and reverify liveness.
OBSERVATIONS: Status-race fix accepted/live; capstone remains open, not all-green. No workers remain active.


## nd_contract
status: new

### evidence
- Local checkpoint ada128cdb0a5167a5c8acd57a1ff3b4d72485d7a on story/OJ-yf2c; clean worktree; not merged, pushed, delivered, or accepted. Claim released because no worker remains active; incomplete evidence remains open.
- Four new real TestClient/static tests; focused suite passed twice, full suite passed twice (45 tests); coordinator rerun: 45 passed, 1 preexisting warning in 23.71s. No mocks or prior test edits.
- Real CUA dry_run E2E completed on isolated loopback 8894 with keyboard upload/prepare/run/download. Desktop/mobile, consent, invalid prepare, terminal error, retry, active/unknown/stale and reset evidence recorded in docs/evidence/frontend-upgrade/REPORT.md and browser/.
- Observed actual status HTTP500/JSONDecodeError during retry; UI safely blocked duplicate run and Check status again recovered. Separate P1 OJ-p8rd records non-atomic status publication diagnosis; production fix not included here.
- GLM read-only checkpoint review: APPROVED CHECKPOINT, not capstone acceptance. Independently checked all 10 manifest hashes, screenshot dimensions/encoding, fixture/test hashes, scope and private-path scan; no blocking findings.
- 8894 test server stopped; approved 8893 PID82602 retained; viewport override reset; Chrome motion preference restored. Explicit temporary IAB-tab close blocked by error-page URL policy and not proven.
- No GPU/API generation spend, no production/design/render changes. bd sync --from-main unavailable: this repository has no beads database; existing shared Paivot nd vault remains source of record, no competing database initialized.

### proof
- [x] AC #1: Actual local dry-run browser E2E and byte-verified final download.
- [x] AC #2: Desktop/mobile/reduced-motion image artifacts, dimensions and hashes.
- [ ] AC #3: Substantial keyboard proof present; exhaustive focus proof for every native media subcontrol and conditional health-retry control remains open.
- [x] AC #4: Required negative scenarios exercised, genuine backend defect disclosed and recovery proven.
- [x] AC #5: Repeated focused/full deterministic suites and independent coordinator full run pass.
- [ ] AC #6: Commands/viewports/fixtures/runtime/teardown evidence present; exact IAB engine version and explicit QA-tab cleanup not independently proven.
- [x] AC #7: Only test/evidence additions; no production semantics or external spend changes.

LEARNINGS: Serial TestClient green does not establish concurrent polling safety. Immediate active-state capture is necessary before short dry-run jobs complete.

OBSERVATIONS: Next evidence work must resolve AC3/AC6 without reopening approved design; OJ-p8rd is a separate bounded concurrency repair requiring review. This checkpoint is not a release or epic-completion claim.

## History
- 2026-10-18T01:53:57Z dep_added: blocked_by OJ-4rht
- 2026-10-18T03:53:02Z dep_added: blocked_by OJ-xtk4
- 2026-10-18T03:53:02Z dep_added: blocked_by OJ-inuo
- 2026-10-18T04:08:39Z dep_removed: was_blocked_by OJ-4rht
- 2026-10-18T04:14:18Z dep_removed: was_blocked_by OJ-xtk4
- 2026-10-18T04:33:19Z dep_removed: was_blocked_by OJ-inuo
- 2026-10-18T13:33:23Z status: open -> in_progress
- 2026-10-18T13:33:23Z auto-follows: linked to predecessor OJ-4rht
- 2026-10-18T13:33:23Z auto-follows: linked to predecessor OJ-xtk4
- 2026-10-18T13:33:23Z auto-follows: linked to predecessor OJ-inuo
- 2026-10-18T13:33:23Z claimed by dev-OJ-yf2c
- 2026-10-18T13:49:50Z status: in_progress -> open
- 2026-10-18T13:49:50Z released by speed
- 2026-10-18T13:55:48Z dep_added: blocked_by OJ-p8rd
- 2026-10-18T14:11:21Z dep_removed: was_blocked_by OJ-p8rd
- 2026-10-18T14:13:38Z status: open -> in_progress
- 2026-10-18T14:13:38Z auto-follows: linked to predecessor OJ-p8rd
- 2026-10-18T14:13:38Z claimed by dev-OJ-yf2c
- 2026-10-18T14:18:29Z status: in_progress -> open
- 2026-10-18T14:18:51Z status: open -> in_progress
- 2026-10-18T14:18:52Z claimed by dev-OJ-yf2c
- 2026-10-18T14:22:12Z status: in_progress -> open
- 2026-10-18T14:22:12Z released by speed
- 2026-10-18T14:53:03Z dep_added: blocked_by OJ-c1vo
- 2026-10-18T15:47:09Z dep_removed: was_blocked_by OJ-c1vo
- 2026-10-18T16:04:00Z dep_added: blocked_by OJ-tfyt

## Links
- Parent: [[OJ-a7l6]]
- Blocked by: [[OJ-tfyt]]
- Was blocked by: [[OJ-4rht]], [[OJ-xtk4]], [[OJ-inuo]], [[OJ-p8rd]], [[OJ-c1vo]]
- Follows: [[OJ-4rht]], [[OJ-xtk4]], [[OJ-inuo]], [[OJ-p8rd]]

## Comments

### 2026-10-18T14:18:29Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)
