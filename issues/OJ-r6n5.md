---
id: OJ-r6n5
title: "Keep selected project hidden fields synchronized across form reset"
status: closed
priority: 0
type: bug
labels: [studio, foundation, local, no-spend]
parent: OJ-mnrv
created_at: 2026-10-27T08:48:10Z
created_by: speed
updated_at: 2026-10-27T08:52:37Z
content_hash: "sha256:66232f5ce95f673c5a2d08bf98b0c455b5d46578efb4e4d44cae9072dbdac0ba"
closed_at: 2026-10-27T08:52:37Z
close_reason: "Duplicate of canonical OJ-0ij6; concurrent late metadata creation only, not implemented or accepted. Preserve OJ-0ij6 for the reset fix."
---

## Description
## Description
Accepted OJ-5uq4 leaves the visible saved-project selection active after the studio form resets, but its hidden `project_id` field can be empty. A later source plus uploaded-reference prepare is then treated as upload-only and is silently omitted from the selected project's saved history. This blocks the OJ-wfpy restart/history capstone.

## Root Cause
At capstone commit `84d52ce06a3e51f34b8f962462828922f76bf31f`:
- `app/web/projects.js:45-49` synchronizes `project-id-input`, `character-id-input`, and `character-version-input` from the module's selected state.
- `app/web/projects.js:173-196` keeps `selectedProjectId` active and dispatches selection state whenever a project is selected.
- `app/web/studio.js:275-279` calls `HTMLFormElement.prototype.reset.call(form)` and then emits `studio:reset`.
- `app/web/projects.js:303-307` receives that event but returns immediately when `!selectedCharacterId`; it never calls `syncHiddenFields()` in the selected-project/no-character mode.
- Consequently native form reset empties the hidden project field while the project select still displays project A. The next source/uploaded-reference FormData no longer contains `project_id`, so the accepted connected prepare path records no project history.

Read-only Node VM evidence supplied by upstream review loaded the actual JS: before reset, UI project and hidden project were both `A`; after actual form reset plus `studio:reset`, UI remained `A` while the hidden field was `''`. A local temporary VM probe did not add a finding beyond this supplied evidence and was abandoned after harness-only setup errors; it did not modify source or tracker state.

## USER INTENT
Resetting transient media/character choices must return the user to a clean upload form without erasing the identity of the still-selected saved project. The next prepare must preserve the user's visible context and recorded project history rather than silently become upload-only.

## Affected Components / DIFF BUDGET
- `app/web/projects.js` — synchronize project/character hidden fields on every `studio:reset` event.
- `tests/test_project_frontend.py` — actual-JS DOM regression plus preserved-history checks.

Exactly 2 files, under 200 changed LOC. A gross overrun is mandatory PM investigation, not automatic rejection.

## Boundary Map
PRODUCES:
- `app/web/projects.js` -> `studio:reset` handling that always calls the existing hidden-field synchronization path after the existing form reset.
  spec: after reset, `project-id-input.value === selectedProjectId`; character fields are empty when no character is selected and are synchronized/cleared through the existing character-state path when one was selected.
- `tests/test_project_frontend.py` -> actual loaded-JS Node DOM VM regressions for no-character and saved-character reset modes, plus real integration assertions that project records/history/jobs remain preserved.

CONSUMES:
- OJ-5uq4: `app/web/projects.js` -> connected project/character selection and hidden form-field integration.
  spec: `window.ProjectsUI.getState()` returns `{projectId: string, characterId: string, characterVersion: number, requestEpoch: number}`; `getReferenceState()` returns `{ready: boolean, references: Array<object>}`; selection emits `projects:selection-change` and consumes `studio:reset`.
- (existing): `app/web/studio.js` -> native form reset followed by `document.dispatchEvent(new CustomEvent('studio:reset'))`.
  source: `HTMLFormElement.prototype.reset.call(form)` clears hidden inputs before the event; run remains explicitly manual.

## Acceptance Criteria
1. A regression loads the real `app/web/projects.js` in a pure Node DOM VM and executes behavior, not substring assertions. In selected-project/no-character mode, after native-equivalent form reset plus `studio:reset`, the project select and `window.ProjectsUI.getState().projectId` remain project A and `project-id-input.value` is also A; character ID/version hidden fields are empty.
2. The same real-JS regression covers selected project A plus a saved selected character. Reset clears transient character/reference selection, makes uploaded references usable again, keeps project A selected and its hidden field synchronized to A, and blanks character ID/version fields. Both AC #1 and AC #2 must assert state after event dispatch, not merely search source text.
3. A FormData built from the reset no-character form includes `project_id=A` and allows an uploaded primary reference; it contains no character ID/version. The test does not invoke `/run` and proves no automatic run request.
4. Real API/store integration around the reset path preserves existing projects, immutable character versions, protected reference bytes, prepared history, job artifacts, and server job records. Reset may clear only transient form selection/media state; it must not delete or rewrite records/history/jobs.
5. Existing upload-only behavior remains valid: when no project is selected, hidden project/character fields remain empty and no project history is invented.
6. Focused frontend test, full suite, JS syntax check, compileall, and touched gates pass using the existing temporary workspace/SQLite/synthetic fixtures. The known Starlette/httpx warning must be disclosed, not suppressed.

## Testing Requirements
- Focused: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m pytest -q tests/test_project_frontend.py`.
- Full: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m pytest -q`.
- JS syntax: `/opt/homebrew/opt/node@22/bin/node --check app/web/projects.js`.
- Compile: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m compileall -q app/web/projects.js tests/test_project_frontend.py`.
- Gates: `pvg gates app/web/projects.js tests/test_project_frontend.py --format text`.
- The pure DOM VM harness may supply deterministic `document`, event, `fetch`, and `localStorage` seams to execute the actual JS, but it is a frontend unit only and must not be described as browser, infrastructure, API, or store proof. Required record/history preservation assertions must use the real API/store without a mock replacing either.
- Baseline expectation is 183 passing tests plus the one known warning before this work; record the actual new counts and exact `LEARNINGS:` and `OBSERVATIONS:` sections.

## Discovered During
Independent capstone review of accepted story OJ-5uq4 at held commit `84d52ce06a3e51f34b8f962462828922f76bf31f`, before OJ-wfpy browser completion. OJ-5uq4 remains accepted; this child tracks the newly found regression without reopening or rewriting its historical contract.

## OUT OF SCOPE
- `app/main.py`, `app/project_api.py`, `app/web/studio.js`, `app/web/index.html`, styles, store, pipeline, and unrelated frontend cleanup: outside this bug's exact ownership and required to remain unchanged.
- Browser/infrastructure certification: OJ-wfpy owns the actual E2E journey after both P0 fixes.
- Any automatic run, provider/GPU call, network collection, key use, push, or publication.

## MANDATORY SKILLS
- developer — owns the bounded implementation and delivery evidence.
- codebase-memory — verifies current brownfield paths, APIs, and call relationships before edits.
- pm_acceptor — performs independent evidence-based acceptance; implementation cannot self-accept.

## nd_contract
status: new

### evidence
- Created: 2026-10-27 by SrPM bug triage from the supplied real-JS finding at `84d52ce`.
- Source review confirmed the early return and reset-to-hidden-field desynchronization; no fix has been applied.

### proof
- [ ] Pending implementation and independent PM verification of AC #1-#6.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-27T08:52:37Z status: open -> closed

## Links
- Parent: [[OJ-mnrv]]

## Comments
