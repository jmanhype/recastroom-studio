---
id: OJ-xtk4
title: "Preserve paired-review aspect ratio"
status: closed
priority: 1
type: bug
labels: [bug, media, local, dogfood, accepted]
parent: OJ-a7l6
created_at: 2026-10-18T03:50:45Z
created_by: speed
updated_at: 2026-10-18T04:14:19Z
content_hash: "sha256:77e6ce6eb2d93a77c82a8b60197cdfb12d09dcbe6a759c17f8e49941ca9d8725"
assignee: dev-OJ-xtk4
follows: [OJ-4rht]
closed_at: 2026-10-18T04:14:18Z
close_reason: "Accepted: independent baseline RED replay, focused GREEN rerun, ffprobe/decoded measurements, byte-identical regeneration, hash verification, and scope review all support the aspect-ratio repair."
---

## Description

## Description
## Description
### Measured defect
The real dogfood paired review stretched both 3:2 inputs into 960x384 tiles, producing a 1920x384 / 5:1 comparison while the standalone final remained 3:2. The owner approved a bounded local export repair.

## Embedded Context
- Parent epic: OJ-a7l6.
- Baseline repository commit at intake: `7ab3b8c`; no repair tests have been run or claimed yet.
- Current code reference: `src/openjutsu/media.py:156-198`; `make_side_by_side(width=960, height=384)` scales each input to fixed dimensions at `src/openjutsu/media.py:175` before `hstack`.
- Dogfood evidence: `../frontend-evidence/dogfood-20261017/live/REPORT.md`, `browser-playback.json`, and `output-verification.json`.
- Measured final: 768x512, DAR 3:2, SHA-256 `f9091b391c96daf28697f46ba49263450112f70d1732fa26dcea73ccdadd2f98`.
- Measured comparison: 1920x384, DAR 5:1, SHA-256 `b2f61d3c292e53846f62bed6460d2b0517cbee7fd91c4b5d2f477aec84da613d`.
- Owner constraints: local deterministic work only; no GPU, paid API, cloud inference, publication, or push.

## Boundary Map
PRODUCES:
- `src/openjutsu/media.py` -> aspect-preserving paired-review video composition in `make_side_by_side`
- `tests/test_media.py` (or one focused existing/new media test module) -> deterministic 3:2, portrait, and 16:9 regression coverage
- `docs/evidence/dogfood-repairs/OJ-xtk4/` -> exact commands, ffprobe/PCM or pixel measurements, output hashes, and limitations

CONSUMES:
- (none -- leaf bug; local ffmpeg and read-only dogfood evidence are external inputs embedded above)

## Story Acceptance Criteria
1. Paired review scale-fits and pads each source and final frame onto a common even-width/even-height tile without cropping or changing each input's intrinsic display aspect ratio; sample aspect ratio remains square.
2. Mixed-aspect pairs are supported: regression evidence explicitly covers 3:2, portrait, and 16:9 inputs, including at least one pair whose input aspect ratios differ.
3. Regression tests use deterministic local media and assert both ffprobe geometry and decoded pixel/padding properties that distinguish correct scale-to-fit from stretch; they fail against the current fixed 960x384 stretch behavior.
4. The repair preserves local-only export semantics, introduces no generation/API redesign or new mandatory dependency, and does not alter unrelated media behavior.
5. The focused media tests and full repository suite pass locally; exact commands, outputs, artifact paths, and SHA-256 hashes are recorded. No result is claimed until actually run.

## Testing Requirements
- Generate all test inputs locally with ffmpeg/project-owned assets. Include 3:2, portrait, and 16:9 cases plus mixed aspect pairs.
- Use ffprobe and a deterministic decoded-frame check to prove intrinsic geometry, padding, even dimensions, and absence of stretch. Literal expected dimensions for each fixture must be stated in the test or test output.
- Commands to run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_media.py -q`, then `PYTHONPATH=src .venv/bin/python -m pytest`.
- Check in only small deterministic local fixtures/evidence needed to reproduce the result; no credentials, public URLs, cloud artifacts, GPU work, or external API calls.
- `git diff --check` must pass.

## MANDATORY SKILLS
- `tool-systematic-debugging`: establish the measured red geometry regression before changing export behavior.

## OUT OF SCOPE
- Audio channel layout, loudness, or speech-preservation changes: those belong to the serialized dependent audio bug.
- Generation workflow/API redesign, progress UX, remote services, GPU work, publication, or push.

## Ownership / Dependencies
- This story owns `src/openjutsu/media.py` first. The dependent audio bug must not start until this story is delivered/accepted because both require edits to the same file.

## nd_contract
status: new

### evidence
- Created from the measured 2026-10-17 dogfood receipt during bounded Sr-PM intake.

### proof
- [ ] AC #1: Aspect-preserving scale-to-fit/pad output with even dimensions and no crop/stretch.
- [ ] AC #2: 3:2, portrait, 16:9, and mixed-aspect regressions are covered.
- [ ] AC #3: Deterministic geometry/pixel tests fail on the measured stretch defect and pass after repair.
- [ ] AC #4: Local export boundary and unrelated behavior are preserved.
- [ ] AC #5: Focused/full tests, diff check, paths, hashes, and exact outputs are recorded.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T03:50:46Z dep_added: blocks OJ-inuo
- 2026-10-18T03:51:25Z status: open -> in_progress
- 2026-10-18T03:51:25Z claimed by dev-OJ-xtk4

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-inuo]]

## Comments


## Description
### Measured defect
The real dogfood paired review stretched both 3:2 inputs into 960x384 tiles, producing a 1920x384 / 5:1 comparison while the standalone final remained 3:2. The owner approved a bounded local export repair.

## Embedded Context
- Parent epic: OJ-a7l6.
- Baseline repository commit at intake: `7ab3b8c`; no repair tests have been run or claimed yet.
- Current code reference: `src/openjutsu/media.py:156-198`; `make_side_by_side(width=960, height=384)` scales each input to fixed dimensions at `src/openjutsu/media.py:175` before `hstack`.
- Dogfood evidence: `../frontend-evidence/dogfood-20261017/live/REPORT.md`, `browser-playback.json`, and `output-verification.json`.
- Measured final: 768x512, DAR 3:2, SHA-256 `f9091b391c96daf28697f46ba49263450112f70d1732fa26dcea73ccdadd2f98`.
- Measured comparison: 1920x384, DAR 5:1, SHA-256 `b2f61d3c292e53846f62bed6460d2b0517cbee7fd91c4b5d2f477aec84da613d`.
- Owner constraints: local deterministic work only; no GPU, paid API, cloud inference, publication, or push.

## Boundary Map
PRODUCES:
- `src/openjutsu/media.py` -> aspect-preserving paired-review video composition in `make_side_by_side`
- `tests/test_media.py` (or one focused existing/new media test module) -> deterministic 3:2, portrait, and 16:9 regression coverage
- `docs/evidence/dogfood-repairs/PENDING-ID/` -> exact commands, ffprobe/PCM or pixel measurements, output hashes, and limitations

CONSUMES:
- (none -- leaf bug; local ffmpeg and read-only dogfood evidence are external inputs embedded above)

## Story Acceptance Criteria
1. Paired review scale-fits and pads each source and final frame onto a common even-width/even-height tile without cropping or changing each input's intrinsic display aspect ratio; sample aspect ratio remains square.
2. Mixed-aspect pairs are supported: regression evidence explicitly covers 3:2, portrait, and 16:9 inputs, including at least one pair whose input aspect ratios differ.
3. Regression tests use deterministic local media and assert both ffprobe geometry and decoded pixel/padding properties that distinguish correct scale-to-fit from stretch; they fail against the current fixed 960x384 stretch behavior.
4. The repair preserves local-only export semantics, introduces no generation/API redesign or new mandatory dependency, and does not alter unrelated media behavior.
5. The focused media tests and full repository suite pass locally; exact commands, outputs, artifact paths, and SHA-256 hashes are recorded. No result is claimed until actually run.

## Testing Requirements
- Generate all test inputs locally with ffmpeg/project-owned assets. Include 3:2, portrait, and 16:9 cases plus mixed aspect pairs.
- Use ffprobe and a deterministic decoded-frame check to prove intrinsic geometry, padding, even dimensions, and absence of stretch. Literal expected dimensions for each fixture must be stated in the test or test output.
- Commands to run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_media.py -q`, then `PYTHONPATH=src .venv/bin/python -m pytest`.
- Check in only small deterministic local fixtures/evidence needed to reproduce the result; no credentials, public URLs, cloud artifacts, GPU work, or external API calls.
- `git diff --check` must pass.

## MANDATORY SKILLS
- `tool-systematic-debugging`: establish the measured red geometry regression before changing export behavior.

## OUT OF SCOPE
- Audio channel layout, loudness, or speech-preservation changes: those belong to the serialized dependent audio bug.
- Generation workflow/API redesign, progress UX, remote services, GPU work, publication, or push.

## Ownership / Dependencies
- This story owns `src/openjutsu/media.py` first. The dependent audio bug must not start until this story is delivered/accepted because both require edits to the same file.

## nd_contract
status: new

### evidence
- Created from the measured 2026-10-17 dogfood receipt during bounded Sr-PM intake.

### proof
- [ ] AC #1: Aspect-preserving scale-to-fit/pad output with even dimensions and no crop/stretch.
- [ ] AC #2: 3:2, portrait, 16:9, and mixed-aspect regressions are covered.
- [ ] AC #3: Deterministic geometry/pixel tests fail on the measured stretch defect and pass after repair.
- [ ] AC #4: Local export boundary and unrelated behavior are preserved.
- [ ] AC #5: Focused/full tests, diff check, paths, hashes, and exact outputs are recorded.


## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-10-17]: Independently reviewed delivery at commit 415e3d51bf5bfd52f60c73450101bea9b8cb00cc.

Evidence checked:
- Delivery preflight passed 9/9.
- Source diff is confined to aspect-preserving `make_side_by_side` filter/validation; audio mapping/encoding options remain unchanged.
- Current focused rerun: 7 passed in 1.66s; `pvg verify` passed 3 files with 0 issues; Python compile passed.
- Baseline replay using base 7ab3b8c with the delivered tests produced 6 failed / 1 passed, including the four recorded geometry RED cases (the committed RED artifact records the intermediate 4 failed / 1 passed snapshot before the strengthening tests were added).
- All five committed paired MP4s independently ffprobed as 1920x384 video, SAR 1:1, DAR 5:1, with AAC audio.
- Independent temporary regeneration matched `measurements.json` exactly and all five MP4s byte-for-byte; actual SHA-256 values matched `SHA256SUMS.json`.
- Committed full-suite evidence records 37 passed, 1 warning; the pre-existing Starlette warning is disclosed as a DISCOVERED_BUG.
- Required clean-worktree `git diff --check` passed; worktree remained clean during review.

## nd_contract
status: accepted

### evidence
- Delivery preflight 9/9; focused rerun 7 passed; independent baseline RED replay 6 failed / 1 passed; regenerated media/hashes/measurements all match committed evidence at 415e3d5.

### proof
- [x] AC #1: DAR-based scale-fit produces centered even 960x384 tiles, square output SAR, and measured black padding without crop/stretch.
- [x] AC #2: 3:2, portrait 9:16, 16:9, mixed-aspect, and non-square-SAR cases are covered.
- [x] AC #3: ffprobe geometry and decoded RGB checks detect baseline stretch and pass after repair.
- [x] AC #4: Only `make_side_by_side` behavior changed; audio options, local export boundary, dependencies, GPU/API/publication/push scope are preserved.
- [x] AC #5: Focused/full test artifacts, coverage, diff check, decoded measurements, hashes, paths, and exact commit SHA are recorded and independently corroborated.

## Implementation Evidence

Commands run:
- `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest tests/test_media.py -q`
- `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest`
- `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python docs/evidence/dogfood-repairs/OJ-xtk4/generate_evidence.py`
- `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python docs/evidence/dogfood-repairs/OJ-xtk4/measure_media_coverage.py`
- `pvg verify src/openjutsu/media.py tests/test_media.py docs/evidence/dogfood-repairs/OJ-xtk4/generate_evidence.py --include-tests --format=text`
- `git diff --check`

Summary: RED 4 failed, 1 passed; focused GREEN 7 passed; full suite 37 passed, 1 pre-existing warning; changed-function statement coverage 4/4 = 100.00%; pvg verify passed 3 files; git diff check passed.
Commit SHA: 415e3d51bf5bfd52f60c73450101bea9b8cb00cc on local-only branch `story/OJ-xtk4`.
Artifacts and SHA-256 hashes: `docs/evidence/dogfood-repairs/OJ-xtk4/REPORT.md`, `pytest-red.txt`, `pytest-focused.txt`, `pytest-full.txt`, `measurements.json`, `SHA256SUMS.json`, `hash-check.txt`.

## nd_contract
status: delivered

### evidence
- RED `4 failed, 1 passed`; focused `7 passed`; full `37 passed, 1 warning`; changed-function coverage `100.00%`; generator, pvg verify, and diff check passed.
- Local-only commit `415e3d51bf5bfd52f60c73450101bea9b8cb00cc` on `story/OJ-xtk4`; evidence and hashes under `docs/evidence/dogfood-repairs/OJ-xtk4/`.

### proof
- [x] AC #1: DAR-based scale-fit/pad produces centered even tiles, square SAR, and no crop/stretch.
- [x] AC #2: 3:2, portrait 9:16, 16:9, mixed-aspect, and non-square-SAR inputs are covered.
- [x] AC #3: Real ffprobe geometry and decoded RGB padding checks fail on baseline stretch and pass after repair.
- [x] AC #4: Local export semantics and audio options remain bounded; no new dependency, GPU, API, publication, or push.
- [x] AC #5: Focused/full tests, 100% changed-function statement coverage, diff check, artifacts, hashes, outputs, and commit SHA are recorded.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest tests/test_media.py -q`
  - `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest`
  - `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python docs/evidence/dogfood-repairs/OJ-xtk4/generate_evidence.py`
  - `PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python docs/evidence/dogfood-repairs/OJ-xtk4/measure_media_coverage.py`
  - `pvg verify src/openjutsu/media.py tests/test_media.py docs/evidence/dogfood-repairs/OJ-xtk4/generate_evidence.py --include-tests --format=text`
  - `git diff --check`
- RED before repair: `4 failed, 1 passed in 1.44s`; every new geometry case observed red at a tile edge that must be black padding. Artifact: `docs/evidence/dogfood-repairs/OJ-xtk4/pytest-red.txt`.
- GREEN focused: `7 passed in 1.75s`. Artifact: `docs/evidence/dogfood-repairs/OJ-xtk4/pytest-focused.txt`.
- Full suite: `37 passed, 1 warning in 12.59s`. Artifact: `docs/evidence/dogfood-repairs/OJ-xtk4/pytest-full.txt`.
- Changed-function executable statement coverage: `4/4 = 100.00%`. Artifact: `docs/evidence/dogfood-repairs/OJ-xtk4/coverage-media.txt`.
- Generator exit: `0`; output geometry/decoded pixels in `measurements.json`; SHA-256 values in `SHA256SUMS.json` and `hash-check.txt`.
- `pvg verify`: `VERIFY: PASSED (3 files scanned, 0 issues)`.
- `git diff --check`: exit `0`.

### Measured geometry
- Common tile: even `960x384`; each paired output: even `1920x384`, SAR `1:1`, DAR `5:1`.
- 3:2 `576x384`: decoded content width `576`, black padding `192+192` per tile.
- Portrait 9:16 `216x384`: content width `216`, padding `372+372`.
- 16:9 `640x360`: nearest even-pixel content width `682`, padding `138+140`.
- Mixed 3:2 + 9:16: independent widths `576` and `216`.
- Non-square input `288x384`, SAR `2:1`, DAR `3:2`: square-SAR content width `576`; output byte-identical to equivalent square-pixel 3:2 artifact.
- Output hashes include `3-2-paired.mp4` `39617c93e19d1f923d175cbb77124500cfb1690d0a807d25bf5d74f906a435f8`, `9-16-portrait-paired.mp4` `9bd21d88b0d5bb780a944fc79497ed53d16d7e9393941a48a5c81d56becefa7e`, `16-9-paired.mp4` `dfda5d3e0dd53fc99469aa94e8fce87db84a7894b1de89afdac63882431ec551`, and mixed/non-SAR values in `SHA256SUMS.json`.

### Commit
- Branch: `story/OJ-xtk4`
- SHA: `415e3d51bf5bfd52f60c73450101bea9b8cb00cc`
- Local commit only; no push performed.

### AC Verification
| AC # | Requirement | Code Location | Test/Evidence Location | Status |
|---|---|---|---|---|
| AC #1 | DAR-based scale-fit into centered even tiles, square SAR, no crop/stretch | `src/openjutsu/media.py:156-184` | `tests/test_media.py:106-167,179-200`; `measurements.json` | PASS |
| AC #2 | 3:2, portrait, 16:9, mixed-aspect, and non-square-SAR inputs | `src/openjutsu/media.py:169-184` | `tests/test_media.py:170-229`; `REPORT.md` | PASS |
| AC #3 | Real ffprobe geometry plus decoded RGB padding checks; red fails stretch baseline | repaired function | `pytest-red.txt`, `pytest-focused.txt`, `measurements.json` | PASS |
| AC #4 | Local-only semantics; no audio redesign, new dependency, GPU, API, publication, or push | `src/openjutsu/media.py:174-205` unchanged audio options after filter | `git show 415e3d5 --stat`; `REPORT.md` | PASS |
| AC #5 | Focused/full tests, coverage, diff check, artifacts/hashes, commit SHA | `docs/evidence/dogfood-repairs/OJ-xtk4/` | `pytest-*.txt`, `coverage-media.txt`, `hash-check.txt` | PASS |

LEARNINGS:
- Scale expressions should use input DAR, not storage width/height, before resetting SAR to `1:1`; this makes non-square-SAR and square-pixel equivalents produce identical square-pixel tiles.
- Sampling both black tile edges and expected color near fit boundaries distinguishes padding from full-width stretching without image-library dependencies.
- Even-pixel geometry necessarily rounds 16:9 at height 384 to `682x384`, visible as `138+140` padding rather than exact symmetric fractional width.

### DISCOVERED_BUG
  title: Full suite emits pre-existing StarletteDeprecationWarning
  context: Full pytest emits `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead` from `.venv/lib/python3.11/site-packages/fastapi/testclient.py:1`. It is unrelated to this media-only change and was not expanded under this story boundary.
  affected_files: tests/test_app.py; tests/test_app_e2e.py; .venv/lib/python3.11/site-packages/fastapi/testclient.py
  discovered_during: OJ-xtk4

## nd_contract
status: delivered

### evidence
- RED: `4 failed, 1 passed`; GREEN focused: `7 passed`; full: `37 passed, 1 warning`; generator and diff checks passed.
- Branch `story/OJ-xtk4`, commit `415e3d51bf5bfd52f60c73450101bea9b8cb00cc`; evidence and hashes under `docs/evidence/dogfood-repairs/OJ-xtk4/`.

### proof
- [x] AC #1: Each input is scaled from intrinsic DAR onto an even centered `960x384` tile with square SAR and no crop/stretch.
- [x] AC #2: 3:2, portrait 9:16, 16:9, mixed-aspect, and non-square-SAR cases are covered.
- [x] AC #3: Real ffprobe geometry and decoded RGB padding/color checks fail on the baseline stretch and pass after repair.
- [x] AC #4: Local export semantics remain bounded; audio options and unrelated media behavior are unchanged, with no new dependency, GPU, API, publication, or push.
- [x] AC #5: Focused/full tests, 100% changed-function statement coverage, diff check, artifacts, SHA-256 hashes, exact outputs, and local commit SHA are recorded.

## History
- 2026-10-18T03:50:46Z dep_added: blocks OJ-inuo
- 2026-10-18T03:51:25Z status: open -> in_progress
- 2026-10-18T03:51:25Z claimed by dev-OJ-xtk4
- 2026-10-18T03:53:02Z dep_added: blocks OJ-yf2c
- 2026-10-18T04:09:05Z status: in_progress -> in_progress
- 2026-10-18T04:09:05Z auto-follows: linked to predecessor OJ-4rht
- 2026-10-18T04:14:18Z status: in_progress -> closed
- 2026-10-18T04:14:18Z dep_removed: no_longer_blocks OJ-inuo
- 2026-10-18T04:14:18Z dep_removed: no_longer_blocks OJ-yf2c

## Links
- Parent: [[OJ-a7l6]]
- Follows: [[OJ-4rht]]

## Comments
