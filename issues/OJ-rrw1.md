---
id: OJ-rrw1
title: "Add opt-in C1 recipe selection"
status: open
priority: 1
type: task
labels: [contest, local, integration, walking-skeleton]
parent: OJ-fglb
created_at: 2026-10-22T03:15:29Z
created_by: speed
updated_at: 2026-10-22T03:19:40Z
content_hash: "sha256:0a019e7357ee3d34eff0fcf7b391d43094634364b796cba95df40a6b3b794277"
blocks: [OJ-oc1m]
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


## History
- 2026-10-22T03:15:30Z dep_added: blocks OJ-oc1m

## Links
- Parent: [[OJ-fglb]]
- Blocks: [[OJ-oc1m]]

## Comments
