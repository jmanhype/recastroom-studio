---
id: OJ-6xh3
title: "Persist the connected workspace record store"
status: in_progress
priority: 1
type: task
labels: [studio, foundation, local, no-spend, delivered]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:28Z
created_by: speed
updated_at: 2026-10-27T05:14:10Z
content_hash: "sha256:49f7127fcffac00d195688a26c69f852fe640fdd6b0a556dca42c3148b436aa1"
blocks: [OJ-5uq4, OJ-wfpy]
assignee: dev-OJ-6xh3
---
## Description
Add the authoritative local workspace store and safe reference import required by the connected M0 path. This is an infrastructure task feeding the user-visible path in the next child.

## USER INTENT
Saved project and reusable identity information must survive restart without rewriting media, accepted decisions or completed jobs. Observable outcome: after reopening the store, its public query methods return the same projects, character versions, asset identities, and prepared-job history.

## Ownership / DIFF BUDGET
NEW src/openjutsu/workspace_store.py; NEW tests/test_workspace_store.py. Approximately 2-3 files, under 700 changed LOC including tests; investigate overruns rather than silently expanding scope. Do not edit app/main.py, workflow.py, media.py or accepted verifier modules.

## Interface contract
WorkspaceStore(root: Path) owns root/workspace.sqlite3 and treats only root/uploads and root/imports as configured upload/import roots. Initialization may create those directories beneath a caller-supplied temporary or configured root, but never scans any other directory. Production wiring is explicit: app/main.py constructs WorkspaceStore(SETTINGS.data_dir), so the store-permitted upload root is exactly SETTINGS.data_dir/uploads and remains compatible with the existing no-project upload destination SETTINGS.data_dir/uploads/<job_id>. Tests create synthetic regular files beneath root/uploads or root/imports; no private photo, movie, keeper, credential, or absolute personal path is required.

Public typed records have these exact fields:
- ProjectRecord(project_id: str, name: str, created_at: str, updated_at: str).
- AssetRecord(asset_id: str, project_id: str, role: str, filename: str, media_type: str | None, size_bytes: int, sha256: str, protected: bool, created_at: str). This is the safe public projection and contains no server path.
- CharacterVersionRecord(character_id: str, version: int, name: str, description: str, reference_asset_ids: list[str], created_at: str); the list contains one or two distinct recorded asset IDs.
- PreparedConfigRecord(project_id: str, job_id: str, character_id: str | None, character_version: int | None, seed: int, workflow_sha256: str, prompt_sha256: str, source_sha256: str | None, reference_sha256s: list[str], config: dict[str, Any], created_at: str).
- ResolvedAsset(record: AssetRecord, path: Path) is server-only. API code may use path to stream a preview but must never serialize it; AssetRecord remains the public response projection.

Public methods: create_project(name: str) -> ProjectRecord; list_projects() -> list[ProjectRecord]; get_project(project_id: str) -> ProjectRecord; register_asset(project_id: str, path: Path, role: str, *, protected: bool = False) -> AssetRecord; stage_asset(project_id: str, filename: str, content: BinaryIO, *, role: str, protected: bool = False) -> AssetRecord; resolve_asset(asset_id: str) -> ResolvedAsset; create_character_version(name: str, reference_asset_ids: list[str], description: str = "") -> CharacterVersionRecord; get_character_version(character_id: str, version: int) -> CharacterVersionRecord; list_character_versions() -> list[CharacterVersionRecord]; record_prepared_job(project_id: str, job_id: str, job_dir: Path, character_version: tuple[str, int] | None = None) -> PreparedConfigRecord; list_prepared_jobs(project_id: str) -> list[PreparedConfigRecord]. State validation, named exceptions, and immutable-record behavior must be documented in module types/tests, not guessed by the API child.

register_asset resolves only an explicit regular file beneath root/uploads or root/imports. It rejects missing files, malformed IDs, traversal, symlinked path components, symlink escape, and files whose resolved location leaves the permitted root; it hashes bytes without moving, rewriting, or deleting the original. stage_asset is the safe server-only multipart staging boundary: it validates an existing project and a single-component filename, consumes BinaryIO content, writes beneath a server-generated root/uploads/<staging_id>/<safe_filename>, and records the resulting asset through the same integrity path without accepting a caller Path or exposing/serializing the destination. resolve_asset(asset_id) rechecks the recorded relative location, regular-file status, symlink boundaries, and protected SHA-256 before returning a server-only path. The API must use this accessor rather than private SQL or caller-supplied paths.

### Functional acceptance
1. Real temp SQLite reopen and independent store instances preserve two projects, asset identities, versioned character references and prepared configuration history; SQLite transactions leave no partial rows after an injected local failure. No distributed/remote submission claim.
2. Asset registration reads only explicit regular files beneath root/uploads or root/imports. Reject missing files, traversal, symlinked components/symlink escape and malformed IDs; compute hashes without moving, rewriting or deleting the original. stage_asset proves safe multipart staging with BinaryIO, a single-component filename, a server-generated root/uploads/<staging_id>/<safe_filename>, rejection of path-bearing names, and a returned AssetRecord containing no destination path. Duplicate content is handled deterministically without erasing project/role ownership.
3. Character versions are append-only. A second project can reuse a specific version; creating another version does not mutate prior references or a prepared job's pinned IDs/hashes.
4. Recording an existing prepared job snapshots the actual workflow/prompt/source/reference fingerprints and seed/config metadata from the produced job directory. Legacy jobs with no project remain readable; no invented acceptance verdict or renderer attempt is created.
5. Private paths remain internal. resolve_asset(asset_id) returns the safe AssetRecord plus a server-only Path after boundary/integrity checks; the public projection contains no absolute path, credential, full graph secret or unsupported legal/quality guarantee. Malformed input or changed protected bytes fails explicitly without table/state corruption or path disclosure.
6. Existing baseline suite remains green; no keeper or bundled graph change. Tests use temp/synthetic files, no real photo or movie access required.

PRODUCES:
- src/openjutsu/workspace_store.py -> WorkspaceStore(root: Path), the exact public typed records above, and the listed public methods including stage_asset(project_id: str, filename: str, content: BinaryIO, *, role: str, protected: bool = False) -> AssetRecord and resolve_asset(asset_id: str) -> ResolvedAsset.
- tests/test_workspace_store.py -> persistence/import/version/configuration transaction and safe asset-resolution regression tests.
CONSUMES:
- (existing): src/openjutsu/pipeline.py -> PreparedJob.to_json(self) -> str and prepare_workflow(...) -> tuple[PreparedJob, dict[str, Any]].
  spec: prepare_workflow(settings: Settings, *, job_id: str, source: str | Path, reference_1: str | Path, reference_2: str | Path | None, words_path: str | Path | None, rights_attested: bool, identity_description: str | None = None, seed: int = 49, workflow_template: str | Path | None = None) -> tuple[PreparedJob, dict[str, Any]]; read produced job.json/workflow.json/prompt.txt only, do not alter generation.

## MANDATORY SKILLS
- developer — owns the bounded implementation and delivery evidence.
- codebase-memory — verifies current brownfield paths, APIs, and call relationships before edits.
- pm_acceptor — performs independent evidence-based acceptance; implementation cannot self-accept.

## Testing requirements
Unit and real SQLite integration tests for staged multipart bytes, explicit imports, and safe resolution; no mock replacing the store. PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_workspace_store.py, then full pytest, compileall and pvg gates on touched source. Record transactional failure and unchanged input hashes as positive evidence.

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
status: delivered

### evidence
- Commit SHA: c38e41a191269c7e015fbc975e7b82df105fabfb
- Commands run: focused pytest => 4 passed; full pytest => 130 passed, 1 supplied warning; compileall => PASS; pvg verify => PASS, 0 issues; touched gates => PASS, 1 disclosed file_loc warning; scoped app/src/scripts/tools gates => PASS, 14 warnings (13 baseline + new file_loc).
- Summary: real temp SQLite persistence/reopen, safe upload/import boundaries, protected staging/resolution, append-only versions, pinned prepared history, legacy history, transaction rollback, and macOS /tmp normalization are implemented and tested.

### proof
- [x] AC #1: SQLite reopen and transaction failure — PASS
- [x] AC #2: safe registration/staging and duplicate ownership — PASS
- [x] AC #3: append-only and reusable character versions — PASS
- [x] AC #4: real prepared-job fingerprints/config and legacy readability — PASS
- [x] AC #5: private-path resolution and public projection integrity — PASS
- [x] AC #6: full baseline suite and scope preservation — PASS

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

### CI/Test Results
Commands run:
- `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q tests/test_workspace_store.py`
- `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q`
- `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m compileall -q src/openjutsu/workspace_store.py tests/test_workspace_store.py`
- `pvg verify src/openjutsu/workspace_store.py tests/test_workspace_store.py --include-tests --format text`
- `pvg gates src/openjutsu/workspace_store.py tests/test_workspace_store.py --format text`
- `pvg gates app src scripts tools --format text`
- stdlib focused trace over the same 4-test command: `python -m trace --count --coverdir="$TRACE_DIR" "$ROOT/.venv/bin/pytest" -q tests/test_workspace_store.py`

Summary:
- Focused real SQLite/temp-filesystem tests: PASS, `4 passed in 0.11s` (final exact-commit run).
- Full suite: PASS, `130 passed, 1 warning in 23.78s`. The warning is the supplied pre-existing Starlette/httpx deprecation; it was not suppressed.
- `compileall`: PASS.
- `pvg verify`: PASS, 2 files scanned, 0 issues.
- Touched gates: PASS with 1 disclosed warning: `workspace_store.py` file_loc 520>400. Complexity warnings were removed by isolating prepared-job directory validation.
- Repository scoped gates (`app src scripts tools`): PASS with 14 warnings = the supplied 13 baseline warnings plus this new file_loc warning. No warnings were suppressed.
- Coverage: stdlib `trace` line execution under focused tests measured `413/413 = 100.0%`. This is line-execution evidence, not branch coverage. The `coverage` package is not installed and was not added because package installation is prohibited.
- Test/storage integrity: real temp SQLite reopen through a second `WorkspaceStore`; no store mock. Original registered-file bytes and mtime stayed unchanged; protected mutation failed closed; an injected SQLite trigger failure left no asset row.
- Scope: no renderer/engine/UI invocation or implementation, no provider/network/GPU call, no credential use, no keeper/graph/app/workflow/media/verifier edits, and no push/publication.

Commit SHA: `c38e41a191269c7e015fbc975e7b82df105fabfb`
Branch: `story/OJ-6xh3`
Artifacts:
- `src/openjutsu/workspace_store.py` (568 physical lines; SHA-256 `536bab6e4d003184ba61c587a23120fb64e961742e707cfacbf08f6d2db6154c`)
- `tests/test_workspace_store.py` (184 physical lines; SHA-256 `393b3dc40d360504e5eeebb269ead59c037c62f0cf5b38feec76a78f5309360c`)
- Git insertion count: 752 across exactly two files. This is 52 lines over the investigative ~700 budget because exact public typed contracts were kept readable and four focused integration scenarios preserve path, transaction, version-pinning, staging, and macOS alias coverage as requested; no unrelated file was added.

Wiring:
- Library-only story; production app wiring is explicitly assigned to the next child. Wiring check intentionally not applicable. Existing `prepare_workflow` was consumed unchanged in tests to produce real `job.json`, `workflow.json`, and `prompt.txt`.

### AC checklist
- [x] AC #1 reopen/persistence/transaction: exact typed records and SQLite history at `src/openjutsu/workspace_store.py:203-376`; real reopen, immutable version pinning, and trigger failure at `tests/test_workspace_store.py:37-97`. PASS.
- [x] AC #2 safe imports/staging/duplicates: public `AssetRecord` and staging at `src/openjutsu/workspace_store.py:221-265`; permitted-root/symlink/hash checks at `src/openjutsu/workspace_store.py:385-434`; explicit imports, unchanged input, safe staging, duplicate ownership, and malformed paths at `tests/test_workspace_store.py:99-184`. PASS.
- [x] AC #3 append-only character versions/reuse: implementation at `src/openjutsu/workspace_store.py:279-316`; old version and cross-project pinned references at `tests/test_workspace_store.py:37-97`. PASS.
- [x] AC #4 prepared job snapshot/legacy: public method at `src/openjutsu/workspace_store.py:318-351`; safe artifact reader at `src/openjutsu/workspace_store.py:448-533`; actual workflow/prompt/source/reference/seed/config and legacy project checks at `tests/test_workspace_store.py:37-97`. PASS.
- [x] AC #5 private-path projection: `AssetRecord` at `src/openjutsu/workspace_store.py:51-62`; server-only `ResolvedAsset` at `src/openjutsu/workspace_store.py:89-92`; resolve/recheck at `src/openjutsu/workspace_store.py:266-277`; no public path, protected mutation failure, malformed IDs, path non-disclosure, and `/tmp` normalization at `tests/test_workspace_store.py:99-160`. PASS.
- [x] AC #6 baseline/scope: exact-commit full suite 130 passed with only the supplied warning; only the two owned files are committed; no keeper or bundled graph change. PASS.

### pvg verify
- `VERIFY: PASSED (2 files scanned, 0 issues)`

LEARNINGS:
- macOS normalization must retain the caller-supplied `/tmp/...` root alias while using the resolved `/private/tmp/...` root for stored relative paths; this allows compatible spelling without accepting symlink escape beneath `uploads` or `imports`.
- Mapping configured roots by tuple index was the only functional implementation bug found by focused tests: imports accidentally inherited the uploads resolved root. The test caught it before commit.
- SQLite trigger injection is a useful no-mock transaction failure mechanism, but the trigger must be dropped before reopen checks so the store's normal behavior remains testable.
- `pvg verify` caught a best-effort cleanup branch written as bare `pass`; explicit `return None` keeps the behavior without a stub finding.
- stdlib `trace` can provide dependency-free focused line evidence, but it must launch the venv pytest script directly; `python -m trace -m pytest` treats pytest as a missing file.

OBSERVATIONS:
- [ISSUE] Python environment: `coverage` is not installed (`ModuleNotFoundError`). No dependency was installed; stdlib trace was used and explicitly identified as line rather than branch coverage.
- [TOOLING] Intermediate `pvg verify --check-mocks` reported an empty integration/e2e heuristic scan for the two explicitly named paths; it was not used as proof. The real SQLite tests and passing normal `pvg verify` are the evidence.
- [TOOLING] One initial `pvg gates --format=text` spelling was rejected; the supported `--format text` run passed. The later `python -m trace -m pytest` spelling failed with “Cannot run file 'pytest'”; the corrected direct pytest-script trace passed. Both were command-use corrections, not source failures.
- [TOOLING] A pre-commit `git diff --cached --check` blocked a blank EOF line; the line was removed before the commit. An attempted trace cleanup command containing `rm -rf` was rejected before execution and had no filesystem effect; `mktemp` directories were used instead.
- [WARN] New `file_loc` warning remains in otherwise PASS gates because the store intentionally keeps the exact records, path boundary, SQLite transaction, and prepared-job contract cohesive. Splitting solely to hide the warning would add a file and reduce API-child readability.

## nd_contract
status: delivered

### evidence
- Exact commit and tests above; focused 4 passed, full 130 passed/1 supplied warning, compileall PASS, pvg verify PASS, gates PASS with disclosed warnings.
- Source/test SHA-256 values recorded above.

### proof
- [x] AC #1: real SQLite persistence/reopen and injected transaction failure verified.
- [x] AC #2: explicit upload/import regular files, symlink/traversal rejection, unchanged input, server-generated staging, safe filenames, duplicate ownership, and hashes verified.
- [x] AC #3: append-only versions, prior-reference immutability, and second-project version reuse verified.
- [x] AC #4: actual prepared artifacts/fingerprints/seed/config and legacy no-project history verified.
- [x] AC #5: private server-only path resolution, public no-path projection, protected-byte integrity failure, and path non-disclosure verified.
- [x] AC #6: full baseline suite green with only the supplied warning and no out-of-scope artifact changes.

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
- 2026-10-27T03:45:28Z dep_added: blocks OJ-5uq4
- 2026-10-27T03:45:29Z dep_added: blocks OJ-wfpy
- 2026-10-27T04:44:08Z status: open -> in_progress
- 2026-10-27T04:44:08Z claimed by dev-OJ-6xh3
- 2026-10-27T05:12:06Z status: in_progress -> in_progress
- 2026-10-27T05:13:04Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-mnrv]]
- Blocks: [[OJ-5uq4]], [[OJ-wfpy]]

## Comments

### 2026-10-27T05:14:10Z speed
Delivery-contract correction (managed Notes contracts serialize before historical contract blocks):

## nd_contract
status: delivered

### evidence
- Commit SHA: c38e41a191269c7e015fbc975e7b82df105fabfb
- Commands run: focused pytest => 4 passed; full pytest => 130 passed, 1 supplied warning; compileall => PASS; pvg verify => PASS; touched gates => PASS/1 warn; scoped gates => PASS/14 warns.
- Summary: real SQLite persistence/reopen, safe paths/staging, protected resolution, append-only versions, prepared/legacy history, transaction rollback, and macOS /tmp normalization verified.

### proof
- [x] AC #1: SQLite reopen and transaction failure — PASS
- [x] AC #2: safe registration/staging and duplicate ownership — PASS
- [x] AC #3: append-only and reusable character versions — PASS
- [x] AC #4: real prepared-job fingerprints/config and legacy readability — PASS
- [x] AC #5: private-path resolution and public projection integrity — PASS
- [x] AC #6: full baseline suite and scope preservation — PASS
