---
id: OJ-wfpy
title: "E2e: return to a saved project with reusable character references in Studio"
status: open
priority: 1
type: task
labels: [studio, foundation, local, no-spend, capstone, e2e]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:29Z
created_by: speed
updated_at: 2026-10-27T04:42:27Z
content_hash: "sha256:4ab272007a0d27b3c74bc5c5023ece8d9428fd3f8a7b2492f06d81971c9a9639"
blocked_by: [OJ-5uq4]
was_blocked_by: [OJ-6xh3]
---
## Description
Exercise the completed foundation through the user's actual local browser and HTTP data flow. This capstone is E2E-only, blocked by every other child. It does not implement a missing store or API.

## USER INTENT
A creator can save a project, reuse a character reference, prepare/review a labeled local dry-run result, restart the app and return to the same project/history without scripts, hidden inference or media loss. Observable outcome: a user can complete this journey and visibly return to the same project/history after restart.

## Ownership / DIFF BUDGET
NEW tests/test_foundation_e2e.py; NEW tools/foundation_trial.py; NEW docs/evidence/studio-foundation/README.md plus public-safe generated receipts/screenshots. Approximately 3-5 files, under 650 changed LOC. No production implementation edits; report missing functionality instead of fixing it in the capstone.

### Functional acceptance
1. Start actual uvicorn on 127.0.0.1 with a temporary workspace wired as WorkspaceStore(SETTINGS.data_dir), credentials removed and dry_run explicitly selected. Use real SQLite, filesystem, HTTP, generated test media and FFmpeg. No mock/stub replaces project, API, store, renderer-dry-run implementation or browser interactions.
2. A user creates a project, safely stages/saves a synthetic character version, prepares a source using that saved version, explicitly runs the existing labeled dry_run path, sees safe asset-ID previews plus comparison/download/configuration links and navigates back to the project's saved history. Do not imply AI inference or a new visual keeper.
3. Stop and restart the actual application process, reopen the browser and prove project/character-version/prepared configuration persisted. Do not claim remote render recovery; verify no new run was submitted by reload and legacy/no-project flow still works.
4. Repeat a version selection and form reset/project switch; old reference bytes, prepared hashes, existing protected evidence and historical links remain unchanged. Missing/conflicting input paths yield user-actionable errors rather than misleading completion.
5. Capture public-safe screenshots/receipts from the actual browser and HTTP flow. Assert no secrets/absolute personal paths, zero creative-provider submissions, loopback binding and stopped owned processes. Do not publish media or open a tunnel.
6. On merged accepted code run the full test suite, compileall, JS syntax checks, pvg gates and the existing keeper verifier. Report actual results, warnings, hashes, ownership and tri-state failures distinctly; a missing API dependency is a failure, not a skipped pass.

PRODUCES:
- tests/test_foundation_e2e.py -> real local foundation user-journey E2E tests only.
- tools/foundation_trial.py -> run_trial(*, temp_root: Path, evidence_root: Path) -> dict[str, Any], owning loopback server/browser cleanup and redacted receipts.
- docs/evidence/studio-foundation/README.md -> replayable exact commands/results and human-readable evidence index.
CONSUMES:
- OJ-6xh3: src/openjutsu/workspace_store.py -> WorkspaceStore(root: Path) and its persisted public record contract.
  spec: WorkspaceStore(root: Path) -> WorkspaceStore; stage_asset(project_id: str, filename: str, content: BinaryIO, *, role: str, protected: bool = False) -> AssetRecord; resolve_asset(asset_id: str) -> ResolvedAsset; get_character_version(character_id: str, version: int) -> CharacterVersionRecord; list_prepared_jobs(project_id: str) -> list[PreparedConfigRecord].
  fields: ResolvedAsset(record: AssetRecord, path: Path) is server-only; AssetRecord and the other public records contain no absolute server path.
- OJ-5uq4: app/project_api.py -> create_project_router(store: WorkspaceStore) -> APIRouter.
  endpoint: POST/GET /api/projects; GET /api/projects/{project_id}; GET /api/projects/{project_id}/jobs; POST /api/characters multipart project_id,name,description,reference_1,optional reference_2; GET /api/characters; GET /api/characters/{character_id}/versions/{version}; GET /api/assets/{asset_id}; project-aware POST /api/prepare.
- OJ-5uq4: app/web/projects.js -> connected project/character selection, safe asset-ID previews, and saved-history UI.
  source: app wiring uses WorkspaceStore(SETTINGS.data_dir) and safe multipart staging while retaining existing no-project SETTINGS.data_dir/uploads/<job_id> behavior; browser module integrates with the existing form and request-isolation behavior without renderer changes.
- (existing): src/openjutsu/evidence.py -> verify_manifest(...) existing public keeper verifier.
  spec: verify_manifest(manifest_path: Path, *, probe_runner: Callable[[Path], dict[str, Any]] = default_ffprobe) -> VerificationResult; never weaken the gate.

## MANDATORY SKILLS
- developer — owns the bounded implementation and delivery evidence.
- codebase-memory — verifies current brownfield paths, APIs, and call relationships before edits.
- pm_acceptor — performs independent evidence-based acceptance; implementation cannot self-accept.

## Testing requirements
E2E tests ONLY. No new unit/integration tests in this capstone and no mocks of any kind. Real local infrastructure and data flows; use sanctioned computer-use/browser tooling for actual interactive evidence. All existing unit/integration suites must still be rerun at the integrated boundary. Read current helper/API signatures before writing the trial. No paid credentials, provider inference or public hosting.

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
- 2026-10-27T03:45:29Z dep_added: blocked_by OJ-6xh3
- 2026-10-27T03:45:29Z dep_added: blocked_by OJ-5uq4
- 2026-10-27T05:22:51Z dep_removed: was_blocked_by OJ-6xh3

## Links
- Parent: [[OJ-mnrv]]
- Blocked by: [[OJ-5uq4]]
- Was blocked by: [[OJ-6xh3]]

## Comments
