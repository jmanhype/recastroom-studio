---
id: OJ-5uq4
title: "Connect saved projects to the existing studio flow"
status: open
priority: 1
type: feature
labels: [studio, foundation, local, no-spend]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:28Z
created_by: speed
updated_at: 2026-10-27T04:42:27Z
content_hash: "sha256:268284401dd34a294a980821d435f900d3efe6f1f4659630924675b2b2f70cf1"
blocked_by: [OJ-6xh3]
blocks: [OJ-wfpy]
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

## Links
- Parent: [[OJ-mnrv]]
- Blocks: [[OJ-wfpy]]
- Blocked by: [[OJ-6xh3]]

## Comments
