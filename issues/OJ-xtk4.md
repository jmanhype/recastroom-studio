---
id: OJ-xtk4
title: "Preserve paired-review aspect ratio"
status: in_progress
priority: 1
type: bug
labels: [bug, media, local, dogfood]
parent: OJ-a7l6
created_at: 2026-10-18T03:50:45Z
created_by: speed
updated_at: 2026-10-18T03:53:01Z
content_hash: "sha256:898707d8f7dc874d486e454c476e3026f005eb480fb8db42306cd19ac09604bf"
blocks: [OJ-inuo]
assignee: dev-OJ-xtk4
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
- The repository's existing local `ffmpeg` dependency and locally generated or project-owned fixtures only.
- The read-only dogfood evidence cited above; do not mutate or re-run generation.

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
- The repository's existing local `ffmpeg` dependency and locally generated or project-owned fixtures only.
- The read-only dogfood evidence cited above; do not mutate or re-run generation.

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
