---
id: OJ-4rht
title: "Cinematic guided studio frontend"
status: in_progress
priority: 1
type: task
labels: [walking-skeleton, skeleton, frontend, external-integration, delivered]
parent: OJ-a7l6
created_at: 2026-10-18T01:53:57Z
created_by: speed
updated_at: 2026-10-18T04:00:26Z
content_hash: "sha256:767c246f8c7c7b0a3d16449b070f0696c03bca609afe6d9bada76e638593f1af"
blocks: [OJ-yf2c]
assignee: dev-OJ-4rht
---

## Description

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

## Historical Boundary Map (superseded 2026-10-17; retained without editing its original text below this heading)
PRODUCES:
- `app/web/index.html` -> semantic cinematic studio DOM and guided upload/prepare/run/review flow
- `app/web/styles.css` -> responsive desktop/mobile styling, visual hierarchy, focus states, and reduced-motion support
- `app/web/studio.js` -> `window.StudioUI.setStage(stage: string): void`; `window.StudioUI.renderPrepareResult(payload: object): void`; `window.StudioUI.renderStatus(status: object): void`; `window.StudioUI.resetStaleJob(): void`

CONSUMES:
- (none -- leaf story; all existing HTTP contracts are embedded above)

## Boundary Map (authoritative reconciliation, 2026-10-17)
PRODUCES:
- `app/web/index.html` -> semantic cinematic studio DOM and guided upload/prepare/run/review flow
- `app/web/styles.css` -> responsive desktop/mobile styling, visual hierarchy, focus states, reduced-motion support, and complete intrinsic performer previews
- `app/web/studio.js` -> private event-driven flow helpers/listeners (including request, health, controls, invalidate, preview, submit, poll, run, reset, and retry paths)
- `app/web/studio.js` -> frozen read-only public seam `window.StudioUI.errorText(value): string`
- `app/web/studio.js` -> frozen read-only public seam `window.StudioUI.getState(): { epoch, jobId, busy, running, recommended, backend }`

CONSUMES:
- (none -- leaf story; all existing HTTP contracts are embedded above and no mutable StudioUI methods are produced)

INTERFACE RECONCILIATION:
- `app/web/studio.js:159-160` at story/OJ-4rht `63b9c00` exposes only frozen, read-only `errorText` and `getState`.
- Stage/prepare/status/reset behavior is implemented through private helpers and DOM/event paths, not `setStage`, `renderPrepareResult`, `renderStatus`, or `resetStaleJob`.
- Do not add mutable test/mutation seams merely to satisfy the historical map. Dependent tests must drive the real UI events and may use `getState`/`errorText` only for read-only observation.

## Story Acceptance Criteria
1. The studio presents a high-fidelity cinematic brand and responsive layout on desktop and mobile, with live previews for the selected source and up to two performer images and accessible names/labels for every control.
2. A guided flow clearly separates source/reference upload, rights consent, prepare, run, and review; submission controls remain disabled until required files and the manually checked rights box are present, and the checkbox is never prechecked or silently set.
3. The UI displays only API-backed stage truth for `queued`, `uploading`, `generating`, `downloading`, `complete`, and `error`; it shows no percentage, ETA, fabricated QC verdict, or invented backend state.
4. In `dry_run`, the interface explicitly identifies local deterministic execution and states that no AI inference occurs; other backends are identified without that claim.
5. A complete job offers source/result review, including `side_by_side`, and real download links for `generated`, `final`, and `side_by_side` using the API artifact routes; links are absent or disabled before artifacts exist.
6. Prepare/network/error responses and terminal `error` state are visible in plain language with a recoverable retry/new-job action; a stale or missing job can be reset without page reload and does not leave the run button permanently disabled.
7. The implementation remains static vanilla frontend code, preserves the backend/API/generation code, adds no mandatory dependency or React migration, and passes the baseline suite.
8. Manual verification/smoke test exercises the real loopback `/api/health`, `/api/prepare`, run, status, and artifact endpoints from the local browser in `dry_run`; no external service or credential is used.
9. Portrait and landscape performer-reference previews preserve the complete intrinsic image: the rendered media aspect ratio matches the natural aspect ratio within a stated tolerance, no clipping parent hides the face/chin, and desktop/mobile browser evidence proves the full image is visible.

## Testing Requirements
- Integration tests: MANDATORY, real local API/static integration (no mocked backend): run the app in `dry_run` with `tests/fixtures/synthetic_source.mp4`, `tests/fixtures/synthetic_reference.png`, and `tests/fixtures/word_timings.json`, upload through the browser, prepare, run to `complete`, and prove artifact routes open.
- Accessibility/responsiveness: check keyboard traversal, visible focus, and `prefers-reduced-motion` in a local browser; automated coverage is expanded in the capstone.
- Portrait preview regression: use local project-owned portrait and landscape reference images, record natural/rendered/container dimensions, and save screenshot evidence proving complete intrinsic visibility without clipping. Current dogfood measurement: 1086x1448 natural image rendered 283x377.328 inside a clipped 285x150 container (`browser-playback.json`).
- Paired-review aspect and restored audio export defects are separate stories OJ-xtk4/OJ-inuo; do not expand this frontend rework into `src/openjutsu/media.py`.
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

## Acceptance Criteria


## Design


## Notes
Routing recovery: GLM native worker stopped after repeated provider status502 stream failures; git status in story worktree clean and branch still7ab3b8c. Router activity confirmed no active old request before replacement. Fresh worker qwen_frontend_4rht routed exactly custom/Qwen-Ambassador/Qwen3.8-Max (not modelscope), same claimed isolated story. Implementation pending; no source changes or tests claimed.
User explicitly requested GPT-6 Astra frontend replacement. Qwen stopped, router activity empty, story worktree clean at7ab3b8c before replacement. Recreated clean Paivot-owned worktree on existing story branch. Fresh Astra bounded frontend-only task dispatched; medium effort, no delegation. Local commits only, backend/generation untouched; independent acceptance pending.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-17.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence
Summary: Cinematic static studio implemented, real browser smoke passed; independent acceptance pending.
Commit SHA: 90ec73d

### CI/Test Results
Commands run:
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q
- git diff --check
- node --check app/web/studio.js

## nd_contract
status: delivered

### evidence
- Implementation b5fd8e4; browser fix/evidence 90ec73d on story/OJ-4rht.
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q: 31 passed, 1 existing warning in 11.08s. docs/evidence/OJ-4rht/pytest.txt.
- git diff --check and node --check app/web/studio.js: exit 0.
- CUA browser real synthetic dry-run job 3af79afdac1c completed with source, final, paired videos and artifact links; paired download SHA256 eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9 matches server artifact.
- docs/evidence/OJ-4rht/desktop-review.jpg SHA256 e1129e68d907e0b8bd7f039334c4f55e1cae0d146f3fb73c1deeb43a1415c9db.
- docs/evidence/OJ-4rht/mobile-review.jpg SHA256 5839db2d82d46cb44dd5eb5bfa395a48ffcd17023a3691a7fa01b2ad829db082.
- Widths 375/414/768/1024/1440 had no horizontal overflow. Keyboard Space consent; two-reference job c00bba38d22c; reset during run remained cleared after server completion. Malformed timing input displayed actionable prepare error and disabled Run.
- Full procedure and limitations: docs/evidence/OJ-4rht/DELIVERY.md.

### proof
- [x] AC #1: Responsive source/two-reference previews, labels/focus/keyboard Space, reduced-motion stylesheet.
- [x] AC #2: Explicit unchecked rights gate, guided select/prepare/run/review with disabled explanations.
- [x] AC #3: Server states only, unknown health not free/local, dry_run explicitly no AI inference.
- [x] AC #4: Complete job shows final/paired review and real artifact links; paired download byte-hash verified.
- [x] AC #5: Inline errors and retry/reset; epoch/job snapshots, abort, URL revocation and text-safe API rendering. Browser reset race exercised; broader permutations reserved for dependent regression story.
- [x] AC #6: Backend unchanged, 31 baseline tests pass, real browser smoke and screenshot hashes saved.

### LEARNINGS
- Form control id reset shadows form.reset; use the prototype method. Browser smoke exposed and verified this repair.

### OBSERVATIONS
- No live inference/GPU/paid calls. No formal screen-reader or exhaustive race-suite claim. User judges aesthetics; independent PM acceptance remains required. Preview loopback 8892 remains running for review.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Implementation b5fd8e4; browser fix/evidence 90ec73d on story/OJ-4rht.
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q: 31 passed, 1 existing warning in 11.08s. docs/evidence/OJ-4rht/pytest.txt.
- git diff --check and node --check app/web/studio.js: exit 0.
- CUA browser real synthetic dry-run job 3af79afdac1c completed with source, final, paired videos and artifact links; paired download SHA256 eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9 matches server artifact.
- docs/evidence/OJ-4rht/desktop-review.jpg SHA256 e1129e68d907e0b8bd7f039334c4f55e1cae0d146f3fb73c1deeb43a1415c9db.
- docs/evidence/OJ-4rht/mobile-review.jpg SHA256 5839db2d82d46cb44dd5eb5bfa395a48ffcd17023a3691a7fa01b2ad829db082.
- Widths 375/414/768/1024/1440 had no horizontal overflow. Keyboard Space consent; two-reference job c00bba38d22c; reset during run remained cleared after server completion. Malformed timing input displayed actionable prepare error and disabled Run.
- Full procedure and limitations: docs/evidence/OJ-4rht/DELIVERY.md.

### proof
- [x] AC #1: Responsive source/two-reference previews, labels/focus/keyboard Space, reduced-motion stylesheet.
- [x] AC #2: Explicit unchecked rights gate, guided select/prepare/run/review with disabled explanations.
- [x] AC #3: Server states only, unknown health not free/local, dry_run explicitly no AI inference.
- [x] AC #4: Complete job shows final/paired review and real artifact links; paired download byte-hash verified.
- [x] AC #5: Inline errors and retry/reset; epoch/job snapshots, abort, URL revocation and text-safe API rendering. Browser reset race exercised; broader permutations reserved for dependent regression story.
- [x] AC #6: Backend unchanged, 31 baseline tests pass, real browser smoke and screenshot hashes saved.

### LEARNINGS
- Form control id reset shadows form.reset; use the prototype method. Browser smoke exposed and verified this repair.

### OBSERVATIONS
- No live inference/GPU/paid calls. No formal screen-reader or exhaustive race-suite claim. User judges aesthetics; independent PM acceptance remains required. Preview loopback 8892 remains running for review.

## nd_contract
status: in_progress

### evidence
- Claimed atomically by dispatcher; story/OJ-4rht worktree created from epic/OJ-a7l6 at 7ab3b8c.
- User explicitly authorized local commits and merges only. No remote configured.
- Backlog repaired through native restore/edit/sync; local API does not require secret provisioning.

### proof
- [ ] AC #1-8: Implementation and browser acceptance pending.

## History
- 2026-10-18T01:53:57Z dep_added: blocks OJ-yf2c
- 2026-10-18T01:57:44Z status: open -> in_progress
- 2026-10-18T01:57:44Z claimed by dev-OJ-4rht
- 2026-10-18T02:27:57Z status: in_progress -> in_progress
- 2026-10-18T02:31:39Z status: in_progress -> open
- 2026-10-18T02:31:40Z released by speed
- 2026-10-18T03:47:31Z status: open -> in_progress
- 2026-10-18T03:47:31Z claimed by dev-OJ-4rht

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]

## Comments


Tracker receipt normalization: existing developer proof copied to the end; independent acceptance is still pending. No history removed.

## Implementation Evidence
Summary: Cinematic static studio implemented, real browser smoke passed; independent acceptance pending.
Commit SHA: 90ec73d

### CI/Test Results
Commands run:
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q
- git diff --check
- node --check app/web/studio.js

## nd_contract
status: delivered

### evidence
- Implementation b5fd8e4; browser fix/evidence 90ec73d on story/OJ-4rht.
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q: 31 passed, 1 existing warning in 11.08s. docs/evidence/OJ-4rht/pytest.txt.
- git diff --check and node --check app/web/studio.js: exit 0.
- CUA browser real synthetic dry-run job 3af79afdac1c completed with source, final, paired videos and artifact links; paired download SHA256 eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9 matches server artifact.
- docs/evidence/OJ-4rht/desktop-review.jpg SHA256 e1129e68d907e0b8bd7f039334c4f55e1cae0d146f3fb73c1deeb43a1415c9db.
- docs/evidence/OJ-4rht/mobile-review.jpg SHA256 5839db2d82d46cb44dd5eb5bfa395a48ffcd17023a3691a7fa01b2ad829db082.
- Widths 375/414/768/1024/1440 had no horizontal overflow. Keyboard Space consent; two-reference job c00bba38d22c; reset during run remained cleared after server completion. Malformed timing input displayed actionable prepare error and disabled Run.
- Full procedure and limitations: docs/evidence/OJ-4rht/DELIVERY.md.

### proof
- [x] AC #1: Responsive source/two-reference previews, labels/focus/keyboard Space, reduced-motion stylesheet.
- [x] AC #2: Explicit unchecked rights gate, guided select/prepare/run/review with disabled explanations.
- [x] AC #3: Server states only, unknown health not free/local, dry_run explicitly no AI inference.
- [x] AC #4: Complete job shows final/paired review and real artifact links; paired download byte-hash verified.
- [x] AC #5: Inline errors and retry/reset; epoch/job snapshots, abort, URL revocation and text-safe API rendering. Browser reset race exercised; broader permutations reserved for dependent regression story.
- [x] AC #6: Backend unchanged, 31 baseline tests pass, real browser smoke and screenshot hashes saved.

### LEARNINGS
- Form control id reset shadows form.reset; use the prototype method. Browser smoke exposed and verified this repair.

### OBSERVATIONS
- No live inference/GPU/paid calls. No formal screen-reader or exhaustive race-suite claim. User judges aesthetics; independent PM acceptance remains required. Preview loopback 8892 remains running for review.

### 2026-10-18T02:31:40Z speed
## PM Decision
REJECTED [2026-10-17]: Delivery/contract gaps; no confirmed user-facing async-state source defect from this bounded review.

EXPECTED: Exact AC-by-AC proof for all eight story criteria and successful delivery preflight.
DELIVERED: verify-delivery reports 8 passed, 1 failed (proof:ac_items). Receipt has six AC numbers with meanings shifted after AC3; AC7 and AC8 are not mapped separately.
GAP: A green backend suite and broad narrative do not satisfy the exact acceptance proof gate.
FIX: Correct the delivery receipt to map all eight actual AC, include literal commands/current implementation SHA, and rerun verify-delivery successfully without bypass. Preserve history and verify the authoritative last contract.

EXPECTED: Boundary map accurately describes PRODUCES and downstream CONSUMES.
DELIVERED: studio.js:159-160 exposes read-only getState/errorText, not the four mutable methods named in OJ-4rht; OJ-yf2c consumes two nonexistent methods.
GAP: Tracker interface contract contradicts implementation and dependent work.
FIX: Sr PM/coordinator must explicitly reconcile both boundary maps with private helpers/read-only observation and user-driven regression tests. Do not add unsafe mutation seams just to satisfy stale tracker text.

EXPECTED: Testing requirements include browser keyboard traversal, visible focus, and prefers-reduced-motion check.
DELIVERED: DELIVERY.md records Space on consent and responsive widths; reduced motion is asserted from CSS, with no browser preference/check result recorded.
GAP: Full specified manual check is not evidenced. Broader deterministic coverage remains OJ-yf2c scope.
FIX: Perform and record bounded keyboard traversal/visible-focus and reduced-motion browser checks against the real local UI; no new dependency or live inference required.

EXPECTED: PM warning ownership requires a DISCOVERED_BUG report rather than dismissing baseline warnings.
DELIVERED: pytest.txt has 31 passed, 1 Starlette/httpx deprecation warning, described only as existing.
GAP: Warning is acknowledged but not tracked in the required structured report.
FIX: Add a DISCOVERED_BUG block for centralized triage; do not expand this frontend story into backend/dependency changes.

## nd_contract
status: rejected

### evidence
- Reviewed story/OJ-4rht at 63b9c005e64fcfa0bdba04ee798acaedd79450e7; source readonly, no merge or commits.
- Read both OJ-4rht and OJ-yf2c native tracker bodies, actual source, desktop/mobile screenshots, DELIVERY.md and pytest.txt.
- node --check app/web/studio.js and git diff --check exit 0.
- pvg story verify-delivery OJ-4rht: 8 passed, 1 failed, proof:ac_items.
- Recorded suite evidence: 31 passed, 1 warning in 11.08s; no redundant suite rerun during PM review.
- Async invalidation checks epoch/job snapshots after await, aborts requests on reset/input, clears artifacts; no confirmed race defect in static pass. No exhaustive race claim.

### proof
- [ ] AC #1: Browser focus/traversal/reduced-motion verification evidence incomplete.
- [ ] AC #2-8: Exact eight-item authoritative delivery proof and boundary reconciliation required.

## Dogfood Rework Addendum (2026-10-17 intake)
- Owner approved adding the measured portrait intrinsic-sizing defect to this existing rework. Original AC #1-8 remain exactly as written above; AC #9 is additive.
- Current frontend reference: story/OJ-4rht `63b9c00`, `app/web/studio.js:14-16` and `159-160`; `app/web/styles.css:3` is minified and contains the fixed-height/overflow reference preview rule implicated by the dogfood measurement.
- Current measured evidence is `../frontend-evidence/dogfood-20261017/live/REPORT.md` and `browser-playback.json`. No repair test result is claimed by this intake.
- Preserve the prior PM rejection and every earlier delivery/decision block. A later authoritative contract may supersede proof details but must map all nine AC explicitly.

## nd_contract
status: in_progress

### evidence
- 2026-10-17 bounded dogfood intake reconciled the boundary map with the actual read-only public seam and added owner-approved AC #9 without releasing the current developer claim.

### proof
- [ ] AC #1: Responsive cinematic studio with complete source/reference previews and accessible controls.
- [ ] AC #2: Guided upload/prepare/run flow preserves manually checked rights consent.
- [ ] AC #3: Only truthful API-backed stage states are displayed.
- [ ] AC #4: Dry-run no-AI-inference disclosure is backend-conditional.
- [ ] AC #5: Complete source/result compare and real artifact downloads work.
- [ ] AC #6: Errors and stale jobs are visible and recoverable.
- [ ] AC #7: Static vanilla boundary, backend/API/generation preservation, no new dependency, and baseline suite pass.
- [ ] AC #8: Real loopback dry-run browser smoke uses the actual API endpoints with no external service or credential.
- [ ] AC #9: Portrait and landscape performer previews preserve complete intrinsic geometry without clipping.


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

## Acceptance Criteria


## Design


## Notes
Routing recovery: GLM native worker stopped after repeated provider status502 stream failures; git status in story worktree clean and branch still7ab3b8c. Router activity confirmed no active old request before replacement. Fresh worker qwen_frontend_4rht routed exactly custom/Qwen-Ambassador/Qwen3.8-Max (not modelscope), same claimed isolated story. Implementation pending; no source changes or tests claimed.
User explicitly requested GPT-6 Astra frontend replacement. Qwen stopped, router activity empty, story worktree clean at7ab3b8c before replacement. Recreated clean Paivot-owned worktree on existing story branch. Fresh Astra bounded frontend-only task dispatched; medium effort, no delegation. Local commits only, backend/generation untouched; independent acceptance pending.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-17.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence
Summary: Cinematic static studio implemented, real browser smoke passed; independent acceptance pending.
Commit SHA: 90ec73d

### CI/Test Results
Commands run:
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q
- git diff --check
- node --check app/web/studio.js

## nd_contract
status: delivered

### evidence
- Implementation b5fd8e4; browser fix/evidence 90ec73d on story/OJ-4rht.
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q: 31 passed, 1 existing warning in 11.08s. docs/evidence/OJ-4rht/pytest.txt.
- git diff --check and node --check app/web/studio.js: exit 0.
- CUA browser real synthetic dry-run job 3af79afdac1c completed with source, final, paired videos and artifact links; paired download SHA256 eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9 matches server artifact.
- docs/evidence/OJ-4rht/desktop-review.jpg SHA256 e1129e68d907e0b8bd7f039334c4f55e1cae0d146f3fb73c1deeb43a1415c9db.
- docs/evidence/OJ-4rht/mobile-review.jpg SHA256 5839db2d82d46cb44dd5eb5bfa395a48ffcd17023a3691a7fa01b2ad829db082.
- Widths 375/414/768/1024/1440 had no horizontal overflow. Keyboard Space consent; two-reference job c00bba38d22c; reset during run remained cleared after server completion. Malformed timing input displayed actionable prepare error and disabled Run.
- Full procedure and limitations: docs/evidence/OJ-4rht/DELIVERY.md.

### proof
- [x] AC #1: Responsive source/two-reference previews, labels/focus/keyboard Space, reduced-motion stylesheet.
- [x] AC #2: Explicit unchecked rights gate, guided select/prepare/run/review with disabled explanations.
- [x] AC #3: Server states only, unknown health not free/local, dry_run explicitly no AI inference.
- [x] AC #4: Complete job shows final/paired review and real artifact links; paired download byte-hash verified.
- [x] AC #5: Inline errors and retry/reset; epoch/job snapshots, abort, URL revocation and text-safe API rendering. Browser reset race exercised; broader permutations reserved for dependent regression story.
- [x] AC #6: Backend unchanged, 31 baseline tests pass, real browser smoke and screenshot hashes saved.

### LEARNINGS
- Form control id reset shadows form.reset; use the prototype method. Browser smoke exposed and verified this repair.

### OBSERVATIONS
- No live inference/GPU/paid calls. No formal screen-reader or exhaustive race-suite claim. User judges aesthetics; independent PM acceptance remains required. Preview loopback 8892 remains running for review.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Implementation b5fd8e4; browser fix/evidence 90ec73d on story/OJ-4rht.
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q: 31 passed, 1 existing warning in 11.08s. docs/evidence/OJ-4rht/pytest.txt.
- git diff --check and node --check app/web/studio.js: exit 0.
- CUA browser real synthetic dry-run job 3af79afdac1c completed with source, final, paired videos and artifact links; paired download SHA256 eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9 matches server artifact.
- docs/evidence/OJ-4rht/desktop-review.jpg SHA256 e1129e68d907e0b8bd7f039334c4f55e1cae0d146f3fb73c1deeb43a1415c9db.
- docs/evidence/OJ-4rht/mobile-review.jpg SHA256 5839db2d82d46cb44dd5eb5bfa395a48ffcd17023a3691a7fa01b2ad829db082.
- Widths 375/414/768/1024/1440 had no horizontal overflow. Keyboard Space consent; two-reference job c00bba38d22c; reset during run remained cleared after server completion. Malformed timing input displayed actionable prepare error and disabled Run.
- Full procedure and limitations: docs/evidence/OJ-4rht/DELIVERY.md.

### proof
- [x] AC #1: Responsive source/two-reference previews, labels/focus/keyboard Space, reduced-motion stylesheet.
- [x] AC #2: Explicit unchecked rights gate, guided select/prepare/run/review with disabled explanations.
- [x] AC #3: Server states only, unknown health not free/local, dry_run explicitly no AI inference.
- [x] AC #4: Complete job shows final/paired review and real artifact links; paired download byte-hash verified.
- [x] AC #5: Inline errors and retry/reset; epoch/job snapshots, abort, URL revocation and text-safe API rendering. Browser reset race exercised; broader permutations reserved for dependent regression story.
- [x] AC #6: Backend unchanged, 31 baseline tests pass, real browser smoke and screenshot hashes saved.

### LEARNINGS
- Form control id reset shadows form.reset; use the prototype method. Browser smoke exposed and verified this repair.

### OBSERVATIONS
- No live inference/GPU/paid calls. No formal screen-reader or exhaustive race-suite claim. User judges aesthetics; independent PM acceptance remains required. Preview loopback 8892 remains running for review.

## nd_contract
status: in_progress

### evidence
- Claimed atomically by dispatcher; story/OJ-4rht worktree created from epic/OJ-a7l6 at 7ab3b8c.
- User explicitly authorized local commits and merges only. No remote configured.
- Backlog repaired through native restore/edit/sync; local API does not require secret provisioning.

### proof
- [ ] AC #1-8: Implementation and browser acceptance pending.

## History
- 2026-10-18T01:53:57Z dep_added: blocks OJ-yf2c
- 2026-10-18T01:57:44Z status: open -> in_progress
- 2026-10-18T01:57:44Z claimed by dev-OJ-4rht
- 2026-10-18T02:27:57Z status: in_progress -> in_progress
- 2026-10-18T02:31:39Z status: in_progress -> open
- 2026-10-18T02:31:40Z released by speed
- 2026-10-18T03:47:31Z status: open -> in_progress
- 2026-10-18T03:47:31Z claimed by dev-OJ-4rht
- 2026-10-18T04:00:26Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]

## Comments


Tracker receipt normalization: existing developer proof copied to the end; independent acceptance is still pending. No history removed.

## Implementation Evidence
Summary: Cinematic static studio implemented, real browser smoke passed; independent acceptance pending.
Commit SHA: 90ec73d

### CI/Test Results
Commands run:
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q
- git diff --check
- node --check app/web/studio.js

## nd_contract
status: delivered

### evidence
- Implementation b5fd8e4; browser fix/evidence 90ec73d on story/OJ-4rht.
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q: 31 passed, 1 existing warning in 11.08s. docs/evidence/OJ-4rht/pytest.txt.
- git diff --check and node --check app/web/studio.js: exit 0.
- CUA browser real synthetic dry-run job 3af79afdac1c completed with source, final, paired videos and artifact links; paired download SHA256 eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9 matches server artifact.
- docs/evidence/OJ-4rht/desktop-review.jpg SHA256 e1129e68d907e0b8bd7f039334c4f55e1cae0d146f3fb73c1deeb43a1415c9db.
- docs/evidence/OJ-4rht/mobile-review.jpg SHA256 5839db2d82d46cb44dd5eb5bfa395a48ffcd17023a3691a7fa01b2ad829db082.
- Widths 375/414/768/1024/1440 had no horizontal overflow. Keyboard Space consent; two-reference job c00bba38d22c; reset during run remained cleared after server completion. Malformed timing input displayed actionable prepare error and disabled Run.
- Full procedure and limitations: docs/evidence/OJ-4rht/DELIVERY.md.

### proof
- [x] AC #1: Responsive source/two-reference previews, labels/focus/keyboard Space, reduced-motion stylesheet.
- [x] AC #2: Explicit unchecked rights gate, guided select/prepare/run/review with disabled explanations.
- [x] AC #3: Server states only, unknown health not free/local, dry_run explicitly no AI inference.
- [x] AC #4: Complete job shows final/paired review and real artifact links; paired download byte-hash verified.
- [x] AC #5: Inline errors and retry/reset; epoch/job snapshots, abort, URL revocation and text-safe API rendering. Browser reset race exercised; broader permutations reserved for dependent regression story.
- [x] AC #6: Backend unchanged, 31 baseline tests pass, real browser smoke and screenshot hashes saved.

### LEARNINGS
- Form control id reset shadows form.reset; use the prototype method. Browser smoke exposed and verified this repair.

### OBSERVATIONS
- No live inference/GPU/paid calls. No formal screen-reader or exhaustive race-suite claim. User judges aesthetics; independent PM acceptance remains required. Preview loopback 8892 remains running for review.

### 2026-10-18T02:31:40Z speed
## PM Decision
REJECTED [2026-10-17]: Delivery/contract gaps; no confirmed user-facing async-state source defect from this bounded review.

EXPECTED: Exact AC-by-AC proof for all eight story criteria and successful delivery preflight.
DELIVERED: verify-delivery reports 8 passed, 1 failed (proof:ac_items). Receipt has six AC numbers with meanings shifted after AC3; AC7 and AC8 are not mapped separately.
GAP: A green backend suite and broad narrative do not satisfy the exact acceptance proof gate.
FIX: Correct the delivery receipt to map all eight actual AC, include literal commands/current implementation SHA, and rerun verify-delivery successfully without bypass. Preserve history and verify the authoritative last contract.

EXPECTED: Boundary map accurately describes PRODUCES and downstream CONSUMES.
DELIVERED: studio.js:159-160 exposes read-only getState/errorText, not the four mutable methods named in OJ-4rht; OJ-yf2c consumes two nonexistent methods.
GAP: Tracker interface contract contradicts implementation and dependent work.
FIX: Sr PM/coordinator must explicitly reconcile both boundary maps with private helpers/read-only observation and user-driven regression tests. Do not add unsafe mutation seams just to satisfy stale tracker text.

EXPECTED: Testing requirements include browser keyboard traversal, visible focus, and prefers-reduced-motion check.
DELIVERED: DELIVERY.md records Space on consent and responsive widths; reduced motion is asserted from CSS, with no browser preference/check result recorded.
GAP: Full specified manual check is not evidenced. Broader deterministic coverage remains OJ-yf2c scope.
FIX: Perform and record bounded keyboard traversal/visible-focus and reduced-motion browser checks against the real local UI; no new dependency or live inference required.

EXPECTED: PM warning ownership requires a DISCOVERED_BUG report rather than dismissing baseline warnings.
DELIVERED: pytest.txt has 31 passed, 1 Starlette/httpx deprecation warning, described only as existing.
GAP: Warning is acknowledged but not tracked in the required structured report.
FIX: Add a DISCOVERED_BUG block for centralized triage; do not expand this frontend story into backend/dependency changes.

## nd_contract
status: rejected

### evidence
- Reviewed story/OJ-4rht at 63b9c005e64fcfa0bdba04ee798acaedd79450e7; source readonly, no merge or commits.
- Read both OJ-4rht and OJ-yf2c native tracker bodies, actual source, desktop/mobile screenshots, DELIVERY.md and pytest.txt.
- node --check app/web/studio.js and git diff --check exit 0.
- pvg story verify-delivery OJ-4rht: 8 passed, 1 failed, proof:ac_items.
- Recorded suite evidence: 31 passed, 1 warning in 11.08s; no redundant suite rerun during PM review.
- Async invalidation checks epoch/job snapshots after await, aborts requests on reset/input, clears artifacts; no confirmed race defect in static pass. No exhaustive race claim.

### proof
- [ ] AC #1: Browser focus/traversal/reduced-motion verification evidence incomplete.
- [ ] AC #2-8: Exact eight-item authoritative delivery proof and boundary reconciliation required.

