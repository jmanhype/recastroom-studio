---
id: OJ-4rht
title: "Cinematic guided studio frontend"
status: open
priority: 1
type: task
labels: [walking-skeleton, skeleton, frontend, external-integration]
parent: OJ-a7l6
created_at: 2026-10-18T01:53:57Z
created_by: speed
updated_at: 2026-10-18T01:56:21Z
content_hash: "sha256:1a2c7b8189d89bccd3560268a8f041d0dc184973e4315e7d64c7ce65f93032ff"
blocks: [OJ-yf2c]
---

## Description
## USER INTENT
As an authorized creator, I want a clear cinematic studio surface for my source clip and performer references, so I can confidently prepare, run, inspect, compare, and download a local job without pretending to know progress that the API does not provide.

## Embedded Context
- Baseline main is `7ab3b8c`; worktree was clean and the existing suite baseline is 31 passing tests.
- Existing static entry: `app/web/index.html`. It may be polished in place and split into `app/web/styles.css` and `app/web/studio.js`.
- No graph index exists. The verified backend is the source of truth:
  - `GET /api/health` returns `ok`, `workflow`, `workflow_exists`, and `backend`.
  - `POST /api/prepare` is multipart with `source`, `reference_1`, optional `reference_2`, optional `words`, `identity`, `seed`, and `rights_attested`; it returns `job_id`, `scene.recommended`, `manifest`, `workflow_url`, and `prompt_url`.
  - `POST /api/jobs/{job_id}/run` returns `job_id` and `state="queued"`; active `uploading`, `generating`, or `downloading` work is rejected.
  - `GET /api/jobs/{job_id}/status` can report `queued`, `uploading`, `generating`, `downloading`, `complete`, or `error`, with `message`, `backend`, and on complete `artifacts` containing `generated`, `final`, and `side_by_side`.
  - Real downloads are `/api/jobs/{job_id}/artifacts/{artifact}` for exactly `generated`, `final`, and `side_by_side`.
- When health reports `backend="dry_run"`, say explicitly that dry-run performs no AI inference. For `legacy` or `sdk`, do not make that no-inference claim.

## Boundary Map
PRODUCES:
- `app/web/index.html` -> semantic cinematic studio DOM and guided upload/prepare/run/review flow
- `app/web/styles.css` -> responsive desktop/mobile styling, visual hierarchy, focus states, and reduced-motion support
- `app/web/studio.js` -> `window.StudioUI.setStage(stage: string): void`; `window.StudioUI.renderPrepareResult(payload: object): void`; `window.StudioUI.renderStatus(status: object): void`; `window.StudioUI.resetStaleJob(): void`

CONSUMES:
- (none -- leaf story; all existing HTTP contracts are embedded above)

## Story Acceptance Criteria
1. The studio presents a high-fidelity cinematic brand and responsive layout on desktop and mobile, with live previews for the selected source and up to two performer images and accessible names/labels for every control.
2. A guided flow clearly separates source/reference upload, rights consent, prepare, run, and review; submission controls remain disabled until required files and the manually checked rights box are present, and the checkbox is never prechecked or silently set.
3. The UI displays only API-backed stage truth for `queued`, `uploading`, `generating`, `downloading`, `complete`, and `error`; it shows no percentage, ETA, fabricated QC verdict, or invented backend state.
4. In `dry_run`, the interface explicitly identifies local deterministic execution and states that no AI inference occurs; other backends are identified without that claim.
5. A complete job offers source/result review, including `side_by_side`, and real download links for `generated`, `final`, and `side_by_side` using the API artifact routes; links are absent or disabled before artifacts exist.
6. Prepare/network/error responses and terminal `error` state are visible in plain language with a recoverable retry/new-job action; a stale or missing job can be reset without page reload and does not leave the run button permanently disabled.
7. The implementation remains static vanilla frontend code, preserves the backend/API/generation code, adds no mandatory dependency or React migration, and passes the baseline suite.
8. Manual verification/smoke test exercises the real loopback `/api/health`, `/api/prepare`, run, status, and artifact endpoints from the local browser in `dry_run`; no external service or credential is used.

## Testing Requirements
- Integration tests: MANDATORY, real local API/static integration (no mocked backend): run the app in `dry_run` with `tests/fixtures/synthetic_source.mp4`, `tests/fixtures/synthetic_reference.png`, and `tests/fixtures/word_timings.json`, upload through the browser, prepare, run to `complete`, and prove artifact routes open.
- Accessibility/responsiveness: check keyboard traversal, visible focus, and `prefers-reduced-motion` in a local browser; automated coverage is expanded in the capstone.
- Commands: `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest` must remain at least the 31-test baseline, with no new failures.
- Evidence: save at least one local browser screenshot and a short command/output note under a new frontend evidence directory; include artifact paths and SHA-256 for screenshots.

## OUT OF SCOPE
- Backend/API/generation changes: the approved frontend upgrade must preserve accepted pipeline semantics.
- Browser automation architecture: the dependent capstone owns deterministic E2E and regression coverage.
- New package/runtime dependencies or a framework migration: the approved direction is vanilla static code.
- Public deployment or cloud/GPU work: owner-gated and forbidden in this epic.

## DIFF BUDGET
- About 3 files under `app/web/`, under 900 changed LOC total.

## MANDATORY SKILLS
- `frontend-design`: cinematic visual direction and distinctive production-grade UI.
- `design-taste-frontend`: avoid generic dashboard/gradient cliches and preserve hierarchy.
- `frontend-responsive-ui`: mobile-first responsive and accessibility implementation.

## Approved Research
- Read `../research/x_frontend_signals/ELITE_UI_STACK.md`. Reuse only licensed/original patterns or generic interaction principles; do not copy third-party assets or code.

## Delivery Requirements
- Paste exact test/browser-command output and artifact paths/hashes into nd notes.
- Include an AC verification table.
- Include a nonempty `LEARNINGS:` block and `OBSERVATIONS:` (write `None` only if truly none).

## nd_contract
status: new

### evidence
- Created from approved frontend-upgrade scope at main `7ab3b8c`.

### proof
- [ ] AC #1: Responsive cinematic studio with source/reference previews and accessible controls.
- [ ] AC #2: Guided upload/prepare/run flow preserves manually checked rights consent.
- [ ] AC #3: Only truthful API-backed stage states are displayed.
- [ ] AC #4: Dry-run no-AI-inference disclosure is backend-conditional.
- [ ] AC #5: Complete source/result compare and real artifact downloads work.
- [ ] AC #6: Errors and stale jobs are visible and recoverable.
- [ ] AC #7: Static vanilla boundary is preserved and baseline tests pass.


## USER INTENT
As an authorized creator, I want a clear cinematic studio surface for my source clip and performer references, so I can confidently prepare, run, inspect, compare, and download a local job without pretending to know progress that the API does not provide.

## Embedded Context
- Baseline main is `7ab3b8c`; worktree was clean and the existing suite baseline is 31 passing tests.
- Existing static entry: `app/web/index.html`. It may be polished in place and split into `app/web/styles.css` and `app/web/studio.js`.
- No graph index exists. The verified backend is the source of truth:
  - `GET /api/health` returns `ok`, `workflow`, `workflow_exists`, and `backend`.
  - `POST /api/prepare` is multipart with `source`, `reference_1`, optional `reference_2`, optional `words`, `identity`, `seed`, and `rights_attested`; it returns `job_id`, `scene.recommended`, `manifest`, `workflow_url`, and `prompt_url`.
  - `POST /api/jobs/{job_id}/run` returns `job_id` and `state="queued"`; active `uploading`, `generating`, or `downloading` work is rejected.
  - `GET /api/jobs/{job_id}/status` can report `queued`, `uploading`, `generating`, `downloading`, `complete`, or `error`, with `message`, `backend`, and on complete `artifacts` containing `generated`, `final`, and `side_by_side`.
  - Real downloads are `/api/jobs/{job_id}/artifacts/{artifact}` for exactly `generated`, `final`, and `side_by_side`.
- When health reports `backend="dry_run"`, say explicitly that dry-run performs no AI inference. For `legacy` or `sdk`, do not make that no-inference claim.

## Boundary Map
PRODUCES:
- `app/web/index.html` -> semantic cinematic studio DOM and guided upload/prepare/run/review flow
- `app/web/styles.css` -> responsive desktop/mobile styling, visual hierarchy, focus states, and reduced-motion support
- `app/web/studio.js` -> `window.StudioUI.setStage(stage: string): void`; `window.StudioUI.renderPrepareResult(payload: object): void`; `window.StudioUI.renderStatus(status: object): void`; `window.StudioUI.resetStaleJob(): void`

CONSUMES:
- (none -- leaf story; all existing HTTP contracts are embedded above)

## Story Acceptance Criteria
1. The studio presents a high-fidelity cinematic brand and responsive layout on desktop and mobile, with live previews for the selected source and up to two performer images and accessible names/labels for every control.
2. A guided flow clearly separates source/reference upload, rights consent, prepare, run, and review; submission controls remain disabled until required files and the manually checked rights box are present, and the checkbox is never prechecked or silently set.
3. The UI displays only API-backed stage truth for `queued`, `uploading`, `generating`, `downloading`, `complete`, and `error`; it shows no percentage, ETA, fabricated QC verdict, or invented backend state.
4. In `dry_run`, the interface explicitly identifies local deterministic execution and states that no AI inference occurs; other backends are identified without that claim.
5. A complete job offers source/result review, including `side_by_side`, and real download links for `generated`, `final`, and `side_by_side` using the API artifact routes; links are absent or disabled before artifacts exist.
6. Prepare/network/error responses and terminal `error` state are visible in plain language with a recoverable retry/new-job action; a stale or missing job can be reset without page reload and does not leave the run button permanently disabled.
7. The implementation remains static vanilla frontend code, preserves the backend/API/generation code, adds no mandatory dependency or React migration, and passes the baseline suite.
8. Manual verification/smoke test exercises the real loopback `/api/health`, `/api/prepare`, run, status, and artifact endpoints from the local browser in `dry_run`; no external service or credential is used.

## Testing Requirements
- Integration tests: MANDATORY, real local API/static integration (no mocked backend): run the app in `dry_run` with `tests/fixtures/synthetic_source.mp4`, `tests/fixtures/synthetic_reference.png`, and `tests/fixtures/word_timings.json`, upload through the browser, prepare, run to `complete`, and prove artifact routes open.
- Accessibility/responsiveness: check keyboard traversal, visible focus, and `prefers-reduced-motion` in a local browser; automated coverage is expanded in the capstone.
- Commands: `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest` must remain at least the 31-test baseline, with no new failures.
- Evidence: save at least one local browser screenshot and a short command/output note under a new frontend evidence directory; include artifact paths and SHA-256 for screenshots.

## OUT OF SCOPE
- Backend/API/generation changes: the approved frontend upgrade must preserve accepted pipeline semantics.
- Browser automation architecture: the dependent capstone owns deterministic E2E and regression coverage.
- New package/runtime dependencies or a framework migration: the approved direction is vanilla static code.
- Public deployment or cloud/GPU work: owner-gated and forbidden in this epic.

## DIFF BUDGET
- About 3 files under `app/web/`, under 900 changed LOC total.

## MANDATORY SKILLS
- `frontend-design`: cinematic visual direction and distinctive production-grade UI.
- `design-taste-frontend`: avoid generic dashboard/gradient cliches and preserve hierarchy.
- `frontend-responsive-ui`: mobile-first responsive and accessibility implementation.

## Approved Research
- Read `../research/x_frontend_signals/ELITE_UI_STACK.md`. Reuse only licensed/original patterns or generic interaction principles; do not copy third-party assets or code.

## Delivery Requirements
- Paste exact test/browser-command output and artifact paths/hashes into nd notes.
- Include an AC verification table.
- Include a nonempty `LEARNINGS:` block and `OBSERVATIONS:` (write `None` only if truly none).

## nd_contract
status: new

### evidence
- Created from approved frontend-upgrade scope at main `7ab3b8c`.

### proof
- [ ] AC #1: Responsive cinematic studio with source/reference previews and accessible controls.
- [ ] AC #2: Guided upload/prepare/run flow preserves manually checked rights consent.
- [ ] AC #3: Only truthful API-backed stage states are displayed.
- [ ] AC #4: Dry-run no-AI-inference disclosure is backend-conditional.
- [ ] AC #5: Complete source/result compare and real artifact downloads work.
- [ ] AC #6: Errors and stale jobs are visible and recoverable.
- [ ] AC #7: Static vanilla boundary is preserved and baseline tests pass.

## USER INTENT
As an authorized creator, I want a clear cinematic studio surface for my source clip and performer references, so I can confidently prepare, run, inspect, compare, and download a local job without pretending to know progress that the API does not provide.

## Embedded Context
- Baseline main is `7ab3b8c`; worktree was clean and the existing suite baseline is 31 passing tests.
- Existing static entry: `app/web/index.html`. It may be polished in place and split into `app/web/styles.css` and `app/web/studio.js`.
- No graph index exists. The verified backend is the source of truth:
  - `GET /api/health` returns `ok`, `workflow`, `workflow_exists`, and `backend`.
  - `POST /api/prepare` is multipart with `source`, `reference_1`, optional `reference_2`, optional `words`, `identity`, `seed`, and `rights_attested`; it returns `job_id`, `scene.recommended`, `manifest`, `workflow_url`, and `prompt_url`.
  - `POST /api/jobs/{job_id}/run` returns `job_id` and `state="queued"`; active `uploading`, `generating`, or `downloading` work is rejected.
  - `GET /api/jobs/{job_id}/status` can report `queued`, `uploading`, `generating`, `downloading`, `complete`, or `error`, with `message`, `backend`, and on complete `artifacts` containing `generated`, `final`, and `side_by_side`.
  - Real downloads are `/api/jobs/{job_id}/artifacts/{artifact}` for exactly `generated`, `final`, and `side_by_side`.
- When health reports `backend="dry_run"`, say explicitly that dry-run performs no AI inference. For `legacy` or `sdk`, do not make that no-inference claim.

## Boundary Map
PRODUCES:
- `app/web/index.html` -> semantic cinematic studio DOM and guided upload/prepare/run/review flow
- `app/web/styles.css` -> responsive desktop/mobile styling, visual hierarchy, focus states, and reduced-motion support
- `app/web/studio.js` -> `window.StudioUI.setStage(stage: string): void`; `window.StudioUI.renderPrepareResult(payload: object): void`; `window.StudioUI.renderStatus(status: object): void`; `window.StudioUI.resetStaleJob(): void`

CONSUMES:
- (none -- leaf story; all existing HTTP contracts are embedded above)

## Acceptance Criteria
1. The studio presents a high-fidelity cinematic brand and responsive layout on desktop and mobile, with live previews for the selected source and up to two performer images and accessible names/labels for every control.
2. A guided flow clearly separates source/reference upload, rights consent, prepare, run, and review; submission controls remain disabled until required files and the manually checked rights box are present, and the checkbox is never prechecked or silently set.
3. The UI displays only API-backed stage truth for `queued`, `uploading`, `generating`, `downloading`, `complete`, and `error`; it shows no percentage, ETA, fabricated QC verdict, or invented backend state.
4. In `dry_run`, the interface explicitly identifies local deterministic execution and states that no AI inference occurs; other backends are identified without that claim.
5. A complete job offers source/result review, including `side_by_side`, and real download links for `generated`, `final`, and `side_by_side` using the API artifact routes; links are absent or disabled before artifacts exist.
6. Prepare/network/error responses and terminal `error` state are visible in plain language with a recoverable retry/new-job action; a stale or missing job can be reset without page reload and does not leave the run button permanently disabled.
7. The implementation remains static vanilla frontend code, preserves the backend/API/generation code, adds no mandatory dependency or React migration, and passes the baseline suite.

## Testing Requirements
- Integration tests: MANDATORY, real local API/static integration (no mocked backend): run the app in `dry_run` with `tests/fixtures/synthetic_source.mp4`, `tests/fixtures/synthetic_reference.png`, and `tests/fixtures/word_timings.json`, upload through the browser, prepare, run to `complete`, and prove artifact routes open.
- Accessibility/responsiveness: check keyboard traversal, visible focus, and `prefers-reduced-motion` in a local browser; automated coverage is expanded in the capstone.
- Commands: `PYTHONPATH=src ../.venv/bin/pytest` must remain at least the 31-test baseline, with no new failures.
- Evidence: save at least one local browser screenshot and a short command/output note under a new frontend evidence directory; include artifact paths and SHA-256 for screenshots.

## OUT OF SCOPE
- Backend/API/generation changes: the approved frontend upgrade must preserve accepted pipeline semantics.
- Browser automation architecture: the dependent capstone owns deterministic E2E and regression coverage.
- New package/runtime dependencies or a framework migration: the approved direction is vanilla static code.
- Public deployment or cloud/GPU work: owner-gated and forbidden in this epic.

## DIFF BUDGET
- About 3 files under `app/web/`, under 900 changed LOC total.

## MANDATORY SKILLS
- `frontend-design`: cinematic visual direction and distinctive production-grade UI.
- `design-taste-frontend`: avoid generic dashboard/gradient cliches and preserve hierarchy.
- `frontend-responsive-ui`: mobile-first responsive and accessibility implementation.

## Approved Research
- Read `../research/x_frontend_signals/ELITE_UI_STACK.md`. Reuse only licensed/original patterns or generic interaction principles; do not copy third-party assets or code.

## Delivery Requirements
- Paste exact test/browser-command output and artifact paths/hashes into nd notes.
- Include an AC verification table.
- Include a nonempty `LEARNINGS:` block and `OBSERVATIONS:` (write `None` only if truly none).

## nd_contract
status: new

### evidence
- Created from approved frontend-upgrade scope at main `7ab3b8c`.

### proof
- [ ] AC #1: Responsive cinematic studio with source/reference previews and accessible controls.
- [ ] AC #2: Guided upload/prepare/run flow preserves manually checked rights consent.
- [ ] AC #3: Only truthful API-backed stage states are displayed.
- [ ] AC #4: Dry-run no-AI-inference disclosure is backend-conditional.
- [ ] AC #5: Complete source/result compare and real artifact downloads work.
- [ ] AC #6: Errors and stale jobs are visible and recoverable.
- [ ] AC #7: Static vanilla boundary is preserved and baseline tests pass.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T01:53:57Z dep_added: blocks OJ-yf2c

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]

## Comments
