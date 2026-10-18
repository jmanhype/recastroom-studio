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
updated_at: 2026-10-18T03:53:01Z
content_hash: "sha256:93bdce7576cb02b884e7e962d4fe651eca80776b7fe067275c47169dd200268d"
blocked_by: [OJ-4rht]
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
- OJ-4rht `app/web/index.html` -> complete real guided flow and semantic controls.
- OJ-4rht `app/web/studio.js` -> real user-driven DOM/event flow; tests must not call nonexistent `setStage`, `renderStatus`, `renderPrepareResult`, or `resetStaleJob` methods.
- OJ-4rht `app/web/studio.js` -> frozen read-only `window.StudioUI.errorText(value): string` for normalized error observation only.
- OJ-4rht `app/web/studio.js` -> frozen read-only `window.StudioUI.getState(): { epoch, jobId, busy, running, recommended, backend }` for state observation only.
- Backend HTTP endpoints independently: `POST /api/prepare`, `POST /api/jobs/{job_id}/run` (409 when active), and `GET /api/jobs/{job_id}/status`; complete artifacts are `generated|final|side_by_side`.
- OJ-xtk4 -> accepted aspect-preserving `make_side_by_side` behavior.
- OJ-inuo -> accepted source-layout/loudness-preserving restored audio behavior.

## Story Acceptance Criteria
1. Manual verification/smoke test: a real local CUA browser E2E run uses the real dry-run backend and all three synthetic fixtures to complete upload, rights consent, prepare, run, status transitions, compare, and artifact download without mocks or external inference.
2. Browser evidence includes actual desktop and mobile screenshots of the finished cinematic flow, plus a reduced-motion screenshot; each is a nonempty image artifact with SHA-256 recorded in evidence, not merely a string assertion.
3. Keyboard-only operation reaches every interactive control with visible focus, submits the guided flow, and activates download/recovery controls; reduced-motion evidence proves motion is suppressed when the browser preference is set.
4. Negative browser scenarios cover missing consent, prepare failure, terminal `error`, retry/new-job recovery, active/unknown/stale job handling, and no state that fabricates percent, ETA, QC verdict, or artifact availability.
5. Deterministic pytest regressions encode static UI invariants and real TestClient API behavior (no mocked backend) and pass repeatedly on the repository venv; the full suite also passes with the prior 31 tests intact and no skipped regressions.
6. Evidence identifies the local browser engine/version, viewport sizes, exact server/test commands, loopback bind address, fixture hashes, and clean process teardown; it contains no credentials, public URLs, absolute user paths, or public-safe claims not actually tested.
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
6. Evidence identifies the local browser engine/version, viewport sizes, exact server/test commands, loopback bind address, fixture hashes, and clean process teardown; it contains no credentials, public URLs, absolute user paths, or public-safe claims not actually tested.
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
