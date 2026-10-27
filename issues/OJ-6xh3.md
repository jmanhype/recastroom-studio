---
id: OJ-6xh3
title: "Persist connected projects, protected asset references and character versions"
status: open
priority: 1
type: task
labels: [studio, foundation, local, no-spend]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:28Z
created_by: speed
updated_at: 2026-10-27T03:45:28Z
content_hash: "sha256:75a30d86ed8b02579ee5f243dfd4aaad12a8aa4b1406cd2bec09a4fd9e1a90e5"
blocks: [OJ-5uq4, OJ-wfpy]
---

## Description
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
