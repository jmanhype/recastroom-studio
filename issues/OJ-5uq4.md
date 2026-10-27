---
id: OJ-5uq4
title: "Connect saved projects to the existing studio flow"
status: in_progress
priority: 1
type: feature
labels: [studio, foundation, local, no-spend]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:28Z
created_by: speed
updated_at: 2026-10-27T07:10:33Z
content_hash: "sha256:c596604683b9bfca906639527a34b808b16d1871c9690c9b557d42894bf7d79d"
blocks: [OJ-wfpy]
was_blocked_by: [OJ-6xh3, OJ-8zaw]
follows: [OJ-6xh3, OJ-8zaw]
assignee: dev-OJ-5uq4
---
## Description
Connect saved projects and reusable character versions to the existing browser prepare/review path using the store delivered by OJ-6xh3. Do not create an unrelated demo UI or new renderer.

## USER INTENT
A creator can choose a saved project and character version, upload a source, prepare the existing C1 workflow using those stored references, reload and find the project's prepared jobs/configuration again.

## Ownership / DIFF BUDGET
NEW app/project_api.py, NEW app/web/projects.js; additive edits app/main.py, app/web/index.html, app/web/studio.js and app/web/styles.css (all verified at main c2a18a5); NEW tests/test_projects_api.py and tests/test_project_frontend.py. Approximately 8-9 files, under 1100 changed LOC including tests. Consumer must not rewrite workspace_store.py's API without separate review.

## API/UI contract
Add same-app /api/projects POST/GET and /api/projects/{project_id} GET; /api/projects/{project_id}/jobs GET; /api/characters POST multipart project_id,name,description,reference_1 and optional reference_2; /api/characters GET; /api/characters/{character_id}/versions/{version} GET; and /api/assets/{asset_id} GET. Character multipart reference files are staged by WorkspaceStore.stage_asset(project_id, safe_filename, BinaryIO content, role=...); the asset endpoint streams a preview through WorkspaceStore.resolve_asset(asset_id) using only the recorded opaque server-generated ID, never a caller filesystem path. app/main.py wires WorkspaceStore(SETTINGS.data_dir) into create_project_router(store), while preserving the existing no-project destination SETTINGS.data_dir/uploads/<job_id>. Requests accept no filesystem path/root and responses expose no server path; actionable 404/409/422 errors are returned. Responses use the store's safe projections.
Existing /api/prepare gains optional project_id,character_id,character_version. Preserve old upload-only clients. A saved version supplies the same one-performer primary/secondary references that already exist; it does NOT represent two-person recasting. If saved-character selection and uploaded references conflict, return an explicit 422 rather than silently substitute. Validation occurs before queuing/generation and missing saved assets fail clearly. Preserve source upload, seed, words, custom-workflow and current attestation semantics. After successful preparation, record the actual prepared job/configuration link in the selected project. Do not submit inference or change configure_workflow.

### Functional acceptance
1. Real API tests create/list/reopen a project, safely stage a synthetic multipart reference bundle through the public store API, prepare with its saved version without re-uploading references, and obtain a saved job/configuration link. They also verify WorkspaceStore(SETTINGS.data_dir) router wiring and compatibility with the existing no-project SETTINGS.data_dir/uploads/<job_id> destination. Verify the actual emitted workflow uses the selected filenames and seed with current C1 constants unchanged.
2. The existing page displays a usable project selector, character library/version choice, safe asset-ID previews, and prepared job links that participate in the existing form. Reload restores the chosen project and server-backed history; switching projects cannot show a stale response as the new project's job.
3. A second project can reuse the pinned character version without inheriting unrelated jobs. Creating a new version or resetting the form leaves prior versions, prepared configuration, original files and running server jobs intact.
4. Legacy no-project upload clients and existing prepare/run/status/artifact/workflow/prompt routes retain their accepted behavior. No automatic run on import, selection, reload or preparation; no new provider, queue or consent-verification claim.
5. Invalid project/version/asset IDs, conflicting references, missing files and changed protected inputs yield actionable errors. Asset previews resolve only recorded IDs through the public store accessor; public JSON/browser links contain no raw paths or credentials. Test request/response races and labels using real browser-visible state, not fabricated progress.
6. Focus, keyboard access and reduced-motion behavior remain usable. Existing workflow, media and readiness suites remain green; frontend JS syntax checks pass. Source-photo inputs in tests are synthetic, not a fake production keeper.

PRODUCES:
- app/project_api.py -> create_project_router(store: WorkspaceStore) -> APIRouter with the endpoint contract above.
- app/web/projects.js -> project/reference selection, safe previews, and server-backed history integrated with the existing form.
- app/main.py -> additive WorkspaceStore(SETTINGS.data_dir) construction, create_project_router(store) wiring, and optional project/character-aware prepare flow, not renderer changes.
- tests/test_projects_api.py -> real store/API contract coverage.
- tests/test_project_frontend.py -> browser/form integration, safe-preview, and stale-state regression coverage.
CONSUMES:
- OJ-6xh3: src/openjutsu/workspace_store.py -> WorkspaceStore(root: Path).
  spec: create_project(name: str) -> ProjectRecord; list_projects() -> list[ProjectRecord]; get_project(project_id: str) -> ProjectRecord; register_asset(project_id: str, path: Path, role: str, *, protected: bool = False) -> AssetRecord; stage_asset(project_id: str, filename: str, content: BinaryIO, *, role: str, protected: bool = False) -> AssetRecord; resolve_asset(asset_id: str) -> ResolvedAsset; create_character_version(name: str, reference_asset_ids: list[str], description: str = "") -> CharacterVersionRecord; get_character_version(character_id: str, version: int) -> CharacterVersionRecord; list_character_versions() -> list[CharacterVersionRecord]; record_prepared_job(project_id: str, job_id: str, job_dir: Path, character_version: tuple[str, int] | None = None) -> PreparedConfigRecord; list_prepared_jobs(project_id: str) -> list[PreparedConfigRecord].
  fields: ProjectRecord(project_id,name,created_at,updated_at); AssetRecord(asset_id,project_id,role,filename,media_type,size_bytes,sha256,protected,created_at); CharacterVersionRecord(character_id,version,name,description,reference_asset_ids,created_at); PreparedConfigRecord(project_id,job_id,character_id,character_version,seed,workflow_sha256,prompt_sha256,source_sha256,reference_sha256s,config,created_at); ResolvedAsset(record,path). Call only these typed public methods, not private SQL internals or caller paths.
- (existing): src/openjutsu/pipeline.py -> prepare_workflow(...) -> tuple[PreparedJob, dict[str, Any]].
  spec: prepare_workflow(settings: Settings, *, job_id: str, source: str | Path, reference_1: str | Path, reference_2: str | Path | None, words_path: str | Path | None, rights_attested: bool, identity_description: str | None = None, seed: int = 49, workflow_template: str | Path | None = None) -> tuple[PreparedJob, dict[str, Any]] with current attestation and C1 behavior.
- (existing): app/web/studio.js -> existing epoch/isCurrent request isolation and explicit prepare/run/review flow.
  source: integrate project/character state without overwriting accepted source behavior.

## MANDATORY SKILLS
- developer — owns the bounded implementation and delivery evidence.
- codebase-memory — verifies current brownfield paths, APIs, and call relationships before edits.
- pm_acceptor — performs independent evidence-based acceptance; implementation cannot self-accept.

## Testing requirements
Real temp store plus FastAPI/TestClient integration, safe multipart staging/root-wiring checks, deterministic form/browser regression and existing no-project regression suites. No mocked store and no paid backend. Run focused tests, full pytest, Python compileall, node --check for changed JS, and pvg gates. Preserve the disclosed existing warning rather than weaken assertions.

## Context and hard boundaries
Brownfield RecastRoom at main c2a18a5; current Python/FastAPI/browser app is the base, not a rewrite. Architecture: ../ntm-recastroom-superapp-architecture-20261026/SUPER_APP_BLUEPRINT.md. This epic covers M0 only; scenes, multi-person engines, effects and camera remain later milestones, not rejected scope.
No provider credentials, paid API/GPU/Colab jobs, network collection, push, public deployment, publication or X actions. Use synthetic/temp fixtures for tests; never commit private footage, actual photos, keys, generated keeper media or absolute personal paths. Preserve the pre-existing untracked docs/evidence/recastroom-hook-v6b-keeper/ directory.
Keep existing attestation behavior, C1 graph, source-audio restoration, status and comparison semantics unchanged. Do not market attestation as verified rights. Do not rename or mix C1 and the older BFS/Head0.35 pipeline. New project history is not a claim of renderer recovery, visual QC, generic casting or model inference.
Mandatory skills for execution: developer and codebase-memory; PM review uses pm_acceptor. Use pvg story claim/deliver and append nd_contract evidence; no direct vault edits. Local source commits/merges are authorized after story gates; pushes, remote publication and provider/GPU spending remain prohibited. Developer delivers, independent PM accepts. Follow current repo/global instructions, public type annotations, apply_patch and scope ownership.
Fresh root baseline: env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src .venv/bin/python -m pytest -q =>126 passed,1 existing Starlette/httpx warning; do not suppress tests/warnings or confuse historical results with a new run. Every delivery includes exact LEARNINGS: and OBSERVATIONS: sections, commands/results, artifact paths and hashes where relevant.

## Acceptance Criteria

## Design

## Notes
## Implementation Evidence (DELIVERED)

### CI/Test Results
Commands run:
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m pytest -q tests/test_projects_api.py tests/test_project_frontend.py
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m pytest -q
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m compileall -q app src tests/test_projects_api.py tests/test_project_frontend.py
- /opt/homebrew/opt/node@22/bin/node --check app/web/projects.js
- /opt/homebrew/opt/node@22/bin/node --check app/web/studio.js
- pvg verify app/project_api.py app/main.py app/web/projects.js app/web/studio.js app/web/index.html app/web/styles.css tests/test_projects_api.py tests/test_project_frontend.py --format=text
- pvg gates --changed de71be6 --format text

Summary: focused tests PASS (5 passed, 1 disclosed pre-existing Starlette/httpx warning); full suite PASS (183 passed, same 1 warning); compileall PASS; both JS syntax checks PASS; pvg verify PASS (6 files scanned, 0 issues); pvg gates PASS (0 block, 0 skipped, 5 nonblocking warnings). Gate warnings are _prepare_reference_selection CCN 15, prepare CCN 22, projects.js renderHistory CCN 19, studio.js anonymous CCN 26, and app/main.py 474 non-blank LOC. The original prepare CCN 36>30 blocker was fixed by extracting _prepare_reference_selection before the final full-suite run.

Coverage: not measured; the required virtualenv has no coverage module and external installs are prohibited. No coverage percentage is claimed.

### Browser / CUA Evidence
- Sanctioned path: rendered ChatGPT IAB through mcp__cua_repl.js and its returned Playwright/DOM APIs. IAB visible=true is unsupported in a subagent; CUA rendering worked with the tab background-visible.
- Final-commit loopback dry-run journey used only synthetic_source.mp4 and synthetic_reference.png: project 753f1971a18541c6a26be0c2baa78f30, character char_aac1c2f392700c1bf7f3611b v1, job 625b10e80e50, seed 49, reference synthetic_reference.png. Project/character creation, protected preview, saved-reference prepare without reference re-upload, history links, and no automatic run were visibly verified. Browser console errors/warnings: none.
- Reload/reset journey: reload restored Browser Recovery Project and its selected character/history; reset cleared transient form selection while preserving saved project, library, and job b063fbc63e2a.
- Real race evidence: a 1.5-second delayed history response for project 62e8eb75061a49f5973572229e38fecf (job b063fbc63e2a) was immediately superseded by selecting project 6c23841ce91343e2b3a3c253a7f573e4. At about 100 ms and again after the delayed response completed, Project B visibly remained "No prepared configuration links yet." This is rendered browser evidence, not a source-string assertion.
- Browser receipt SHA-256: 7c9399fe02ca51355f3070ba2ea8957db0c62d2b4927f41a8eaaebc4b0867355. Final journey screenshot SHA-256: ac52a27c7a9bb2936230ce7f84e3a198144fa30afe3d5d1d9c10087f64ad16b3. Race screenshot SHA-256: 63a4d0a2797aac1a96c4558f9e2e9955f73731eadb382bca0e1866e991d1a8c6.
- All three owned IAB tabs and loopback servers were closed/stopped; no listeners remained on ports 8896-8898.

### Commit
Commit SHA: 94c859474c66068824d4788cb07714ea356353ab
Branch: story/OJ-5uq4
Base: de71be6
Diff: exactly the 8 owned files; 1124 insertions, 20 deletions. Worktree clean after commit.

### Wiring
- app/main.py:47-67 constructs WorkspaceStore(SETTINGS.data_dir), keeps it synchronized for project routes, and app/main.py:542 mounts create_project_router.
- app/main.py:138-171 validates saved/upload reference selection; app/main.py:174-266 prepares and records project history without changing run routes.
- app/project_api.py:89-195 exposes the project, character, asset, and safe history endpoints using only public WorkspaceStore methods.
- app/web/projects.js:156-222 guards history responses by request epoch and restores saved selections; app/web/studio.js:57-122 and 264-303 integrate saved-reference readiness, reset, and prepare events.

### AC Verification
| AC # | Requirement | Status |
|---|---|---|
| 1 | Real API root wiring, safe multipart staging, saved-version prepare without re-upload, actual C1 filenames/seed, isolated history, no path leakage | PASS — tests/test_projects_api.py:52-124 and app/project_api.py:89-195 |
| 2 | Project selector, character library/version, safe previews, history links, reload restoration, stale-response race guard, no autorun | PASS — app/web/index.html:28-69, app/web/projects.js:65-222, browser journey above |
| 3 | Cross-project pinned-version reuse without inherited jobs; reset preserves versions/config/files/server jobs | PASS — tests/test_projects_api.py:83-116, app/web/projects.js:290-307, browser reset journey |
| 4 | Legacy upload-only and existing prepare/run/status/artifact/workflow/prompt behavior unchanged; no automatic/provider/consistency claims | PASS — tests/test_projects_api.py:210-244 plus full 183-test suite; browser run remained uninvoked |
| 5 | Actionable invalid/conflict/missing/integrity errors; only recorded asset IDs resolve; real browser-visible race safety | PASS — tests/test_projects_api.py:127-207, app/project_api.py:35-82, app/main.py:138-171, rendered race evidence above |
| 6 | Focus/keyboard/reduced-motion usability, existing suites green, JS syntax, synthetic source inputs only | PASS — app/web/styles.css:3,7,40-58 and tests/test_project_frontend.py:40-130; full/JS gates above |

LEARNINGS:
- The store-first boundary held: every HTTP action uses public WorkspaceStore methods, and responses serialize records rather than ResolvedAsset.path.
- Restricting store synchronization middleware to /api/projects, /api/characters, and /api/assets preserved legacy health/catalog/prepare behavior while still supporting isolated TestClient roots.
- A real stale-response test required a deliberately delayed first project history response; requestEpoch rejection was then observed in rendered browser state, not inferred from source text.
- pvg gates caught a genuine prepare-complexity blocker that focused/full behavior tests missed. Extracting validation was behavior-preserving and moved the gate from FAIL to PASS.
- CUA subagent IAB visibility is constrained, but rendered background tabs, accessibility snapshots, screenshots, and console logs still provide usable browser evidence.

OBSERVATIONS:
- CUA ResourceTiming capture was not available in this rendered tab: the first supported evaluate failed because performance was undefined, and the second returned no entries. No third attempt was made; race proof relies on visible state at both checkpoints plus the screenshot.
- The app server logged automatic favicon.ico 404 requests during browser journeys. Browser console error/warning output was empty and no story-owned route changed; no favicon fix was attempted outside ownership.
- The temporary race-only proxy printed stack traces when relaying those favicon 404s. It was test harness noise, not an application request in the race path, and the proxy was stopped during cleanup.
- pvg notes search reported vault "Claude" unavailable, matching dispatch guidance; no vault repair was attempted.
- pvg verify reported six scannable files although eight explicit paths were supplied because HTML/CSS/test-only paths are outside its current scanners.

## nd_contract
status: new

### evidence
- 2026-10-26 final SrPM mechanical repair: normalized the four owned bodies through pvg issues/nd, including supported pvg nd edit lifecycle; pvg lint --backlog --epic OJ-mnrv --json => [].
- pvg nd doctor => All 29 issues passed validation; pvg nd dep cycles => none; pvg nd sync --no-push => up to date (bcae4548).

### proof
- [ ] Substantive implementation and story-specific acceptance evidence remain pending for developers.

## nd_contract
status: new

### evidence
- Created from the operator-approved connected-studio architecture; no implementation or execution claim.

### proof
- [ ] The story's explicit acceptance criteria are independently verified before acceptance.

## nd_contract
status: new

### evidence
- 2026-10-26 SrPM mechanical repair through pvg issues/pvg nd only; baseline pvg lint --backlog --epic OJ-mnrv --json reported 6 errors and 8 review findings.
- Repaired managed-heading duplication, exact MANDATORY SKILLS shape, typed cross-story signatures, safe asset resolution/upload-root contracts, observable outcomes, combined titles, and the operator's local-only commit authorization.

### proof
- [ ] Implementation proof remains pending for this story's substantive acceptance criteria.

## nd_contract
status: new

### evidence
- Created from the operator-approved connected-studio architecture; no implementation or execution claim.

### proof
- [ ] The story's explicit acceptance criteria are independently verified before acceptance.

## History
- 2026-10-27T03:45:28Z dep_added: blocked_by OJ-6xh3
- 2026-10-27T03:45:29Z dep_added: blocks OJ-wfpy
- 2026-10-27T05:22:51Z dep_removed: was_blocked_by OJ-6xh3
- 2026-10-27T05:33:08Z dep_added: blocked_by OJ-8zaw
- 2026-10-27T05:45:32Z dep_removed: was_blocked_by OJ-8zaw
- 2026-10-27T05:47:29Z status: open -> in_progress
- 2026-10-27T05:47:29Z auto-follows: linked to predecessor OJ-6xh3
- 2026-10-27T05:47:29Z auto-follows: linked to predecessor OJ-8zaw
- 2026-10-27T05:47:29Z claimed by dev-OJ-5uq4
- 2026-10-27T06:36:01Z status: in_progress -> open
- 2026-10-27T06:36:01Z released by speed
- 2026-10-27T06:36:01Z status: open -> in_progress
- 2026-10-27T06:36:02Z claimed by dev-OJ-5uq4

## Links
- Parent: [[OJ-mnrv]]
- Blocks: [[OJ-wfpy]]
- Was blocked by: [[OJ-6xh3]], [[OJ-8zaw]]
- Follows: [[OJ-6xh3]], [[OJ-8zaw]]

## Comments

### 2026-10-27T06:28:22Z speed
Worker /root/dev_oj_5uq4 ended with empty final before any source commit or delivered label. Do not treat progress reports as completion. Fresh bounded recovery agent is preserving only the eight owned source/test artifacts into a local WIP commit and reporting tests without code edits; failed worktree will then be removed/recreated and a fresh developer will finish verification/rework. No acceptance or merge; no push/GPU spending.

### 2026-10-27T06:37:22Z speed
Recovery artifact2e33c57 preserved exact8paths; independent fresh recovery verification focused5pass/full183pass,1baselinewarning; owned uvicorn8895 stopped. Removed failed worktree via pvg, released then pvg loop next selected story, atomically reclaimed and recreated canonical worktree. Fresh GLM high-effort worker now finishing browser verification/rework from committed artifacts; failed worker not resumed. No deliver/accept/merge yet.
