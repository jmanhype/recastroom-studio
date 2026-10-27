---
id: OJ-6xh3
title: "Persist the connected workspace record store"
status: open
priority: 1
type: task
labels: [studio, foundation, local, no-spend]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:28Z
created_by: speed
updated_at: 2026-10-27T04:26:01Z
content_hash: "sha256:24f971d6366370c0f0cca8338391f1cb45a2b999e1258ca93f405e4a000efdee"
blocks: [OJ-5uq4, OJ-wfpy]
---

## Description

## Description
Add the authoritative local workspace store and safe reference import required by the connected M0 path. This is an infrastructure task feeding the user-visible path in the next child.

## USER INTENT
Saved project and reusable identity information must survive restart without rewriting media, accepted decisions or completed jobs. Observable outcome: after reopening the store, its public query methods return the same projects, character versions, asset identities, and prepared-job history.

## Ownership / DIFF BUDGET
NEW src/openjutsu/workspace_store.py; NEW tests/test_workspace_store.py. Approximately 2-3 files, under 700 changed LOC including tests; investigate overruns rather than silently expanding scope. Do not edit app/main.py, workflow.py, media.py or accepted verifier modules.

## Interface contract
WorkspaceStore(root: Path) owns root/workspace.sqlite3 and treats only root/uploads and root/imports as configured upload/import roots. Initialization may create those directories beneath a caller-supplied temporary or configured root, but never scans any other directory. Tests create synthetic regular files beneath root/uploads or root/imports; no private photo, movie, keeper, credential, or absolute personal path is required.

Public typed records have these exact fields:
- ProjectRecord(project_id: str, name: str, created_at: str, updated_at: str).
- AssetRecord(asset_id: str, project_id: str, role: str, filename: str, media_type: str | None, size_bytes: int, sha256: str, protected: bool, created_at: str). This is the safe public projection and contains no server path.
- CharacterVersionRecord(character_id: str, version: int, name: str, description: str, reference_asset_ids: list[str], created_at: str); the list contains one or two distinct recorded asset IDs.
- PreparedConfigRecord(project_id: str, job_id: str, character_id: str | None, character_version: int | None, seed: int, workflow_sha256: str, prompt_sha256: str, source_sha256: str | None, reference_sha256s: list[str], config: dict[str, Any], created_at: str).
- ResolvedAsset(record: AssetRecord, path: Path) is server-only. API code may use path to stream a preview but must never serialize it; AssetRecord remains the public response projection.

Public methods: create_project(name: str) -> ProjectRecord; list_projects() -> list[ProjectRecord]; get_project(project_id: str) -> ProjectRecord; register_asset(project_id: str, path: Path, role: str, *, protected: bool = False) -> AssetRecord; resolve_asset(asset_id: str) -> ResolvedAsset; create_character_version(name: str, reference_asset_ids: list[str], description: str = "") -> CharacterVersionRecord; get_character_version(character_id: str, version: int) -> CharacterVersionRecord; list_character_versions() -> list[CharacterVersionRecord]; record_prepared_job(project_id: str, job_id: str, job_dir: Path, character_version: tuple[str, int] | None = None) -> PreparedConfigRecord; list_prepared_jobs(project_id: str) -> list[PreparedConfigRecord]. State validation, named exceptions, and immutable-record behavior must be documented in module types/tests, not guessed by the API child.

register_asset resolves only an explicit regular file beneath root/uploads or root/imports. It rejects missing files, malformed IDs, traversal, symlinked path components, symlink escape, and files whose resolved location leaves the permitted root; it hashes bytes without moving, rewriting, or deleting the original. resolve_asset(asset_id) rechecks the recorded relative location, regular-file status, symlink boundaries, and protected SHA-256 before returning a server-only path. The API must use this accessor rather than private SQL or caller-supplied paths.

## Acceptance Criteria
1. Real temp SQLite reopen and independent store instances preserve two projects, asset identities, versioned character references and prepared configuration history; SQLite transactions leave no partial rows after an injected local failure. No distributed/remote submission claim.
2. Asset registration reads only explicit regular files beneath root/uploads or root/imports. Reject missing files, traversal, symlinked components/symlink escape and malformed IDs; compute hashes without moving, rewriting or deleting the original. Duplicate content is handled deterministically without erasing project/role ownership.
3. Character versions are append-only. A second project can reuse a specific version; creating another version does not mutate prior references or a prepared job's pinned IDs/hashes.
4. Recording an existing prepared job snapshots the actual workflow/prompt/source/reference fingerprints and seed/config metadata from the produced job directory. Legacy jobs with no project remain readable; no invented acceptance verdict or renderer attempt is created.
5. Private paths remain internal. resolve_asset(asset_id) returns the safe AssetRecord plus a server-only Path after boundary/integrity checks; the public projection contains no absolute path, credential, full graph secret or unsupported legal/quality guarantee. Malformed input or changed protected bytes fails explicitly without table/state corruption or path disclosure.
6. Existing baseline suite remains green; no keeper or bundled graph change. Tests use temp/synthetic files, no real photo or movie access required.

PRODUCES:
- src/openjutsu/workspace_store.py -> WorkspaceStore(root: Path), the exact public typed records above, and the listed public methods including resolve_asset(asset_id: str) -> ResolvedAsset.
- tests/test_workspace_store.py -> persistence/import/version/configuration transaction and safe asset-resolution regression tests.
CONSUMES:
- (existing): src/openjutsu/pipeline.py -> PreparedJob.to_json(self) -> str and prepare_workflow(...) -> tuple[PreparedJob, dict[str, Any]].
  spec: prepare_workflow(settings: Settings, *, job_id: str, source: str | Path, reference_1: str | Path, reference_2: str | Path | None, words_path: str | Path | None, rights_attested: bool, identity_description: str | None = None, seed: int = 49, workflow_template: str | Path | None = None) -> tuple[PreparedJob, dict[str, Any]]; read produced job.json/workflow.json/prompt.txt only, do not alter generation.

## MANDATORY SKILLS
- developer — owns the bounded implementation and delivery evidence.
- codebase-memory — verifies current brownfield paths, APIs, and call relationships before edits.
- pm_acceptor — performs independent evidence-based acceptance; implementation cannot self-accept.

## Testing requirements
Unit and real SQLite integration tests; no mock replacing the store. PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_workspace_store.py, then full pytest, compileall and pvg gates on touched source. Record transactional failure and unchanged input hashes as positive evidence.

## Context and hard boundaries
Brownfield RecastRoom at main c2a18a5; current Python/FastAPI/browser app is the base, not a rewrite. Architecture: ../ntm-recastroom-superapp-architecture-20261026/SUPER_APP_BLUEPRINT.md. This epic covers M0 only; scenes, multi-person engines, effects and camera remain later milestones, not rejected scope.
No provider credentials, paid API/GPU/Colab jobs, network collection, push, public deployment, publication or X actions. Use synthetic/temp fixtures for tests; never commit private footage, actual photos, keys, generated keeper media or absolute personal paths. Preserve the pre-existing untracked docs/evidence/recastroom-hook-v6b-keeper/ directory.
Keep existing attestation behavior, C1 graph, source-audio restoration, status and comparison semantics unchanged. Do not market attestation as verified rights. Do not rename or mix C1 and the older BFS/Head0.35 pipeline. New project history is not a claim of renderer recovery, visual QC, generic casting or model inference.
Mandatory skills for execution: developer and codebase-memory; PM review uses pm_acceptor. Use pvg story claim/deliver and append nd_contract evidence; no direct vault edits. Local source commits/merges are authorized after story gates; pushes, remote publication and provider/GPU spending remain prohibited. Developer delivers, independent PM accepts. Follow current repo/global instructions, public type annotations, apply_patch and scope ownership.
Fresh root baseline: env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src .venv/bin/python -m pytest -q =>126 passed,1 existing Starlette/httpx warning; do not suppress tests/warnings or confuse historical results with a new run. Every delivery includes exact LEARNINGS: and OBSERVATIONS: sections, commands/results, artifact paths and hashes where relevant.


## Design


## Notes
## nd_contract
status: new

### evidence
- Created from the operator-approved connected-studio architecture; no implementation or execution claim.

### proof
- [ ] The story's explicit acceptance criteria are independently verified before acceptance.


## History
- 2026-10-27T03:45:28Z dep_added: blocks OJ-5uq4
- 2026-10-27T03:45:29Z dep_added: blocks OJ-wfpy

## Links
- Parent: [[OJ-mnrv]]
- Blocks: [[OJ-5uq4]], [[OJ-wfpy]]

## Comments

## Description
Add the authoritative local workspace store and safe reference import required by the connected M0 path. This is an infrastructure task feeding the user-visible path in the next child.

## USER INTENT
Saved project and reusable identity information must survive restart without rewriting media, accepted decisions or completed jobs.

## Ownership / DIFF BUDGET
NEW src/openjutsu/workspace_store.py; NEW tests/test_workspace_store.py. Approximately 2-3 files, under 700 changed LOC including tests; investigate overruns rather than silently expanding scope. Do not edit app/main.py, workflow.py, media.py or accepted verifier modules.

## Interface contract
WorkspaceStore(root: Path) creates a schema-versioned workspace.sqlite3 beneath the supplied configured data root using Python stdlib sqlite3, not a new service. Public typed records ProjectRecord, AssetRecord, CharacterVersionRecord and PreparedConfigRecord carry IDs, hashes/version metadata and safe public projections; private server paths never appear in public projections.
Public methods: create_project(name: str) -> ProjectRecord; list_projects() -> list[ProjectRecord]; get_project(project_id: str) -> ProjectRecord; register_asset(project_id: str, path: Path, role: str, *, protected: bool = False) -> AssetRecord; create_character_version(name: str, reference_asset_ids: list[str], description: str = "") -> CharacterVersionRecord; get_character_version(character_id: str, version: int) -> CharacterVersionRecord; list_character_versions() -> list[CharacterVersionRecord]; record_prepared_job(project_id: str, job_id: str, job_dir: Path, character_version: tuple[str,int] | None = None) -> PreparedConfigRecord; list_prepared_jobs(project_id: str) -> list[PreparedConfigRecord]. State validation, named exceptions and exact record fields must be documented in module types/tests, not guessed by the API child.

## Acceptance Criteria
1. Real temp SQLite reopen and independent store instances preserve two projects, asset identities, versioned character references and prepared configuration history; SQLite transactions leave no partial rows after an injected local failure. No distributed/remote submission claim.
2. Asset registration reads only explicit regular files from configured import/upload roots. Reject missing files, traversal/symlink escape and malformed IDs; compute hashes without moving, rewriting or deleting the original. Duplicate content is handled deterministically without erasing project/role ownership.
3. Character versions are append-only. A second project can reuse a specific version; creating another version does not mutate prior references or a prepared job's pinned IDs/hashes.
4. Recording an existing prepared job snapshots the actual workflow/prompt/source/reference fingerprints and seed/config metadata from the produced job directory. Legacy jobs with no project remain readable; no invented acceptance verdict or renderer attempt is created.
5. Private paths remain internal. The public projection contains no absolute path, credential, full graph secret or unsupported legal/quality guarantee. Malformed input fails explicitly without table/state corruption.
6. Existing baseline suite remains green; no keeper or bundled graph change. Tests use temp/synthetic files, no real photo or movie access required.

PRODUCES:
- src/openjutsu/workspace_store.py -> WorkspaceStore(root: Path) and the typed public method/record contract above.
- tests/test_workspace_store.py -> persistence/import/version/configuration transaction regression tests.
CONSUMES:
- (existing) src/openjutsu/pipeline.py -> PreparedJob.to_json(self) -> str and prepare_workflow(settings: Settings, *, job_id, source, reference_1, reference_2, words_path, rights_attested, identity_description=None, seed=49, workflow_template=None) -> tuple[PreparedJob, dict[str, Any]]; read produced job.json/workflow.json/prompt.txt only, do not alter generation.

## Testing requirements
Unit and real SQLite integration tests; no mock replacing the store. PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_workspace_store.py, then full pytest, compileall and pvg gates on touched source. Record transactional failure and unchanged input hashes as positive evidence.

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
- 2026-10-27T03:45:28Z dep_added: blocks OJ-5uq4
- 2026-10-27T03:45:29Z dep_added: blocks OJ-wfpy

## Links
- Parent: [[OJ-mnrv]]
- Blocks: [[OJ-5uq4]], [[OJ-wfpy]]

## Comments
