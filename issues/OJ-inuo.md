---
id: OJ-inuo
title: "Preserve restored source audio layout and loudness"
status: in_progress
priority: 1
type: bug
labels: [bug, media, local, dogfood]
parent: OJ-a7l6
created_at: 2026-10-18T03:50:46Z
created_by: speed
updated_at: 2026-10-18T04:25:22Z
content_hash: "sha256:ca406b3b58411609653d1845739fe86310fb5c121b78bae384c773498b9e1939"
blocks: [OJ-yf2c]
was_blocked_by: [OJ-xtk4]
assignee: dev-OJ-inuo
follows: [OJ-xtk4]
---

## Description

## Description
## Description
### Measured defect
Audio restoration forces every source layout to 5.1. The real dogfood source was stereo, but both restored final and paired review were 5.1; decoded mono PCM showed final gain 0.4141805368 versus source and an RMS difference of 1491.237 S16 samples. Correlation 0.9999677 proves similar speech content, not preserved layout or loudness.

## Embedded Context
- Parent epic: OJ-a7l6.
- Baseline repository commit at intake: `7ab3b8c`; no repair tests have been run or claimed yet.
- Current code references: `src/openjutsu/media.py:105-153` restores source audio and hardcodes `aformat=channel_layouts=5.1` at line 128; `make_side_by_side` repeats that forced layout at `src/openjutsu/media.py:181`.
- Dogfood evidence: `../frontend-evidence/dogfood-20261017/live/REPORT.md`, `browser-playback.json`, and `output-verification.json`.
- Measured source: stereo, 48 kHz, 2 channels. Measured final/comparison: 5.1, 6 channels. Source and final decoded sample count were both 282,624, final peak was 7,530, correlation was 0.9999677326692922, and final/source mono gain was 0.41418053682187445.
- Owner constraints: local deterministic work only; no GPU, paid API, cloud inference, publication, or push.

## Boundary Map
PRODUCES:
- `src/openjutsu/media.py` -> source-layout-preserving audio restoration in `restore_source_audio` and paired-review audio handling in `make_side_by_side`
- `tests/test_media.py` (or one focused existing/new media test module) -> mono, stereo, and 5.1 speech/layout/loudness regressions
- `docs/evidence/dogfood-repairs/OJ-inuo/` -> exact commands, ffprobe layouts, decoded PCM metrics, output hashes, and limitations

CONSUMES:
- OJ-xtk4: `src/openjutsu/media.py` -> accepted aspect-preserving `make_side_by_side` baseline
  source: src/openjutsu/media.py
  spec: authorized local speech/ffmpeg fixtures are embedded above and must remain private/local

## Story Acceptance Criteria
1. For mono, stereo, and 5.1 source fixtures, restored final and paired-review outputs preserve the source audio channel count and channel layout; no path forces `5.1`, downmixes stereo, or invents channels.
2. The original speech waveform remains present: regression tests decode source and exported outputs to PCM and compare sample alignment/count, nonzero peak, per-channel RMS/loudness, and a correlation/waveform metric using explicit predeclared tolerances.
3. Loudness preservation is measured, not inferred: active speech-channel RMS levels remain within the predeclared test tolerance (at most 1.0 dB), and no active source speech channel becomes silent or materially attenuated as in the measured 0.414 mono gain.
4. Regression tests cover mono, stereo, and 5.1 separately and fail against the current forced-5.1 behavior while passing after repair; all audio artifacts remain local.
5. The repair preserves local export semantics, introduces no generation/API redesign or new mandatory dependency, and does not change unrelated media behavior.
6. The focused media tests and full repository suite pass locally; exact commands, outputs, artifact paths, PCM metrics, and SHA-256 hashes are recorded. No result is claimed until actually run.

## Testing Requirements
- Use an authorized original-speech sample owned by this project. Derive compact mono, stereo, and 5.1 test inputs locally with ffmpeg; document the exact channel mapping and ensure every asserted channel contains the intended speech signal rather than silence.
- For each layout, probe channels/layout and decode exported audio to a common PCM analysis format without collapsing layouts before measurement. Record sample count, peak, per-channel RMS, correlation or equivalent waveform metric, and loudness delta.
- State fixed numerical tolerances in the tests. Correlation alone is not sufficient proof of loudness.
- Commands to run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_media.py -q`, then `PYTHONPATH=src .venv/bin/python -m pytest`.
- Check in only compact deterministic local fixtures/evidence; no credentials, public URLs, cloud artifacts, GPU work, or external API calls.
- `git diff --check` must pass.

## MANDATORY SKILLS
- `tool-systematic-debugging`: establish measured forced-5.1/loudness red regressions before changing audio behavior.

## OUT OF SCOPE
- Generation workflow/API redesign, speech-to-video synchronization changes, loudness normalization that changes the source, progress UX, remote services, GPU work, publication, or push.
- Video aspect-ratio algorithm work; consume the accepted aspect-ratio story.

## Ownership / Dependencies
- Blocked by the paired-review aspect-ratio bug because both stories edit `src/openjutsu/media.py`. Do not claim this story until that blocker is delivered/accepted.

## nd_contract
status: new

### evidence
- Created from the measured 2026-10-17 dogfood receipt during bounded Sr-PM intake.

### proof
- [ ] AC #1: Mono/stereo/5.1 source layouts are preserved without forced 5.1.
- [ ] AC #2: Original speech is proven by decoded PCM sample, peak, RMS, and waveform measurements.
- [ ] AC #3: Loudness remains within an explicit test tolerance and no active speech channel is silent.
- [ ] AC #4: Focused regressions fail on forced 5.1 and pass after repair.
- [ ] AC #5: Local export boundary and unrelated behavior are preserved.
- [ ] AC #6: Focused/full tests, diff check, metrics, hashes, and exact outputs are recorded.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T03:50:46Z dep_added: blocked_by OJ-xtk4

## Links
- Parent: [[OJ-a7l6]]
- Blocked by: [[OJ-xtk4]]

## Comments


## Description
### Measured defect
Audio restoration forces every source layout to 5.1. The real dogfood source was stereo, but both restored final and paired review were 5.1; decoded mono PCM showed final gain 0.4141805368 versus source and an RMS difference of 1491.237 S16 samples. Correlation 0.9999677 proves similar speech content, not preserved layout or loudness.

## Embedded Context
- Parent epic: OJ-a7l6.
- Baseline repository commit at intake: `7ab3b8c`; no repair tests have been run or claimed yet.
- Current code references: `src/openjutsu/media.py:105-153` restores source audio and hardcodes `aformat=channel_layouts=5.1` at line 128; `make_side_by_side` repeats that forced layout at `src/openjutsu/media.py:181`.
- Dogfood evidence: `../frontend-evidence/dogfood-20261017/live/REPORT.md`, `browser-playback.json`, and `output-verification.json`.
- Measured source: stereo, 48 kHz, 2 channels. Measured final/comparison: 5.1, 6 channels. Source and final decoded sample count were both 282,624, final peak was 7,530, correlation was 0.9999677326692922, and final/source mono gain was 0.41418053682187445.
- Owner constraints: local deterministic work only; no GPU, paid API, cloud inference, publication, or push.

## Boundary Map
PRODUCES:
- `src/openjutsu/media.py` -> source-layout-preserving audio restoration in `restore_source_audio` and paired-review audio handling in `make_side_by_side`
- `tests/test_media.py` (or one focused existing/new media test module) -> mono, stereo, and 5.1 speech/layout/loudness regressions
- `docs/evidence/dogfood-repairs/PENDING-ID/` -> exact commands, ffprobe layouts, decoded PCM metrics, output hashes, and limitations

CONSUMES:
- OJ-xtk4: `src/openjutsu/media.py` -> accepted aspect-preserving `make_side_by_side` baseline
  source: src/openjutsu/media.py
  spec: authorized local speech/ffmpeg fixtures are embedded above and must remain private/local

## Story Acceptance Criteria
1. For mono, stereo, and 5.1 source fixtures, restored final and paired-review outputs preserve the source audio channel count and channel layout; no path forces `5.1`, downmixes stereo, or invents channels.
2. The original speech waveform remains present: regression tests decode source and exported outputs to PCM and compare sample alignment/count, nonzero peak, per-channel RMS/loudness, and a correlation/waveform metric using explicit predeclared tolerances.
3. Loudness preservation is measured, not inferred: active speech-channel RMS levels remain within the predeclared test tolerance (at most 1.0 dB), and no active source speech channel becomes silent or materially attenuated as in the measured 0.414 mono gain.
4. Regression tests cover mono, stereo, and 5.1 separately and fail against the current forced-5.1 behavior while passing after repair; all audio artifacts remain local.
5. The repair preserves local export semantics, introduces no generation/API redesign or new mandatory dependency, and does not change unrelated media behavior.
6. The focused media tests and full repository suite pass locally; exact commands, outputs, artifact paths, PCM metrics, and SHA-256 hashes are recorded. No result is claimed until actually run.

## Testing Requirements
- Use an authorized original-speech sample owned by this project. Derive compact mono, stereo, and 5.1 test inputs locally with ffmpeg; document the exact channel mapping and ensure every asserted channel contains the intended speech signal rather than silence.
- For each layout, probe channels/layout and decode exported audio to a common PCM analysis format without collapsing layouts before measurement. Record sample count, peak, per-channel RMS, correlation or equivalent waveform metric, and loudness delta.
- State fixed numerical tolerances in the tests. Correlation alone is not sufficient proof of loudness.
- Commands to run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_media.py -q`, then `PYTHONPATH=src .venv/bin/python -m pytest`.
- Check in only compact deterministic local fixtures/evidence; no credentials, public URLs, cloud artifacts, GPU work, or external API calls.
- `git diff --check` must pass.

## MANDATORY SKILLS
- `tool-systematic-debugging`: establish measured forced-5.1/loudness red regressions before changing audio behavior.

## OUT OF SCOPE
- Generation workflow/API redesign, speech-to-video synchronization changes, loudness normalization that changes the source, progress UX, remote services, GPU work, publication, or push.
- Video aspect-ratio algorithm work; consume the accepted aspect-ratio story.

## Ownership / Dependencies
- Blocked by the paired-review aspect-ratio bug because both stories edit `src/openjutsu/media.py`. Do not claim this story until that blocker is delivered/accepted.

## nd_contract
status: new

### evidence
- Created from the measured 2026-10-17 dogfood receipt during bounded Sr-PM intake.

### proof
- [ ] AC #1: Mono/stereo/5.1 source layouts are preserved without forced 5.1.
- [ ] AC #2: Original speech is proven by decoded PCM sample, peak, RMS, and waveform measurements.
- [ ] AC #3: Loudness remains within an explicit test tolerance and no active speech channel is silent.
- [ ] AC #4: Focused regressions fail on forced 5.1 and pass after repair.
- [ ] AC #5: Local export boundary and unrelated behavior are preserved.
- [ ] AC #6: Focused/full tests, diff check, metrics, hashes, and exact outputs are recorded.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T03:50:46Z dep_added: blocked_by OJ-xtk4
- 2026-10-18T03:53:02Z dep_added: blocks OJ-yf2c
- 2026-10-18T04:14:18Z dep_removed: was_blocked_by OJ-xtk4
- 2026-10-18T04:15:55Z status: open -> in_progress
- 2026-10-18T04:15:55Z auto-follows: linked to predecessor OJ-xtk4
- 2026-10-18T04:15:55Z claimed by dev-OJ-inuo

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]
- Was blocked by: [[OJ-xtk4]]
- Follows: [[OJ-xtk4]]

## Comments

### 2026-10-18T04:25:22Z speed
Coordinator takeover: GLM worker was interrupted after producing no diff or status; no edits were reverted. CoS hello compatible=null; configured native Qwen role is a different provider, not the authorized Ambassador route. Root is performing the bounded repair in dev-OJ-inuo; independent PM acceptance still required. No new GPU/API generation.
