---
id: OJ-mnrv
title: "Build RecastRoom connected studio foundation"
status: open
priority: 1
type: epic
labels: [studio, foundation, local, no-spend]
created_at: 2026-10-27T03:45:27Z
created_by: speed
updated_at: 2026-10-27T05:27:17Z
content_hash: "sha256:e4ea6234b520a9a2ace34d91518fb7521a7b78383fb047cf0cd68cb11b815eb0"
---
## Description
Implement the first connected studio foundation: saved projects, protected asset references, reusable versioned character bundles and inspectable prepared-job history connected to the existing prepare/review flow.

## USER INTENT
A creator can return to the same project, reuse the chosen character references, prepare a real existing-workflow job without re-uploading the identity each time, and inspect its saved configuration without hidden inference or lost context.

### Functional acceptance
1. All children pass independent PM review, including a real local E2E capstone.
2. Project/character/configuration records survive application restart; original inputs and accepted evidence remain byte-identical.
3. Existing no-project prepare/run/review routes remain compatible, with no generation or attestation-policy redesign.
4. No spend, credentials, remote publication or paid backend is needed to demonstrate M0. Later engine milestones remain explicitly planned.

## Out of scope
Multi-shot orchestration, generic person selection, multi-person generation, effects/camera engines, managed rendering queue and hosted paid execution belong to later architecture milestones, not permanent concept-card substitutes.

## Context and hard boundaries
Brownfield RecastRoom at main c2a18a5; current Python/FastAPI/browser app is the base, not a rewrite. Architecture: ../ntm-recastroom-superapp-architecture-20261026/SUPER_APP_BLUEPRINT.md. This epic covers M0 only; scenes, multi-person engines, effects and camera remain later milestones, not rejected scope.
No provider credentials, paid API/GPU/Colab jobs, network collection, push, public deployment, publication or X actions. Use synthetic/temp fixtures for tests; never commit private footage, actual photos, keys, generated keeper media or absolute personal paths. Preserve the pre-existing untracked docs/evidence/recastroom-hook-v6b-keeper/ directory.
Keep existing attestation behavior, C1 graph, source-audio restoration, status and comparison semantics unchanged. Do not market attestation as verified rights. Do not rename or mix C1 and the older BFS/Head0.35 pipeline. New project history is not a claim of renderer recovery, visual QC, generic casting or model inference.
Mandatory skills for execution: developer and codebase-memory; PM review uses pm_acceptor. Use pvg story claim/deliver and append nd_contract evidence; no direct vault edits. Local source commits/merges are authorized after story gates; pushes, remote publication and provider/GPU spending remain prohibited. Developer delivers, independent PM accepts. Follow current repo/global instructions, public type annotations, apply_patch and scope ownership.
Fresh root baseline: env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src .venv/bin/python -m pytest -q =>126 passed,1 existing Starlette/httpx warning; do not suppress tests/warnings or confuse historical results with a new run. Every delivery includes exact LEARNINGS: and OBSERVATIONS: sections, commands/results, artifact paths and hashes where relevant.

## Acceptance Criteria

## Design

## Notes
Foundation children: OJ-6xh3 (store), OJ-5uq4 (connected app), OJ-wfpy (all-dependency E2E capstone). Old submission epic OJ-fglb preserved. Operator authorization now permits local source commits/merges only after story gates; no push or loop rotation is authorized.
Owner authorization 2026-10-26: build the connected studio foundation using Paivot. Local source-code commits and merges only. No pushes, publication, credentials, provider/GPU jobs or GPU/API spending. Supersedes earlier pending-commit-approval sentence. Root preflight:126 passed,1 disclosed Starlette/httpx warning. Existing old submission epic and its issues remain unchanged.
Dispatcher preflight: local-only source commits/merges explicitly authorized; foundation backlog structural repair is assigned to foundation_backlog_repair. Existing accepted architecture and full product scope preserved. Epic branch/worktree epic/OJ-mnrv/.claude/worktrees/epic-OJ-mnrv created from main c2a18a5 without switching main or touching pre-existing evidence. No developer dispatched before structural lint and independent Anchor approval. SQLite/temp filesystem/FFmpeg and root Python3.11.11 venv available. Use temporary Git transport guard for loop setup automatic remote sync; use pvg nd sync --no-push at manual sync boundaries. No source changes, no provider/GPU calls.
ANCHOR ROUND 1 ADDRESSED — upload staging/interface gap:

- OJ-6xh3 now produces the server-only staging API `stage_asset(project_id: str, filename: str, content: BinaryIO, *, role: str, protected: bool = False) -> AssetRecord`; it validates a single-component filename, consumes binary content, writes only beneath server-generated `root/uploads/<staging_id>/<safe_filename>`, and returns a safe `AssetRecord` without exposing the destination. `register_asset` remains the explicit import path and `resolve_asset` remains the safe lookup.
- OJ-5uq4 now requires `app/main.py` to construct `WorkspaceStore(SETTINGS.data_dir)`, pass it to `create_project_router(store)`, and stage character multipart bytes through `stage_asset`; existing no-project uploads remain at `SETTINGS.data_dir/uploads/<job_id>`. Requests accept no caller path/root and responses serialize no server path.
- OJ-wfpy now exercises the actual configured-root wiring and safe multipart staging in the restart journey.
- Verification after the repair: `pvg lint --backlog --epic OJ-mnrv --json` => `[]`; `pvg nd doctor` => all 29 issues valid; `pvg nd dep cycles` => none.
## ANCHOR REVIEW (backlog_review)
REVIEW_RESULT: APPROVED

### Round
2 of 3

### Prior-gap recheck
- RESOLVED: The round-1 upload staging/interface blocker is closed at the backlog-contract level.
- OJ-6xh3 now publishes the exact server-only API `stage_asset(project_id: str, filename: str, content: BinaryIO, *, role: str, protected: bool = False) -> AssetRecord`, requires a validated project and single-component filename, writes only beneath server-generated `root/uploads/<staging_id>/<safe_filename>`, rejects path-bearing names, accepts no caller `Path`, and returns only the safe `AssetRecord` without exposing the destination.
- OJ-5uq4 consumes that exact signature for multipart character references, requires `app/main.py` to construct `WorkspaceStore(SETTINGS.data_dir)` and pass it to `create_project_router(store)`, preserves the existing no-project `SETTINGS.data_dir/uploads/<job_id>` destination, accepts no filesystem path/root from requests, and serializes no server path.
- Both producer and consumer now carry matching typed PRODUCES/CONSUMES contracts and explicit staged-upload/root-wiring test requirements. The round-1 general rule is therefore addressed across the producer, consumer, and app wiring boundary rather than only patched in one story.
- No remaining gap from the round-1 rejection. Implementation, tests, and delivery evidence remain pending for the normal story/PM workflow; that is not a new backlog-review finding.

### Evidence
- `pvg lint --backlog --epic OJ-mnrv --json` => `[]`.
- Re-read the prior round-1 verdict from live `OJ-mnrv` and current live `OJ-6xh3`/`OJ-5uq4` interface, acceptance, PRODUCES/CONSUMES, wiring, and testing sections.
- `pvg nd dep cycles` => no dependency cycles.
- Bounded round-2 recheck only: no unrelated product/architecture rediscovery, source edit, provider/GPU call, credential use, push, issue acceptance/closure, or full test rerun.

## ANCHOR REVIEW (backlog_review)
REVIEW_RESULT: REJECTED

### Round
1 of 3

### Gaps
1. ISSUE: OJ-6xh3 -> OJ-5uq4 upload staging/interface is not executable as written. OJ-6xh3 permits asset registration only from an explicit regular file beneath its own `root/uploads` or `root/imports`, but its exact public contract exposes only `register_asset(project_id, path: Path, ...)` and `resolve_asset(asset_id)`; it exposes no safe server-only staging method or upload-root accessor. OJ-5uq4 nevertheless requires `POST /api/characters` multipart uploads while producing `create_project_router(store: WorkspaceStore) -> APIRouter` and instructs the consumer to call only the listed typed public methods. Current brownfield preparation writes uploads itself under `SETTINGS.data_dir/uploads/<job_id>` (`app/main.py` lines 96-113), so a router holding only `store` cannot place a new multipart reference inside the store's permitted root without guessing a private root, accepting a caller path, or rewriting the producer API.
   RULE: A producer that restricts mutation/import to server-controlled roots must also publish the exact root-construction and safe staging API required by its consumer; consumers may not guess private internals or widen ownership.
   SCOPE: Sweep the OJ-mnrv producer/consumer boundary: OJ-6xh3's public interface/tests, OJ-5uq4's router contract, and OJ-5uq4's `app/main.py` wiring.
   Impact: The sole connected API story cannot implement its required character upload path without an unauthorized interface change, making the vertical slice execution-breaking.
   Fix: Amend OJ-6xh3 and OJ-5uq4 consistently—for example add `stage_upload(project_id, source: IO[bytes] | bytes, filename: str, role: str, *, protected: bool = False) -> AssetRecord` (or a server-only staged-path API plus `register_asset`), specify exact store-root construction/wiring in `app/main.py`, keep returned paths server-only, and add the exact signature to both PRODUCES/CONSUMES and tests.

### Positive scope checks
- The three-child dependency chain is coherent: OJ-6xh3 blocks OJ-5uq4, and both block OJ-wfpy; `pvg nd dep cycles` found none.
- M0 remains a bounded brownfield slice rather than a rewrite: SQLite workspace state, immutable media, existing job artifacts, current Python/FastAPI/browser app, and legacy readers align with `SUPER_APP_BLUEPRINT.md` lines 76-96 and the M0 boundary at line 222.
- The backlog explicitly preserves the no-project flow, C1 lineage, attestation/status/review semantics, keepers, and local-only/no-spend boundary; broader scene/engine/hosting work remains later-milestone scope consistent with `SUPER_APP_BLUEPRINT.md` lines 216-228 and `IMPLEMENTATION_HANDOFF.md` lines 16-18, 38-52.
- OJ-5uq4 correctly describes a one-performer primary/optional-secondary reference bundle and explicitly rejects two-person recasting semantics.
- OJ-wfpy is a positive, all-dependency local user-path capstone: actual loopback uvicorn, SQLite/filesystem/HTTP/browser/FFmpeg, explicit dry-run, restart/reopen, no mocks, public-safe evidence, and legacy-flow regression.
- Safe asset-ID resolution is otherwise well specified: opaque IDs, recorded relative location, regular-file/symlink/traversal/integrity checks, safe public records, and server-only `ResolvedAsset.path`.

### Evidence
- `pvg lint --backlog --epic OJ-mnrv --json` => `[]` (exit 0), so this rejection is judgment-based, not a mechanical lint failure.
- `pvg settings design.machinery` => `off`; machinery gates/RTM were therefore not required. The separately reported zero-tagged-requirement RTM was not treated as coverage proof.
- Vault gap searches against the live nd root returned no matching walking-skeleton/integration/testing pattern notes; the default `Claude` vault lookup was not used.
- `pvg issues show OJ-mnrv/OJ-6xh3/OJ-5uq4/OJ-wfpy` and `pvg nd show ...` were reviewed; `pvg nd dep tree OJ-mnrv` and `pvg nd dep cycles` were run.
- Exact current consumed signatures verified: `PreparedJob.to_json` and `prepare_workflow(...)` at `src/openjutsu/pipeline.py` lines 15-43; `verify_manifest(...)` at `src/openjutsu/evidence.py` lines 240-244; existing epoch/request isolation and prepare/run/review behavior at `app/web/studio.js` lines 7-11, 274-289, and 292-355.
- Relevant architecture excerpts reviewed: `SUPER_APP_BLUEPRINT.md` lines 76-96 and 216-228; `IMPLEMENTATION_HANDOFF.md` lines 12-18 and 38-52.
- Bounded review only: no full test rerun, provider/GPU call, source edit, issue acceptance/closure, push, credential use, or publication.

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

Foundation children: OJ-6xh3 (store), OJ-5uq4 (connected app), OJ-wfpy (all-dependency E2E capstone). Old submission epic OJ-fglb preserved. Source-code commit/merge permission has been requested separately; no source work or loop rotation performed.
Owner authorization 2026-10-26: build the connected studio foundation using Paivot. Local source-code commits and merges only. No pushes, publication, credentials, provider/GPU jobs or GPU/API spending. Supersedes earlier pending-commit-approval sentence. Root preflight:126 passed,1 disclosed Starlette/httpx warning. Existing old submission epic and its issues remain unchanged.
Dispatcher preflight: local-only source commits/merges explicitly authorized; foundation backlog structural repair is assigned to foundation_backlog_repair. Existing accepted architecture and full product scope preserved. Epic branch/worktree epic/OJ-mnrv/.claude/worktrees/epic-OJ-mnrv created from main c2a18a5 without switching main or touching pre-existing evidence. No developer dispatched before structural lint and independent Anchor approval. SQLite/temp filesystem/FFmpeg and root Python3.11.11 venv available. Use temporary Git transport guard for loop setup automatic remote sync; use pvg nd sync --no-push at manual sync boundaries. No source changes, no provider/GPU calls.
User explicitly redirected work: "Ok let’s build the foundation now using Paivot. Local commits and merges only, no pushes or GPU spending." Existing OJ-fglb loop has no in-progress work and is stale from2026-10-18. Switching its execution scope to OJ-mnrv preserves OJ-fglb and all child issue states; this is owner-directed scope change, not autonomous abandonment.

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


## Links
## Comments

### 2026-10-27T05:27:17Z speed
Integration boundary: accepted OJ-6xh3 locally merged as a3bc898. Coordinator independently reran credential-stripped full pytest from integration worktree: 130 passed,1 disclosed Starlette/httpx warning in24.42s; compileall PASS and both source/test hashes matched delivery. New finding: public PreparedConfigRecord.config contains full workflow JSON instead of safe allowlist. SrPM bug triage requested before UI history exposure. Main remains c2a18a5; no pushes/GPU/render/provider work.
