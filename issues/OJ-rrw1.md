---
id: OJ-rrw1
title: "Add opt-in C1 recipe selection"
status: in_progress
priority: 1
type: task
labels: [contest, local, integration, walking-skeleton, delivered]
parent: OJ-fglb
created_at: 2026-10-22T03:15:29Z
created_by: speed
updated_at: 2026-10-22T03:28:47Z
content_hash: "sha256:e63a9e194fcbd7c54dc899a171d6c14fb27a62ce7e2fc20708f2366a558710f7"
blocks: [OJ-oc1m, OJ-xodm]
assignee: dev-OJ-rrw1
follows: [OJ-g2xx]
---

## Description

## Description
## USER INTENT
As the owner, I want an opt-in named C1 recipe in the existing Studio prepare path, so I can reproduce the accepted C1 graph contract with new authorized media while the legacy default and frozen keeper artifact remain unchanged.

## Context (Embedded)
- Baseline main: `d9c8e805c4a1e56b7860a5087c57ceb9e0ee37fd`; dispatcher baseline: `105 passed`, one disclosed existing Starlette/httpx warning, `pip check` clean.
- Default template: `workflows/openjutsu_h3_lipsync_local.json`, SHA-256 `06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21`; it must remain byte-for-byte unchanged.
- Provenance only (do not copy, move, or modify): `work/recast-engines/reference-recast-jay-v1/renders/keepers/c1_jay_20261021/workflow_api.json`, SHA-256 `1bf97e171b9e947160d5992c12d6286eca5905570f42993d9639acf0b938e129`. Its media/prompt/system_stats/private configuration stay frozen and out of this story.
- Current callers are `src/openjutsu/pipeline.py::prepare_workflow`, `app/main.py::prepare`, and `src/openjutsu/cli.py::command_prepare`.
- Exact C1 graph deltas versus the legacy template (excluding runtime prompt/planner media fields): remove node `1192`; node `64.model=["586",0]` and turbo filename `minimax_h3_dmd_ref2va_8step_turbo_pruned.safetensors`; node `586` uses `minimax_h3_character_swap_v1.1_ref2va_fro.safetensors` at strength `1.0`; node `1177` uses `use_ref_2=true`, `source_blur="head + hands (keep mouth)"`, `source_blur_strength=1.0`, `source_blur_segmenter="SAM 3.1"`, and `source_blur_effect="blur"`; add nodes `200` (`MiniMaxH3TimedAudio`) and `201` (`MiniMaxH3ExactAudioLock`), with node `201` receiving node `1177` output 1 and node `200`, and change node `14.latent_image=["201",0]`. Seed remains caller-selected (default 49), scheduler steps 8, `with_audio=true`, aligned guide, and both output prefixes remain parameterized by job ID.
- Do not claim a byte-identical future GPU render or eye-perfect output. The accepted keeper remains human-accepted with a disclosed blink mismatch.

## OUT OF SCOPE
- Real rendering, GPU/provider spend, credentials, model downloads, public exposure, push, posting, or submission: owner-gated; never in this story.
- Copying Jay runtime photos/video, frozen prompt text, system stats, private configs, or altering the keeper folder: preserve frozen provenance.
- Take/review UX improvements, public sample selection, and later public sample work: record below, do not start.
- Changing legacy defaults, rights semantics, readiness semantics, backend runners, or deployment assets: preserve behavior.

## DIFF BUDGET
- ~6-10 files, under 500 changed non-template LOC. Gross overrun mandates PM investigation.

## Boundary Map
PRODUCES:
- `src/openjutsu/workflow.py` -> `configure_workflow(template: dict[str, Any], *, video_name: str, reference_1: str, reference_2: str | None, prompt: str, seed: int = 49, output_prefix: str = "openjutsu/result", with_audio: bool = True, preset: str = "legacy") -> dict[str, Any]`
- `src/openjutsu/pipeline.py` -> `prepare_workflow(..., preset: str = "legacy") -> tuple[PreparedJob, dict[str, Any]]`, with `PreparedJob.preset: str`
- `app/main.py` -> `POST /api/prepare` multipart field `preset` (omitted/default = `legacy`; `c1` = C1)
- `src/openjutsu/cli.py` -> `openjutsu prepare --preset {legacy,c1}`
- `app/web/index.html` + `app/web/studio.js` -> accessible opt-in recipe selector and truthful C1 second-reference requirement
- tests under `tests/` -> deterministic offline graph/API/UI/CLI proof

CONSUMES:
- (existing): `src/openjutsu/workflow.py` -> `load_workflow(path: str | Path) -> dict[str, Any]`
- (existing): `src/openjutsu/scene.py` -> `analyze_scene(path: str | Path, ffprobe: str = "ffprobe") -> SceneReport`
- (existing): `app/main.py` -> `_public_manifest(job: object) -> dict`, which must continue redacting paths to filenames
- (existing): `src/openjutsu/cli.py` -> `command_prepare(args: argparse.Namespace) -> int`

## Acceptance Criteria
1. **State / default preservation:** With no `preset` field, CLI/API/pipeline calls produce the same legacy graph semantics as `main`; the default workflow SHA remains `06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21`, node `1192` remains present, and existing rights/public-filename gates remain unchanged.
2. **C1 graph:** `preset="c1"` deterministically applies every exact graph delta listed in Context to a copied graph, parameterizes only runtime media filenames, prompt, seed, output prefixes, and source planner geometry, and never reads or mutates the frozen keeper folder at runtime.
3. **Reference contract:** Legacy accepts an optional second reference. C1 fails closed with `WorkflowError`/pipeline `ValueError` (API HTTP 422; CLI nonzero) when `reference_2` is absent; it never downgrades C1 to one-reference legacy behavior. A supplied C1 pair routes only runtime basenames into planner fields and `use_ref_2=true`.
4. **Audio and sampler routing:** Prepared C1 includes nodes `200` and `201`, routes `1177` output 1 plus timed audio into `201`, and makes `SamplerCustomAdvanced` node `14` sample node `201` output 0. Tests inspect actual node links, not only class names.
5. **Geometry handling:** C1 derives planner FPS/frame window from the actual source rather than copying frozen `fps=24,start_f=0,end_f=141`. A source already matching a supported H3 window produces that window; unsupported geometry fails closed with an explicit error or returns an explicit geometry decision—never a silent clamp/truncate to 141. Tests distinguish exact C1 graph replay from a different valid frame window.
6. **API/UI/CLI opt-in:** The UI exposes only `legacy` and `c1`, defaults to legacy, labels C1 truthfully, makes the second reference required only for C1, and includes `preset` in the public manifest. `/api/prepare` and CLI prepare both prove the C1 path; no local absolute path or media bytes appear in API responses.
7. **Unknown recipe:** Any value other than `legacy` or `c1` fails closed before graph/job write/API success, with a deterministic message and no fallback.
8. **Offline proof:** Added tests use committed synthetic fixtures or runtime-generated tiny media only; they run without ComfyUI, GPU, SDK credentials, model downloads, or network. They cover legacy regression, C1 success, absent second reference, unknown preset, API/UI selectors/manifest, CLI compatibility, default-template hash, and frozen provenance hash.

## Testing Requirements
- Unit: focused `configure_workflow` tests for every C1 delta, legacy default, optional versus required reference 2, unknown preset, and source geometry branch.
- Integration: MANDATORY real app-path integration (no mocks) through `/api/prepare` with `dry_run` settings; inspect persisted `workflow.json` and public response.
- CLI: run `openjutsu prepare` for legacy and C1 (or invoke `build_parser`/`command_prepare` directly without network) and assert compatibility/default behavior.
- Frontend/static: deterministic parser/JS assertions for selector, accessible labels, dynamic second-reference requirement, and no fabricated quality/progress claims.
- Commands: focused tests, then `PYTHONPATH=src .venv/bin/python -m pytest -q`; run `.venv/bin/python -m pip check`; verify both workflow SHA-256 values above where applicable; run `git diff --check`.

## Skills To Use
- None identified.

## Delivery Requirements
- Paste exact commands/output and a per-AC verification table.
- Include nonempty exact `LEARNINGS:` and relevant `OBSERVATIONS:`.
- Do not run or claim rendering; keep local/SDK readiness semantics truthful and owner-gated.
- Record any intentional behavior difference as differential evidence rather than claiming legacy byte identity.

## Deferred Follow-ups (do not start)
- Take/review UX for choosing/reviewing recipes.
- Public rights-cleared C1 sample selection and presentation.
- Real local or hosted render proof; remains gated by `OJ-oc1m` and owner authorization.

## MANDATORY SKILLS
- None beyond the ordinary offline developer workflow; run deterministic pytest only. Do not invoke ComfyUI, the SDK, GPU, or network.

## nd_contract
status: new

### evidence
- Created from source inspection at main `d9c8e80`, frozen keeper `workflow_api.json` SHA-256 `1bf97e171b9e947160d5992c12d6286eca5905570f42993d9639acf0b938e129`, and dispatcher baseline `105 passed` / `pip check` clean.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-22T03:15:30Z dep_added: blocks OJ-oc1m

## Links
- Parent: [[OJ-fglb]]
- Blocks: [[OJ-oc1m]]

## Comments

## USER INTENT
As the owner, I want an opt-in named C1 recipe in the existing Studio prepare path, so I can reproduce the accepted C1 graph contract with new authorized media while the legacy default and frozen keeper artifact remain unchanged.

## Context (Embedded)
- Baseline main: `d9c8e805c4a1e56b7860a5087c57ceb9e0ee37fd`; dispatcher baseline: `105 passed`, one disclosed existing Starlette/httpx warning, `pip check` clean.
- Default template: `workflows/openjutsu_h3_lipsync_local.json`, SHA-256 `06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21`; it must remain byte-for-byte unchanged.
- Provenance only (do not copy, move, or modify): `work/recast-engines/reference-recast-jay-v1/renders/keepers/c1_jay_20261021/workflow_api.json`, SHA-256 `1bf97e171b9e947160d5992c12d6286eca5905570f42993d9639acf0b938e129`. Its media/prompt/system_stats/private configuration stay frozen and out of this story.
- Current callers are `src/openjutsu/pipeline.py::prepare_workflow`, `app/main.py::prepare`, and `src/openjutsu/cli.py::command_prepare`.
- Exact C1 graph deltas versus the legacy template (excluding runtime prompt/planner media fields): remove node `1192`; node `64.model=["586",0]` and turbo filename `minimax_h3_dmd_ref2va_8step_turbo_pruned.safetensors`; node `586` uses `minimax_h3_character_swap_v1.1_ref2va_fro.safetensors` at strength `1.0`; node `1177` uses `use_ref_2=true`, `source_blur="head + hands (keep mouth)"`, `source_blur_strength=1.0`, `source_blur_segmenter="SAM 3.1"`, and `source_blur_effect="blur"`; add nodes `200` (`MiniMaxH3TimedAudio`) and `201` (`MiniMaxH3ExactAudioLock`), with node `201` receiving node `1177` output 1 and node `200`, and change node `14.latent_image=["201",0]`. Seed remains caller-selected (default 49), scheduler steps 8, `with_audio=true`, aligned guide, and both output prefixes remain parameterized by job ID.
- Do not claim a byte-identical future GPU render or eye-perfect output. The accepted keeper remains human-accepted with a disclosed blink mismatch.

## OUT OF SCOPE
- Real rendering, GPU/provider spend, credentials, model downloads, public exposure, push, posting, or submission: owner-gated; never in this story.
- Copying Jay runtime photos/video, frozen prompt text, system stats, private configs, or altering the keeper folder: preserve frozen provenance.
- Take/review UX improvements, public sample selection, and later public sample work: record below, do not start.
- Changing legacy defaults, rights semantics, readiness semantics, backend runners, or deployment assets: preserve behavior.

## DIFF BUDGET
- ~6-10 files, under 500 changed non-template LOC. Gross overrun mandates PM investigation.

## Boundary Map
PRODUCES:
- `src/openjutsu/workflow.py` -> `configure_workflow(template: dict[str, Any], *, video_name: str, reference_1: str, reference_2: str | None, prompt: str, seed: int = 49, output_prefix: str = "openjutsu/result", with_audio: bool = True, preset: str = "legacy") -> dict[str, Any]`
- `src/openjutsu/pipeline.py` -> `prepare_workflow(..., preset: str = "legacy") -> tuple[PreparedJob, dict[str, Any]]`, with `PreparedJob.preset: str`
- `app/main.py` -> `POST /api/prepare` multipart field `preset` (omitted/default = `legacy`; `c1` = C1)
- `src/openjutsu/cli.py` -> `openjutsu prepare --preset {legacy,c1}`
- `app/web/index.html` + `app/web/studio.js` -> accessible opt-in recipe selector and truthful C1 second-reference requirement
- tests under `tests/` -> deterministic offline graph/API/UI/CLI proof

CONSUMES:
- (existing): `src/openjutsu/workflow.py` -> `load_workflow(path: str | Path) -> dict[str, Any]`
- (existing): `src/openjutsu/scene.py` -> `analyze_scene(path: str | Path, ffprobe: str = "ffprobe") -> SceneReport`
- (existing): `app/main.py` -> `_public_manifest(job: object) -> dict`, which must continue redacting paths to filenames
- (existing): `src/openjutsu/cli.py` -> `command_prepare(args: argparse.Namespace) -> int`

## Acceptance Criteria
1. **State / default preservation:** With no `preset` field, CLI/API/pipeline calls produce the same legacy graph semantics as `main`; the default workflow SHA remains `06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21`, node `1192` remains present, and existing rights/public-filename gates remain unchanged.
2. **C1 graph:** `preset="c1"` deterministically applies every exact graph delta listed in Context to a copied graph, parameterizes only runtime media filenames, prompt, seed, output prefixes, and source planner geometry, and never reads or mutates the frozen keeper folder at runtime.
3. **Reference contract:** Legacy accepts an optional second reference. C1 fails closed with `WorkflowError`/pipeline `ValueError` (API HTTP 422; CLI nonzero) when `reference_2` is absent; it never downgrades C1 to one-reference legacy behavior. A supplied C1 pair routes only runtime basenames into planner fields and `use_ref_2=true`.
4. **Audio and sampler routing:** Prepared C1 includes nodes `200` and `201`, routes `1177` output 1 plus timed audio into `201`, and makes `SamplerCustomAdvanced` node `14` sample node `201` output 0. Tests inspect actual node links, not only class names.
5. **Geometry handling:** C1 derives planner FPS/frame window from the actual source rather than copying frozen `fps=24,start_f=0,end_f=141`. A source already matching a supported H3 window produces that window; unsupported geometry fails closed with an explicit error or returns an explicit geometry decision—never a silent clamp/truncate to 141. Tests distinguish exact C1 graph replay from a different valid frame window.
6. **API/UI/CLI opt-in:** The UI exposes only `legacy` and `c1`, defaults to legacy, labels C1 truthfully, makes the second reference required only for C1, and includes `preset` in the public manifest. `/api/prepare` and CLI prepare both prove the C1 path; no local absolute path or media bytes appear in API responses.
7. **Unknown recipe:** Any value other than `legacy` or `c1` fails closed before graph/job write/API success, with a deterministic message and no fallback.
8. **Offline proof:** Added tests use committed synthetic fixtures or runtime-generated tiny media only; they run without ComfyUI, GPU, SDK credentials, model downloads, or network. They cover legacy regression, C1 success, absent second reference, unknown preset, API/UI selectors/manifest, CLI compatibility, default-template hash, and frozen provenance hash.

## Testing Requirements
- Unit: focused `configure_workflow` tests for every C1 delta, legacy default, optional versus required reference 2, unknown preset, and source geometry branch.
- Integration: MANDATORY real app-path integration (no mocks) through `/api/prepare` with `dry_run` settings; inspect persisted `workflow.json` and public response.
- CLI: run `openjutsu prepare` for legacy and C1 (or invoke `build_parser`/`command_prepare` directly without network) and assert compatibility/default behavior.
- Frontend/static: deterministic parser/JS assertions for selector, accessible labels, dynamic second-reference requirement, and no fabricated quality/progress claims.
- Commands: focused tests, then `PYTHONPATH=src .venv/bin/python -m pytest -q`; run `.venv/bin/python -m pip check`; verify both workflow SHA-256 values above where applicable; run `git diff --check`.

## Skills To Use
- None identified.

## Delivery Requirements
- Paste exact commands/output and a per-AC verification table.
- Include nonempty exact `LEARNINGS:` and relevant `OBSERVATIONS:`.
- Do not run or claim rendering; keep local/SDK readiness semantics truthful and owner-gated.
- Record any intentional behavior difference as differential evidence rather than claiming legacy byte identity.

## Deferred Follow-ups (do not start)
- Take/review UX for choosing/reviewing recipes.
- Public rights-cleared C1 sample selection and presentation.
- Real local or hosted render proof; remains gated by `OJ-oc1m` and owner authorization.

## nd_contract
status: new

### evidence
- Created from source inspection at main `d9c8e80`, frozen keeper `workflow_api.json` SHA-256 `1bf97e171b9e947160d5992c12d6286eca5905570f42993d9639acf0b938e129`, and dispatcher baseline `105 passed` / `pip check` clean.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes
PROOF: Implementation commit 40aa30b772f4cbf9f475318bbd6e787e25cb1af4 on story/OJ-rrw1. Nine files changed, 390 insertions and 9 deletions. Full test suite: 119 passed, 0 failures, 0 skipped, one disclosed Starlette deprecation. pvg gates --changed d9c8e80: PASS, one controls complexity warning. pvg story verify-tdd --base d9c8e80: PASS, one commit checked, no unauthorized test edits. Whole-repository gates remain FAIL as detailed below; no claim of global gate success. No line-coverage measurement available. Acceptance coverage: 8/8 mapped to concrete tests and hash evidence.
Post-commit verification at 40aa30b772f4cbf9f475318bbd6e787e25cb1af4: PYTHONPATH=src $ROOT/.venv/bin/python -m pytest -q completed synchronously: 119 passed, 1 disclosed warning in 27.00s; no background work remains.

# OJ-rrw1 — offline C1 preparation proof

Base: `d9c8e805c4a1e56b7860a5087c57ceb9e0ee37fd`. Branch: `story/OJ-rrw1`.
The implementation commit is recorded in the append-only story delivery notes.
`ROOT` below means the main Openjutsu checkout; all commands ran from its
`.claude/worktrees/dev-OJ-rrw1` worktree, using the existing `$ROOT/.venv`.

## PROOF:

Commands and measured results:

```sh
PYTHONPATH=src "$ROOT/.venv/bin/python" -m pytest -q tests/test_c1_recipe.py tests/test_workflow.py tests/test_app_e2e.py tests/test_frontend_regression.py
# 23 passed, 1 warning in 9.19s
PYTHONPATH=src "$ROOT/.venv/bin/python" -m pytest -q
# 119 passed, 1 warning (0 failures, 0 skipped)
"$ROOT/.venv/bin/python" -m pip check
# No broken requirements found.
git diff --check
# exit 0, no output
pvg verify src/openjutsu/workflow.py src/openjutsu/pipeline.py src/openjutsu/cli.py app/main.py app/web/index.html app/web/studio.js tests/test_c1_recipe.py workflows/README.md --format=text
# VERIFY: PASSED (6 files scanned, 0 issues)
pvg gates src/openjutsu/workflow.py src/openjutsu/pipeline.py src/openjutsu/cli.py app/main.py app/web/index.html app/web/studio.js tests/test_c1_recipe.py workflows/README.md
# GATES: PASS (1 warn, 0 skipped); controls() CCN 29 > 15
pvg gates
# GATES: FAIL (16 block, 11 warn, 0 skipped)
shasum -a 256 workflows/openjutsu_h3_lipsync_local.json
# 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21
shasum -a 256 "$ROOT/work/recast-engines/reference-recast-jay-v1/renders/keepers/c1_jay_20261021/workflow_api.json"
# 1bf97e171b9e947160d5992c12d6286eca5905570f42993d9639acf0b938e129
```

Acceptance coverage: 8/8 ACs mapped below; Python line coverage was not measured
(coverage package unavailable; no dependency installation attempted).

| AC | Verifiable proof |
|---|---|
| 1 | Immutable template SHA; `test_graph_contract_and_immutable_template`; full legacy suite; real API and CLI default branches retain node 1192. |
| 2 | Whole-dictionary C1 comparison against sanitized expected deltas; deepcopy equality; only runtime prompt/media/seed/prefix/window vary. Runtime has no keeper dependency. |
| 3 | Missing second ref raises WorkflowError/direct or ValueError/pipeline, HTTP 422/API, nonzero/CLI; legacy real API accepts absent second ref. |
| 4 | Whole-dictionary contract asserts exact 200/201 inputs and 14 latent link; API persisted graph independently checked. |
| 5 | Real generated 124-, 141-, 158-frame sources retain their complete windows; 107/144/362 frames, 25fps, and absent audio fail closed before job creation. |
| 6 | No-mock TestClient prepare writes graph and manifest; public basenames/preset asserted; CLI runs actual preparation; HTML parser/static JS prove named/labelled selector, conditional ref2 requirement, FormData and epoch invalidation. |
| 7 | Unknown preset rejected at configure/pipeline/API/CLI; API validation precedes upload/job creation, pipeline validation precedes source reads and job writes. |
| 8 | 14 new offline cases, 119 total passing; tiny runtime ffmpeg color/sine sources and existing synthetic reference only. Immutable provenance hash manually verified, not required by portable tests. |

## LEARNINGS:

- The inherited planner window is 141 frames; actual decoded timestamps/count are
  necessary to avoid silently truncating different sources. This recipe accepts
  the existing 5–15 second envelope at CFR24 on the H3 17n+5 grid, not arbitrary
  inputs or a new normalization algorithm.
- C1 removes a legacy-required node, so required-node validation must branch
  before legacy-only Head Swap strength mutation.
- Public manifest redaction already handles the new scalar preset without
  exposing filesystem paths. Preparation is not rendering, readiness or QC.

## OBSERVATIONS:

- Whole-repository metric gates remain blocked: 23.3% duplication (>10%), with
  15 individual duplication blocks in historical `docs/evidence` JSON receipts,
  workflows and probes (OJ-2gs4, OJ-2t3g, OJ-vwzl, OJ-inuo, OJ-xtk4).
  Eleven complexity warnings include Studio controls and ten other functions.
  Scoped changed-file gates pass, but this is **not** a whole-repository gate pass.
- DISCOVERED_BUG: Starlette test-client import emits
  `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
  Reproduced by the full pytest command above. Dependency migration is outside
  this recipe change; no warning was suppressed.
- `pvg notes search C1` cannot reach its configured `Claude` vault (not found).
- No GPU, model inference/downloads, SDK/network execution, public exposure,
  credential access, remote push or submission occurred. No render-quality claim.
- Differential behavior: manifests now include `preset`; failed preparations
  no longer create an empty job directory before graph validation.

## History
- 2026-10-22T03:15:30Z dep_added: blocks OJ-oc1m
- 2026-10-22T03:20:42Z dep_added: blocks OJ-xodm
- 2026-10-22T03:20:56Z status: open -> in_progress
- 2026-10-22T03:20:56Z auto-follows: linked to predecessor OJ-g2xx
- 2026-10-22T03:20:56Z claimed by dev-OJ-rrw1
- 2026-10-22T03:28:46Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-fglb]]
- Blocks: [[OJ-oc1m]], [[OJ-xodm]]
- Follows: [[OJ-g2xx]]

## Comments
