---
id: OJ-inuo
title: "Preserve restored source audio layout and loudness"
status: in_progress
priority: 1
type: bug
labels: [bug, media, local, dogfood, delivered]
parent: OJ-a7l6
created_at: 2026-10-18T03:50:46Z
created_by: speed
updated_at: 2026-10-18T04:29:00Z
content_hash: "sha256:e7b4823f0d176818add8f1d417f6bb756d61cab198b61bb4e4a4b421e427bc93"
blocks: [OJ-yf2c]
was_blocked_by: [OJ-xtk4]
assignee: dev-OJ-inuo
follows: [OJ-xtk4, OJ-4rht]
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

## Implementation Evidence

Summary: Remove forced 5.1 expansion while preserving source speech layout and loudness.
Commit SHA: 5304b7a04089fce0224670ab38d5acb2e1abbe23; implementation 01c234a1fec42dcd64387d10215b997bcd0c993a.

### CI/Test Results
Commands run:
- PYTHONPATH=src root-venv/bin/python -m pytest tests/test_media_audio.py -q
- PYTHONPATH=src root-venv/bin/python -m pytest -q
- pvg verify src/openjutsu/media.py tests/test_media_audio.py --include-tests
- git diff --check cda27bc..HEAD

Results: RED2failed1passed4.23s; GREEN3passed3.08s; full41passed1existingwarning23.34s.
PROOF: docs/evidence/dogfood-repairs/OJ-inuo/REPORT.md, transcripts, artifact metrics/probes/hashes.
LEARNINGS: test layout and per-channel loudness, not only waveform correlation.
OBSERVATIONS: preexisting warning/static findings and initial fixture failure disclosed in REPORT.md.

### AC Verification
| AC # | Evidence | Status |
|---|---|---|
| AC #1 | Mono/stereo/5.1 source and output probes; no forced expansion | PASS |
| AC #2 | Per-channel sample count, peaks, RMS and zero-lag correlation in metrics.json | PASS |
| AC #3 | All channels within <=1dB predeclared RMS limit | PASS |
| AC #4 | Definitive RED2failed1passed; GREEN3passed unchanged tests | PASS |
| AC #5 | Four-line audio-only deletion, accepted geometry retained | PASS |
| AC #6 | Focused/full suites, diff scan, artifacts, probes, SHA256SUMS | PASS |

## nd_contract
status: delivered

### evidence
- Summary/implementation: four-line deletion removes forced 5.1 conversion in both audio export paths; source commit 01c234a1fec42dcd64387d10215b997bcd0c993a; final commit SHA 5304b7a04089fce0224670ab38d5acb2e1abbe23.
- Commands run: PYTHONPATH=src root-venv/bin/python -m pytest tests/test_media_audio.py -q (RED 2 failed,1 passed in4.23s; GREEN3 passed in3.08s); same command full suite41 passed,1 preexisting warning in23.34s.
- CI/test results: local only; no remote CI claimed. git diff --check passed; pvg verify src/openjutsu/media.py tests/test_media_audio.py --include-tests passed2files0issues.
- PROOF: docs/evidence/dogfood-repairs/OJ-inuo/REPORT.md, full/red/green logs, source-probes.json, artifact metrics and SHA256SUMS.json. Coverage: 2/2 changed functions exercised; statement coverage not measured.
- Existing real render re-export: stereo/48k preserved, 282624samples/channel, RMS delta -0.00065545dB, correlation0.99999903; final SHA f69e776234249ee45dfbea199aba49adbd8d9c7c5a261ae7fd0d63329a9130c9, comparison062b8f59140981e0eefcf4be69958fc77fcdd5249fc65e0fe7594d4e107fb2a5. Original hashes unchanged. No GPU generation or publication.
- LEARNINGS: correlation alone misses attenuation; compare layout and per-channel RMS; band-limit LFE fixtures. OBSERVATIONS: existing Starlette warning and 3 unrelated preexisting unscoped static-scan findings retained; initial fixture error and prior root ENOSPC failure explicitly recorded.

### proof
- [x] AC #1: Mono/stereo/5.1 channel counts and layouts preserved in final and paired outputs.
- [x] AC #2: Real speech decoded; sample counts, peaks, per-channel RMS and zero-lag correlation measured.
- [x] AC #3: Every active channel satisfies predeclared <=1dB loudness bound and remains nonzero.
- [x] AC #4: Forced5.1 RED mono/stereo failures and unchanged5.1 baseline pass; all3 GREEN.
- [x] AC #5: Accepted video geometry unchanged; local only, no new dependency/API/generation work.
- [x] AC #6: Focused/full suites and diff checks pass; files/probes/metrics/hashes recorded on disk.


## Implementation Evidence

Summary: Remove forced 5.1 expansion while preserving source speech layout and loudness.
Commit SHA: 5304b7a04089fce0224670ab38d5acb2e1abbe23; implementation 01c234a1fec42dcd64387d10215b997bcd0c993a.

### CI/Test Results
Commands run:
- PYTHONPATH=src root-venv/bin/python -m pytest tests/test_media_audio.py -q
- PYTHONPATH=src root-venv/bin/python -m pytest -q
- pvg verify src/openjutsu/media.py tests/test_media_audio.py --include-tests
- git diff --check cda27bc..HEAD

Results: RED2failed1passed4.23s; GREEN3passed3.08s; full41passed1existingwarning23.34s.
PROOF: docs/evidence/dogfood-repairs/OJ-inuo/REPORT.md, transcripts, artifact metrics/probes/hashes.
LEARNINGS: test layout and per-channel loudness, not only waveform correlation.
OBSERVATIONS: preexisting warning/static findings and initial fixture failure disclosed in REPORT.md.

## nd_contract
status: delivered

### evidence
- Summary/implementation: four-line deletion removes forced 5.1 conversion in both audio export paths; source commit 01c234a1fec42dcd64387d10215b997bcd0c993a; final commit SHA 5304b7a04089fce0224670ab38d5acb2e1abbe23.
- Commands run: PYTHONPATH=src root-venv/bin/python -m pytest tests/test_media_audio.py -q (RED 2 failed,1 passed in4.23s; GREEN3 passed in3.08s); same command full suite41 passed,1 preexisting warning in23.34s.
- CI/test results: local only; no remote CI claimed. git diff --check passed; pvg verify src/openjutsu/media.py tests/test_media_audio.py --include-tests passed2files0issues.
- PROOF: docs/evidence/dogfood-repairs/OJ-inuo/REPORT.md, full/red/green logs, source-probes.json, artifact metrics and SHA256SUMS.json. Coverage: 2/2 changed functions exercised; statement coverage not measured.
- Existing real render re-export: stereo/48k preserved, 282624samples/channel, RMS delta -0.00065545dB, correlation0.99999903; final SHA f69e776234249ee45dfbea199aba49adbd8d9c7c5a261ae7fd0d63329a9130c9, comparison062b8f59140981e0eefcf4be69958fc77fcdd5249fc65e0fe7594d4e107fb2a5. Original hashes unchanged. No GPU generation or publication.
- LEARNINGS: correlation alone misses attenuation; compare layout and per-channel RMS; band-limit LFE fixtures. OBSERVATIONS: existing Starlette warning and 3 unrelated preexisting unscoped static-scan findings retained; initial fixture error and prior root ENOSPC failure explicitly recorded.

### proof
- [x] AC #1: Mono/stereo/5.1 channel counts and layouts preserved in final and paired outputs.
- [x] AC #2: Real speech decoded; sample counts, peaks, per-channel RMS and zero-lag correlation measured.
- [x] AC #3: Every active channel satisfies predeclared <=1dB loudness bound and remains nonzero.
- [x] AC #4: Forced5.1 RED mono/stereo failures and unchanged5.1 baseline pass; all3 GREEN.
- [x] AC #5: Accepted video geometry unchanged; local only, no new dependency/API/generation work.
- [x] AC #6: Focused/full suites and diff checks pass; files/probes/metrics/hashes recorded on disk.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Summary/implementation: four-line deletion removes forced 5.1 conversion in both audio export paths; source commit 01c234a1fec42dcd64387d10215b997bcd0c993a; final commit SHA 9dd6efc64b5ddf3912513fd27cca4e772801070c.
- Commands run: PYTHONPATH=src root-venv/bin/python -m pytest tests/test_media_audio.py -q (RED 2 failed,1 passed in4.23s; GREEN3 passed in3.08s); same command full suite41 passed,1 preexisting warning in23.34s.
- CI/test results: local only; no remote CI claimed. git diff --check passed; pvg verify src/openjutsu/media.py tests/test_media_audio.py --include-tests passed2files0issues.
- PROOF: docs/evidence/dogfood-repairs/OJ-inuo/REPORT.md, full/red/green logs, source-probes.json, artifact metrics and SHA256SUMS.json. Coverage: 2/2 changed functions exercised; statement coverage not measured.
- Existing real render re-export: stereo/48k preserved, 282624samples/channel, RMS delta -0.00065545dB, correlation0.99999903; final SHA f69e776234249ee45dfbea199aba49adbd8d9c7c5a261ae7fd0d63329a9130c9, comparison062b8f59140981e0eefcf4be69958fc77fcdd5249fc65e0fe7594d4e107fb2a5. Original hashes unchanged. No GPU generation or publication.
- LEARNINGS: correlation alone misses attenuation; compare layout and per-channel RMS; band-limit LFE fixtures. OBSERVATIONS: existing Starlette warning and 3 unrelated preexisting unscoped static-scan findings retained; initial fixture error and prior root ENOSPC failure explicitly recorded.

### proof
- [x] AC #1: Mono/stereo/5.1 channel counts and layouts preserved in final and paired outputs.
- [x] AC #2: Real speech decoded; sample counts, peaks, per-channel RMS and zero-lag correlation measured.
- [x] AC #3: Every active channel satisfies predeclared <=1dB loudness bound and remains nonzero.
- [x] AC #4: Forced5.1 RED mono/stereo failures and unchanged5.1 baseline pass; all3 GREEN.
- [x] AC #5: Accepted video geometry unchanged; local only, no new dependency/API/generation work.
- [x] AC #6: Focused/full suites and diff checks pass; files/probes/metrics/hashes recorded on disk.


## History
- 2026-10-18T03:50:46Z dep_added: blocked_by OJ-xtk4
- 2026-10-18T03:53:02Z dep_added: blocks OJ-yf2c
- 2026-10-18T04:14:18Z dep_removed: was_blocked_by OJ-xtk4
- 2026-10-18T04:15:55Z status: open -> in_progress
- 2026-10-18T04:15:55Z auto-follows: linked to predecessor OJ-xtk4
- 2026-10-18T04:15:55Z claimed by dev-OJ-inuo
- 2026-10-18T04:28:03Z status: in_progress -> in_progress
- 2026-10-18T04:28:03Z auto-follows: linked to predecessor OJ-4rht
- 2026-10-18T04:28:41Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]
- Was blocked by: [[OJ-xtk4]]
- Follows: [[OJ-xtk4]], [[OJ-4rht]]

## Comments

### 2026-10-18T04:25:22Z speed
Coordinator takeover: GLM worker was interrupted after producing no diff or status; no edits were reverted. CoS hello compatible=null; configured native Qwen role is a different provider, not the authorized Ambassador route. Root is performing the bounded repair in dev-OJ-inuo; independent PM acceptance still required. No new GPU/API generation.
