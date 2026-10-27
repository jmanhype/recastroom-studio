---
id: OJ-0ij6
title: "Keep selected project hidden fields synchronized across form reset"
status: closed
priority: 0
type: bug
labels: [studio, foundation, local, no-spend, delivered, accepted]
parent: OJ-mnrv
created_at: 2026-10-27T08:47:01Z
created_by: speed
updated_at: 2026-10-27T09:29:41Z
content_hash: "sha256:07b8540c67eafe324f93946d4396b9edd1e12ce9c19a268010736f4f6b1176b9"
assignee: dev-OJ-0ij6
follows: [OJ-r6n5, OJ-m439]
closed_at: 2026-10-27T09:29:41Z
close_reason: "Accepted: Independent review verified the exact two-file f45521d delivery, real-JS reset regressions across no-character/saved-character/no-project modes, FormData and no-run behavior, and separate real API/temp-SQLite preservation evidence. Required test/syntax/compile/verify/gate results and warnings are complete; browser capstone remains OJ-wfpy."
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
## Implementation Evidence

### CI/Test Results
Commands run:
- Focused pytest: 4 passed, 1 known warning.
- Full pytest: 185 passed, 1 known warning.
- Node syntax check: PASS.
- Python compileall: PASS.
- pvg verify: PASS, 2 files / 0 issues.
- pvg gates: PASS, 1 disclosed managed complexity warning / 0 skipped.

Summary: AC regressions and real API/store preservation pass; the only test warning is the known Starlette/httpx deprecation.
Commit SHA: f45521def3fc9a811759c6fbedee35d2b62cbde2

### AC Verification
| AC # | Requirement | Status |
|---|---|---|
| 1 | Real-JS no-character reset preserves/synchronizes project A | PASS |
| 2 | Real-JS saved-character reset clears transient selection and preserves project A | PASS |
| 3 | FormData projects project A with uploads and request log has no run | PASS |
| 4 | Real API/store records and artifacts survive reset | PASS |
| 5 | Upload-only/no-project behavior remains empty/unrecorded | PASS |
| 6 | Required tests and touched gates pass with warning disclosed | PASS |

LEARNINGS:
- Native form reset clears hidden inputs before the projects reset listener runs, so synchronization must be unconditional after transient character cleanup.

OBSERVATIONS:
- The known Starlette/httpx warning and managed renderHistory complexity warning remain disclosed; gates pass.

## nd_contract
status: delivered

### evidence
- Commit SHA: f45521def3fc9a811759c6fbedee35d2b62cbde2
- Focused 4 passed / 1 known warning; full 185 passed / 1 known warning; syntax and compileall PASS.
- pvg verify PASS; pvg gates PASS with one disclosed managed warning.

### proof
- [x] AC #1: PASS
- [x] AC #2: PASS
- [x] AC #3: PASS
- [x] AC #4: PASS
- [x] AC #5: PASS
- [x] AC #6: PASS


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

### CI/Test Results
Commands run:
- Baseline before edits: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q tests/test_project_frontend.py`
- Base regression probe with the new Node VM harness against `fdc9130:app/web/projects.js`: before hidden project `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`; after reset hidden project empty while UI project stayed `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`; `/run` request list `[]`.
- Focused: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q tests/test_project_frontend.py`
- Full: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q`
- JS syntax: `/opt/homebrew/opt/node@22/bin/node --check app/web/projects.js`
- Python compile: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m compileall -q app/web/projects.js tests/test_project_frontend.py`
- Touched verify: `pvg verify app/web/projects.js tests/test_project_frontend.py --format=text`
- Touched gates: `pvg gates app/web/projects.js tests/test_project_frontend.py --format text`

Summary:
- Baseline focused: 2 passed, 1 known Starlette/httpx deprecation warning.
- Final focused: 4 passed, 1 known Starlette/httpx deprecation warning.
- Full suite: 185 passed, 1 known Starlette/httpx deprecation warning (baseline expectation was 183 passed).
- JS syntax PASS; compileall PASS.
- `pvg verify`: `VERIFY: PASSED (2 files scanned, 0 issues)`.
- `pvg gates`: `GATES: PASS (1 warn, 0 skipped)`; disclosed pre-existing complexity warning `renderHistory 19>15` at `app/web/projects.js:127`.
- The real-JS Node VM/Fake DOM/Fake fetch/Fake localStorage harness is frontend unit proof only. Record preservation uses the real FastAPI app, real `WorkspaceStore`, temporary SQLite/workspace, and synthetic media fixtures; neither store nor API is mocked in that case.

Commit SHA: `f45521def3fc9a811759c6fbedee35d2b62cbde2`

Hashes:
- `app/web/projects.js`: `b68fe9ff202c617c81daeec9864eef5817cb81132be5b4b9e35cb2c2a7a2b3b9`
- `tests/test_project_frontend.py`: `e61f62b56414c71976af263020d2e43bc10180056408b89b2f8b0202871ae84f`

Diff budget: 2 files, 187 insertions / 2 deletions (189 changed LOC, under 200).

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | Real JS VM, project A/no character keeps UI project A, state project A, hidden project A, and empty character fields after reset | `app/web/projects.js:303-305` | `tests/test_project_frontend.py:22-119,239-266` | PASS |
| 2 | Real JS VM with saved character clears transient character/reference selection, restores upload usability, and preserves/synchronizes project A | `app/web/projects.js:303-306` | `tests/test_project_frontend.py:54-76,87-108,239-266` | PASS |
| 3 | Reset no-character FormData carries `project_id=A` plus uploaded source/primary reference, no character fields, and request log has no `/run` | `app/web/projects.js:303-305` | `tests/test_project_frontend.py:100-107,259-266` | PASS |
| 4 | Real API/store records, immutable character, protected bytes, history, artifacts, and job status are byte/equivalent-preserved around frontend reset | `app/web/projects.js:303-306` | `tests/test_project_frontend.py:269-315` | PASS |
| 5 | Upload-only/no-project mode keeps project and character hidden fields empty and invents no history | `app/web/projects.js:303-305` | `tests/test_project_frontend.py:27,242-266` | PASS |
| 6 | Focused/full tests, syntax, compileall, verify, and touched gates pass; known warning disclosed | `app/web/projects.js`, `tests/test_project_frontend.py` | Commands and summaries above | PASS |

LEARNINGS:
- The failure is exactly an early-return path: native reset cleared hidden inputs, but selected project state survived only in the visible select and `ProjectsUI`.
- Executing the real script in Node VM caught the desynchronization that static source assertions missed; retaining before/after snapshots also documents the visible/hidden split.
- Node `process.argv` for `node -e script arg1 arg2` exposes the source path at `argv[1]` and mode at `argv[2]`; this differs from the more familiar script-file argv layout.
- Frontend reset itself is non-mutating; exact real API/store snapshots before and after it are sufficient to prove persistence without launching a browser or running a job.

OBSERVATIONS:
- The known Starlette/httpx deprecation warning remains and is not suppressed.
- `pvg gates` reports the managed pre-existing `renderHistory` complexity warning but passes. No broad UI refactor was made outside this bug's two-file budget.

## nd_contract
status: delivered

### evidence
- Commit `f45521def3fc9a811759c6fbedee35d2b62cbde2` on `story/OJ-0ij6`.
- Focused 4 passed / 1 known warning; full 185 passed / 1 known warning; JS syntax and compileall PASS.
- `pvg verify` PASS; `pvg gates` PASS with one disclosed managed complexity warning.

### proof
- [x] AC #1: Real-JS no-character reset synchronizes project A across UI, state, and hidden field.
- [x] AC #2: Real-JS saved-character reset clears transient character/reference state while preserving project A.
- [x] AC #3: Reset FormData projects `project_id=A`, accepts uploaded source/reference, omits character fields, and logs no `/run`.
- [x] AC #4: Real API/store project, immutable character, protected bytes, history, artifacts, and job status are unchanged.
- [x] AC #5: No-project mode remains upload-only with empty hidden IDs and no invented history.
- [x] AC #6: Required focused/full/syntax/compile/verify/gate checks passed with the known warning disclosed.


## nd_contract\nstatus: in_progress\n\n### evidence\n- 2026-10-27: resumed claimed story in story/OJ-0ij6 at base fdc9130; reading exact source/tests before edits.\n\n### proof\n- [ ] AC #1: pending.\n- [ ] AC #2: pending.\n- [ ] AC #3: pending.\n- [ ] AC #4: pending.\n- [ ] AC #5: pending.\n- [ ] AC #6: pending.

## History
- 2026-10-27T08:50:21Z dep_added: blocks OJ-wfpy
- 2026-10-27T08:54:27Z status: open -> in_progress
- 2026-10-27T08:54:27Z auto-follows: linked to predecessor OJ-r6n5
- 2026-10-27T08:54:27Z claimed by dev-OJ-0ij6
- 2026-10-27T09:19:53Z status: in_progress -> in_progress
- 2026-10-27T09:19:53Z auto-follows: linked to predecessor OJ-m439
- 2026-10-27T09:29:41Z status: in_progress -> closed
- 2026-10-27T09:29:41Z dep_removed: no_longer_blocks OJ-wfpy

## Links
- Parent: [[OJ-mnrv]]
- Follows: [[OJ-r6n5]], [[OJ-m439]]

## Comments

### 2026-10-27T09:23:02Z speed
## nd_contract
status: delivered

### evidence
- Commit SHA: f45521def3fc9a811759c6fbedee35d2b62cbde2
- Focused pytest 4 passed / 1 known warning; full pytest 185 passed / 1 known warning.
- Node syntax, Python compileall, pvg verify, and pvg gates PASS; the managed complexity warning is disclosed.
- Detailed evidence is in the Implementation Evidence note on this story.

### proof
- [x] AC #1: PASS
- [x] AC #2: PASS
- [x] AC #3: PASS
- [x] AC #4: PASS
- [x] AC #5: PASS
- [x] AC #6: PASS

