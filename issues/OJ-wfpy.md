---
id: OJ-wfpy
title: "E2e: return to a saved project with reusable character references in Studio"
status: in_progress
priority: 1
type: task
labels: [studio, foundation, local, no-spend, capstone, e2e, delivered]
parent: OJ-mnrv
created_at: 2026-10-27T03:45:29Z
created_by: speed
updated_at: 2026-10-27T10:29:16Z
content_hash: "sha256:d11311f659cc1bf59fcd742e989328e1393b06b2afc3d57a691f166f6b6ec4f3"
was_blocked_by: [OJ-6xh3, OJ-8zaw, OJ-5uq4, OJ-m439, OJ-0ij6]
follows: [OJ-6xh3, OJ-8zaw, OJ-5uq4, OJ-m439, OJ-0ij6, OJ-r6n5]
blocked_by: [OJ-r6n5]
assignee: dev-OJ-wfpy
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
## Implementation Evidence (REWORK DELIVERED)

### CI/Test Results
Commands run:
- git diff --name-only 709ceb5..66ddca0
- git diff --check
- test -f docs/evidence/studio-foundation/browser-cycle-1.log && test -f docs/evidence/studio-foundation/browser-cycle-2.log
- shasum -a 256 docs/evidence/studio-foundation/browser-cycle-1.log docs/evidence/studio-foundation/browser-cycle-2.log
- pvg verify docs/evidence/studio-foundation/README.md --format=text

Summary: documentation-only correction PASS. The sole changed path is docs/evidence/studio-foundation/README.md. Commit 66ddca0 changes exactly two README table rows from nonexistent browser-server-cycle-*.log names to the actual committed browser-cycle-*.log paths. Both files exist and their SHA-256 values remain 6e510dd70c1f95613d783afbe581ae87f522f5af51b4ba96db1ff1614b4cc8a0 and 231c5f5791c0e77dded9617976bd926dea6c3a19674a13d0f17582e035dc8968. git diff --check PASS; README pvg verify PASS (0 scannable source files by design). No code, test, artifact, receipt, production, or other file changed, so behavioral reruns were not run per the PM's explicit documentation-only rework instruction.

Commit SHA: 66ddca0

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | Prior real-process foundation proof remains unchanged | Retained commits through 709ceb5 | Prior evidence in this story | PASS |
| 2 | Prior saved-reference/dry-run/browser journey remains unchanged | Retained commits through 709ceb5 | Prior evidence in this story | PASS |
| 3 | Prior restart persistence proof remains unchanged | Retained commits through 709ceb5 | Prior evidence in this story | PASS |
| 4 | Prior nonmutation/error-path proof remains unchanged | Retained commits through 709ceb5 | Prior evidence in this story | PASS |
| 5 | Human-readable evidence index now names actual public-safe artifacts | docs/evidence/studio-foundation/README.md:66-67 | Path/hash verification above; a225746 artifacts unchanged | PASS |
| 6 | Documentation-only correction is commit-bound, scoped, and preserves prior gate results | Commit 66ddca0; prior gate evidence | git diff/path/hash outputs above | PASS |

LEARNINGS:
- A hand-written evidence index must be checked against the actual file inventory, not only the generated receipts whose embedded metadata is correct.
- The PM correctly scoped this as documentation-only: renaming the index rows to existing artifacts preserves all underlying evidence and avoids unnecessary behavioral reruns.

OBSERVATIONS:
- The two log artifacts and all receipts/screenshots were not renamed or modified.
- No push, acceptance, story merge, provider/GPU spend, or external action occurred.

## nd_contract
status: delivered

### evidence
- Prior substantive delivery: 709ceb5. Documentation-only rework: 66ddca0.
- Correct README rows and artifact hashes verified above; worktree is clean.

### proof
- [x] AC #1 through AC #6 pass with the corrected evidence index; AC #5/AC #6 documentation defect from PM rejection is resolved without changing behavior.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-27.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

### CI/Test Results
Commands run:
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m pytest -q tests/test_foundation_e2e.py
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" tools/foundation_trial.py --temp-root /tmp/oj-wfpy-http-receipt --evidence-root docs/evidence/studio-foundation
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m pytest -q
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src "$APP/.venv/bin/python" -m compileall -q .
- /opt/homebrew/opt/node@22/bin/node --check app/web/projects.js
- /opt/homebrew/opt/node@22/bin/node --check app/web/studio.js
- pvg verify tools/foundation_trial.py tools/foundation_runtime.py tests/test_foundation_e2e.py docs/evidence/studio-foundation/README.md --include-tests --format=text
- pvg gates tools/foundation_trial.py tools/foundation_runtime.py tests/test_foundation_e2e.py docs/evidence/studio-foundation/README.md
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH="$APP/src" "$APP/.venv/bin/python" "$APP/tools/verify_keeper_evidence.py" "$APP/docs/evidence/slate/manifest.json"

Summary: focused E2E PASS (1 passed in 2.10s); replay PASS (job b703393027e7); full suite PASS (187 passed, 1 known StarletteDeprecationWarning, 27.18s); compileall PASS; both node --check commands PASS; pvg verify PASS (3 files scanned, 0 issues); pvg gates PASS (2 advisory warnings, 0 skipped); keeper verifier PASS (11 keepers, 48 artifacts). Actual CUA journey completed in a rendered visible=false IAB tab using two owned uvicorn cycles and the same temporary SQLite workspace; final owned-browser-tab count was 0 and the 127.0.0.1:18765 listener count was 0.

Commit SHA: 709ceb5 (story/OJ-wfpy; includes authorized no-conflict epic merge c57dd92, collision proof e964b3b, evidence a225746, and evidence README f4880e2/709ceb5).

Evidence artifacts:
- docs/evidence/studio-foundation/http-receipt.json — SHA-256 2c408c2cce4b58972bd018efe3f8c19064d4d806af8d0e767e162c3c35c31746
- docs/evidence/studio-foundation/browser-receipt.json — SHA-256 2b5d171974e7277e24e9b3f43b7bcd2fadc0788fa2653d5ec0f8305cf95c8377
- docs/evidence/studio-foundation/browser-workspace-receipt.json — SHA-256 567061e7a4bd0f0075a555f1cc6206ef7a6285d7ae83cfaf1b855bf8780f6c0c
- docs/evidence/studio-foundation/README.md — exact command/hash index and cleanup proof

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | Actual loopback uvicorn, strict dry-run child env, real SQLite/filesystem/HTTP/FFmpeg/media | tools/foundation_runtime.py:41-101,168-223; tools/foundation_trial.py:62-119 | tests/test_foundation_e2e.py:11-42; http-receipt.json | PASS |
| 2 | Project, protected saved version, saved-reference prepare, explicit dry-run, safe previews/config/downloads/history | tools/foundation_trial.py:121-291 | tests/test_foundation_e2e.py:17-38; browser-receipt.json journey/screenshots 01-04 | PASS |
| 3 | Actual stop/restart/reopen persistence without automatic run; legacy/no-project flow remains real | tools/foundation_trial.py:293-374 | tests/test_foundation_e2e.py:24-40; browser-receipt.json restart; screenshots 04-05 | PASS |
| 4 | Version reselection/reset/project switch preserve old bytes/hashes/history; missing/conflict/duplicate inputs are actionable nonmutations | tools/foundation_trial.py:137-216,375-424 | tests/test_foundation_e2e.py:26-34; browser-workspace-receipt.json; screenshots 05-08 | PASS |
| 5 | Public-safe browser+HTTP receipts/screenshots, no secrets/user paths/provider submissions/tunnel, loopback and stopped owned processes | tools/foundation_runtime.py:39-59,212-223,265-274; docs/evidence/studio-foundation/README.md | tests/test_foundation_e2e.py:36-42; public-safe scan and cleanup evidence | PASS |
| 6 | Full suite, compileall, JS checks, pvg verify/gates, keeper verifier, actual warnings/hashes/results | docs/evidence/studio-foundation/README.md:49-78 | command outputs above | PASS |

### pvg verify
VERIFY: PASSED (3 files scanned, 0 issues)

### Keeper verifier
PASS: canonical docs/evidence/slate/manifest.json; keeper_count=11; artifact_count=48; manifest_sha256=ada599a6e327b83e3b426bece75887f2b1d3a1aa1180047bbf6edd24e8659d33

LEARNINGS:
- Keep replayable HTTP proof and agent-operated rendered-browser proof separate; the Python helper can prove process/data persistence, but only the CUA receipt can claim actual browser interactions.
- A 320x180 one-second synthetic source is useful as an intentional nonrecommended preflight control, while a 640x360 two-second source unlocks the existing explicit Run button without changing production behavior.
- Pre-restart byte comparison must separately explain workspace.sqlite3: every protected media/config hash stayed unchanged, while the database changed exactly to add the expected post-restart uploaded-reference history.
- The strict child environment belongs in shared runtime code so both server cycles reuse the same allowlist, loopback binding, FFmpeg pinning, SQLite reader, redaction, and stop path.
- The upstream accepted collision/reset merges integrated without production conflicts; extending only owned E2E evidence kept the capstone boundary clean.

OBSERVATIONS:
- The full suite retains the known third-party StarletteDeprecationWarning from fastapi.testclient; all 187 tests ran and passed.
- pvg gates reports advisory warnings for run_trial complexity 21 and 423 nonblank lines; the four-file owned diff is 778 lines because the reusable runtime helper extraction is 272 lines. No production/API/store/frontend/pipeline/workflow/verifier/fixtures files were edited by this story after the authorized epic merge.
- The first CUA label-triggered file chooser timed out and reset the CUA kernel; one documented retry using the actual input plus filechooser event succeeded. Two exact-text waits missed longer concatenated UI messages; fresh DOM state captured the actual visible messages. ResourceTiming was not used.
- An initial direct replay invocation with only PYTHONPATH=src failed to import local tools; the successful replay uses PYTHONPATH=src:.. A nonexistent docs/evidence/studio-fudio shell typo also returned a file error but did not affect artifacts or checks.
- No creative provider, GPU, Colab, external destination, push, publication, or tunnel was used. Owned browser/server cleanup completed.

## nd_contract
status: delivered

### evidence
- Authorized no-conflict epic merge: c57dd92. Tested collision/nonmutation extension: e964b3b. Captured evidence: a225746. Final evidence/docs: 709ceb5.
- Full gate outputs, artifact hashes, exact paths, cleanup counts, screenshots, browser/HTTP receipts, and job IDs are recorded above and under docs/evidence/studio-foundation/.

### proof
- [x] AC #1: actual loopback uvicorn/SQLite/filesystem/HTTP/FFmpeg journey with strict dry-run child environment.
- [x] AC #2: project + protected version + saved-reference prepare + explicit dry-run + safe previews/downloads/history.
- [x] AC #3: actual stop/restart/reopen persistence and no automatic run; real legacy flow exercised.
- [x] AC #4: selection/reset/switch nonmutation and actionable 422/404 failures with no misleading job state.
- [x] AC #5: public-safe actual browser/HTTP receipts and zero secret/provider/tunnel exposure with loopback cleanup.
- [x] AC #6: all mandatory suites/checks/gates/keeper verifier run with results, warning, hashes, and ownership reported.

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
- 2026-10-27T05:33:55Z dep_added: blocked_by OJ-8zaw
- 2026-10-27T05:45:32Z dep_removed: was_blocked_by OJ-8zaw
- 2026-10-27T07:25:45Z dep_removed: was_blocked_by OJ-5uq4
- 2026-10-27T07:31:04Z status: open -> in_progress
- 2026-10-27T07:31:04Z auto-follows: linked to predecessor OJ-6xh3
- 2026-10-27T07:31:04Z auto-follows: linked to predecessor OJ-8zaw
- 2026-10-27T07:31:05Z auto-follows: linked to predecessor OJ-5uq4
- 2026-10-27T07:31:05Z claimed by dev-OJ-wfpy
- 2026-10-27T08:34:23Z status: in_progress -> open
- 2026-10-27T08:34:23Z released by speed
- 2026-10-27T08:50:21Z dep_added: blocked_by OJ-0ij6
- 2026-10-27T08:50:21Z dep_added: blocked_by OJ-m439
- 2026-10-27T08:53:00Z dep_added: blocked_by OJ-r6n5
- 2026-10-27T09:18:45Z dep_removed: was_blocked_by OJ-m439
- 2026-10-27T09:29:41Z dep_removed: was_blocked_by OJ-0ij6
- 2026-10-27T09:33:15Z status: open -> in_progress
- 2026-10-27T09:33:15Z auto-follows: linked to predecessor OJ-m439
- 2026-10-27T09:33:15Z auto-follows: linked to predecessor OJ-0ij6
- 2026-10-27T09:33:15Z claimed by dev-OJ-wfpy
- 2026-10-27T10:08:39Z status: in_progress -> in_progress
- 2026-10-27T10:08:39Z auto-follows: linked to predecessor OJ-r6n5
- 2026-10-27T10:24:28Z status: in_progress -> open
- 2026-10-27T10:24:28Z released by speed
- 2026-10-27T10:26:55Z status: open -> in_progress
- 2026-10-27T10:26:55Z claimed by dev-OJ-wfpy
- 2026-10-27T10:29:16Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-mnrv]]
- Blocked by: [[OJ-r6n5]]
- Was blocked by: [[OJ-6xh3]], [[OJ-8zaw]], [[OJ-5uq4]], [[OJ-m439]], [[OJ-0ij6]]
- Follows: [[OJ-6xh3]], [[OJ-8zaw]], [[OJ-5uq4]], [[OJ-m439]], [[OJ-0ij6]], [[OJ-r6n5]]

## Comments

### 2026-10-27T08:34:23Z speed
Developer explicitly HOLDed pending upstream Anchor P0 fixes, not delivered. Preserved local commits84d52ce and3dcb225, focused actualHTTP/SQLite/uvicorn-restart E2E1pass, compileall/verify/gatesPASS advisoryonly. Partialbrowser stoppedbeforeprepare/run; ownIABclosed,uvicornPID21597stopped/18971closed. Removedcleanworktree, releasedclaim while newbugdependencies are triaged; branch/artifacts remain. Finishactualbrowser/fullgateproof onlyafteracceptedupstreamfixes.

### 2026-10-27T10:09:43Z speed
## Implementation Evidence

### CI/Test Results
Commands run: See the authoritative Implementation Evidence block in Notes and docs/evidence/studio-foundation/README.md.
Summary: focused E2E 1 passed in 2.10s; HTTP replay job b703393027e7 PASS; full suite 187 passed with 1 known StarletteDeprecationWarning in 27.18s; compileall PASS; projects.js and studio.js node --check PASS; pvg verify PASS; pvg gates PASS with 2 advisory warnings; keeper verifier PASS for 11 keepers/48 artifacts. Actual CUA restart journey and cleanup are captured in browser-receipt.json.
Commit SHA: 709ceb5

## nd_contract
status: delivered

### evidence
- Final local story branch commit: 709ceb5.
- Public-safe evidence paths and SHA-256 hashes are recorded in Notes and docs/evidence/studio-foundation/README.md.

### proof
- [x] AC #1 through AC #6 verified with real HTTP, SQLite, filesystem, FFmpeg, uvicorn restart, and separate rendered-browser evidence.

### 2026-10-27T10:24:28Z speed
## PM Decision
REJECTED [2026-10-27]: The real-process and browser evidence is substantively strong, but the declared human-readable evidence index is not accurate for two committed artifacts.

EXPECTED: `docs/evidence/studio-foundation/README.md` is a declared capstone deliverable providing a replayable exact command/result and human-readable evidence index.
DELIVERED: README lines 66-67 name `browser-server-cycle-1.log` and `browser-server-cycle-2.log`; neither path exists. The actual committed logs are `docs/evidence/studio-foundation/browser-cycle-1.log` and `docs/evidence/studio-foundation/browser-cycle-2.log`, with the same SHA-256 values shown in the README.
GAP: The evidence index points readers to nonexistent paths. The underlying receipts name the correct files, but the required README index itself is not exact and would misdirect independent verification.
FIX: In a scoped documentation-only rework commit, rename the two README table entries to the actual `browser-cycle-1.log` and `browser-cycle-2.log` paths (do not rename artifacts or change production/test code). Re-run `pvg story verify-delivery OJ-wfpy`; no behavioral test rerun is required for this documentation-only correction unless the rework touches anything else.

### Independent review evidence
- Live story preflight passed 9/9 at commit `709ceb5ee3c47541b584196fb96a78554881c75b` on clean `story/OJ-wfpy`.
- Verified capstone-only diff from authorized upstream `0a26d26888ab94ef2145fcad856de7067d6f8ff4`: 19 files, 2,688 insertions; authored files are 455 + 272 + 41 + 78 = 846 lines; no production path changed.
- Verified receipt hashes: HTTP `2c408c2cce4b58972bd018efe3f8c19064d4d806af8d0e767e162c3c35c31746`; browser `2b5d171974e7277e24e9b3f43b7bcd2fadc0788fa2653d5ec0f8305cf95c8377`; workspace `567061e7a4bd0f0075a555f1cc6206ef7a6285d7ae83cfaf1b855bf8780f6c0c`; slate manifest `ada599a6e327b83e3b426bece75887f2b1d3a1aa1180047bbf6edd24e8659d33`.
- Independently parsed all three receipts, matched all eight JPEG byte counts/hashes, visually inspected focused screenshots, confirmed synthetic test-pattern media, and found no `/Users/`, credential token, or non-loopback URL. HTTP receipt records 36 real requests including two explicit run requests; port 18765 and all four recorded server PIDs are now absent.

LEARNINGS:
- Validate declared evidence indices against `git ls-files`, not only against embedded receipt metadata: receipts can be correct while a hand-written README path drifts.
- The functional journey can be independently corroborated without another full test run when commit-bound receipts, logs, hashes, screenshots, and cleanup state agree.

OBSERVATIONS:
- No stubs, TODO markers, mocks, skips, warning suppression, production edits, secrets, provider/GPU spend, checkout, merge, or push were found in the capstone-only delta.
- The approximate 650-line budget is exceeded by 128 authored lines (846 total), explained by the reusable 272-line runtime helper; generated JSON/logs/JPEG account for the remainder and are public-safe. This overrun is not the rejection reason.

## nd_contract
status: rejected

### evidence
- PM independently reviewed live OJ-wfpy notes and capstone-only diff at `709ceb5`.
- README evidence-index path mismatch independently reproduced against the retained worktree and git file inventory.

### proof
- [ ] AC #5 (partial): screenshots/receipts are public-safe and substantively verified, but the declared README evidence index names two nonexistent artifact paths.
- [x] AC #1: strict allowlisted dry-run child environment, actual loopback uvicorn/SQLite/FFmpeg/HTTP evidence reviewed.
- [x] AC #2: saved project/version/reference, explicit dry-run, safe preview/download/history evidence reviewed.
- [x] AC #3: two-cycle restart persistence/no-autorun evidence reviewed.
- [x] AC #4: nonmutation and actionable 422/404 evidence reviewed.
- [ ] AC #6 (partial): reported command results and hashes are complete, but final human-readable evidence index accuracy fails the deliverable bar.
