---
id: OJ-5uq4
title: "Connect saved projects and character references to the existing studio flow"
status: open
priority: 1
type: feature
labels: [studio, foundation, local, no-spend]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:28Z
created_by: speed
updated_at: 2026-10-27T03:45:28Z
content_hash: "sha256:39d541c284d3dcf33a42b4c7d0ae04c5b4d44a06ae16222d72b859d10ed222b1"
blocked_by: [OJ-6xh3]
blocks: [OJ-wfpy]
---

## Description
## Description
Connect saved projects and reusable character versions to the existing browser prepare/review path using the store delivered by OJ-6xh3. Do not create an unrelated demo UI or new renderer.

## USER INTENT
A creator can choose a saved project and character version, upload a source, prepare the existing C1 workflow using those stored references, reload and find the project's prepared jobs/configuration again.

## Ownership / DIFF BUDGET
NEW app/project_api.py, NEW app/web/projects.js; additive edits app/main.py, app/web/index.html, app/web/studio.js and app/web/styles.css (confirm the existing stylesheet path before editing); NEW tests/test_projects_api.py and tests/test_project_frontend.py. Approximately 8-9 files, under 1100 changed LOC including tests. Consumer must not rewrite workspace_store.py's API without separate review.

## API/UI contract
Add same-app /api/projects POST/GET and /api/projects/{project_id} GET; /api/projects/{project_id}/jobs GET; /api/characters POST multipart name,description,reference_1 and optional reference_2; /api/characters GET; /api/characters/{character_id}/versions/{version} GET. Public asset preview resolves an authorized recorded asset ID, never a caller filesystem path. Responses use the store's safe projections and actionable 404/409/422 errors.
Existing /api/prepare gains optional project_id,character_id,character_version. Preserve old upload-only clients. A saved version supplies the same one-performer primary/secondary references that already exist; it does NOT represent two-person recasting. If saved-character selection and uploaded references conflict, return an explicit 422 rather than silently substitute. Validation occurs before queuing/generation and missing saved assets fail clearly. Preserve source upload, seed, words, custom-workflow and current attestation semantics. After successful preparation, record the actual prepared job/configuration link in the selected project. Do not submit inference or change configure_workflow.

## Acceptance Criteria
1. Real API tests create/list/reopen a project, upload a synthetic reference bundle, prepare with its saved version without re-uploading references, and obtain a saved job/configuration link. Verify the actual emitted workflow uses the selected filenames and seed with current C1 constants unchanged.
2. The existing page includes a usable project selector and character library/version choice that participates in the existing form, previews and prepared job links. Reload restores the chosen project and server-backed history; switching projects cannot show a stale response as the new project's job.
3. A second project can reuse the pinned character version without inheriting unrelated jobs. Creating a new version or resetting the form leaves prior versions, prepared configuration, original files and running server jobs intact.
4. Legacy no-project upload clients and existing prepare/run/status/artifact/workflow/prompt routes retain their accepted behavior. No automatic run on import, selection, reload or preparation; no new provider, queue or consent-verification claim.
5. Invalid project/version/asset IDs, conflicting references, missing files and changed protected inputs yield actionable errors; public JSON/browser links contain no raw paths or credentials. Test request/response races and labels using real browser-visible state, not fabricated progress.
6. Focus, keyboard access and reduced-motion behavior remain usable. Existing workflow, media and readiness suites remain green; frontend JS syntax checks pass. Source-photo inputs in tests are synthetic, not a fake production keeper.

PRODUCES:
- app/project_api.py -> create_project_router(store: WorkspaceStore) -> APIRouter with the endpoint contract above.
- app/web/projects.js -> project/reference selection and server-backed history integrated with the existing form.
- app/main.py -> additive project router wiring and optional project/character-aware prepare flow, not renderer changes.
- tests/test_projects_api.py -> real store/API contract coverage.
- tests/test_project_frontend.py -> browser/form integration and stale-state regression coverage.
CONSUMES:
- OJ-6xh3: src/openjutsu/workspace_store.py -> WorkspaceStore(root: Path); create_project(name: str) -> ProjectRecord; list_projects() -> list[ProjectRecord]; get_project(project_id: str) -> ProjectRecord; register_asset(project_id: str, path: Path, role: str, *, protected: bool = False) -> AssetRecord; create_character_version(name: str, reference_asset_ids: list[str], description: str = "") -> CharacterVersionRecord; get_character_version(character_id: str, version: int) -> CharacterVersionRecord; list_character_versions() -> list[CharacterVersionRecord]; record_prepared_job(project_id: str, job_id: str, job_dir: Path, character_version: tuple[str,int] | None = None) -> PreparedConfigRecord; list_prepared_jobs(project_id: str) -> list[PreparedConfigRecord]. Call only typed public methods, not private SQL internals.
- (existing) src/openjutsu/pipeline.py -> prepare_workflow(...) -> tuple[PreparedJob, dict[str, Any]] with current attestation and C1 behavior.
- (existing) app/web/studio.js -> existing epoch/isCurrent request isolation and explicit prepare/run/review flow; integrate without overwriting accepted source.

## Testing requirements
Real temp store plus FastAPI/TestClient integration, deterministic form/browser regression and existing no-project regression suites. No mocked store and no paid backend. Run focused tests, full pytest, Python compileall, node --check for changed JS, and pvg gates. Preserve the disclosed existing warning rather than weaken assertions.

## Context and hard boundaries
Brownfield RecastRoom at main c2a18a5; current Python/FastAPI/browser app is the base, not a rewrite. Architecture: ../ntm-recastroom-superapp-architecture-20261026/SUPER_APP_BLUEPRINT.md. This epic covers M0 only; scenes, multi-person engines, effects and camera remain later milestones, not rejected scope.
No provider credentials, paid API/GPU/Colab jobs, network collection, push, public deployment, publication or X actions. Use synthetic/temp fixtures for tests; never commit private footage, actual photos, keys, generated keeper media or absolute personal paths. Preserve the pre-existing untracked docs/evidence/recastroom-hook-v6b-keeper/ directory.
Keep existing attestation behavior, C1 graph, source-audio restoration, status and comparison semantics unchanged. Do not market attestation as verified rights. Do not rename or mix C1 and the older BFS/Head0.35 pipeline. New project history is not a claim of renderer recovery, visual QC, generic casting or model inference.
Mandatory skills for execution: developer and codebase-memory; PM review uses pm_acceptor. Use pvg story claim/deliver and append nd_contract evidence; no direct vault edits. No source commit/merge until the operator authorizes it for this foundation. Developer delivers, independent PM accepts. Follow current repo/global instructions, public type annotations, apply_patch and scope ownership.
Fresh root baseline: env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src .venv/bin/python -m pytest -q =>126 passed,1 existing Starlette/httpx warning; do not suppress tests/warnings or confuse historical results with a new run. Every delivery includes exact LEARNINGS: and OBSERVATIONS: sections, commands/results, artifact paths and hashes where relevant.


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: new

### evidence
- Created from the operator-approved connected-studio architecture; no implementation or execution claim.

### proof
- [ ] The story's explicit acceptance criteria are independently verified before acceptance.


## History
- 2026-10-27T03:45:28Z dep_added: blocked_by OJ-6xh3
- 2026-10-27T03:45:29Z dep_added: blocks OJ-wfpy

## Links
- Parent: [[OJ-mnrv]]
- Blocks: [[OJ-wfpy]]
- Blocked by: [[OJ-6xh3]]

## Comments
