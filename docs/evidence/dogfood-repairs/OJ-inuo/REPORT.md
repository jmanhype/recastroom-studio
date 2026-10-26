# OJ-inuo — source audio preservation

Source commit: `01c234a1fec42dcd64387d10215b997bcd0c993a`.
Base: `cda27bc` (accepted portrait and aspect fixes included).

## Change

Removed the two `-af aformat=channel_layouts=5.1` arguments from
`restore_source_audio` and `make_side_by_side`. FFmpeg now keeps the mapped
source audio's mono/stereo/5.1 layout. No normalization, new dependency,
video-filter change, remote request, GPU work, or generation was added.

## PROOF: tests and commands

Commands run from the story checkout with the root repository virtualenv:

```sh
PYTHONPATH=src "$ROOT_VENV/bin/python" -m pytest tests/test_media_audio.py -q
PYTHONPATH=src "$ROOT_VENV/bin/python" -m pytest tests/test_media_audio.py -q --basetemp=docs/evidence/dogfood-repairs/OJ-inuo/artifacts
PYTHONPATH=src "$ROOT_VENV/bin/python" -m pytest -q
git diff --check HEAD^..HEAD
pvg verify src/openjutsu/media.py tests/test_media_audio.py --include-tests
```

- RED on unmodified production code: **2 failed, 1 passed in 4.23s**.
  Mono and stereo incorrectly became six channels. Existing 5.1 already passed.
- GREEN: **3 passed in 3.08s** using identical final tests.
- Full suite: **41 passed, 1 warning in 23.34s**.
- Changed-file static scan and diff check passed.
- Both changed functions are exercised in every layout case (2/2 function
  coverage); statement/branch coverage percentage was not measured.
- `red.txt`, `green.txt`, `full.txt` are complete transcripts with private
  path prefixes redacted. Raw originals are retained in private dogfood evidence.
- An initial 5.1 test-fixture experiment failed in FFmpeg's join/AAC encoder;
  `initial-fixture-error.txt` preserves it. The fixture was corrected to explicit
  pan plus LFE-only lowpass before the definitive RED and before production edits.

## Fixture provenance and fixed tolerances

`tests/fixtures/export_speech.wav` is the first two seconds of the authorized
project-generated kitchen source, converted locally to mono PCM16/48 kHz:

```sh
ffmpeg -y -v error -i "$AUTHORIZED_SOURCE" -map 0:a:0 -t 2 -ac 1 -ar 48000 -c:a pcm_s16le -map_metadata -1 tests/fixtures/export_speech.wav
```

Source MP4 SHA-256:
`63d824b104058844e32170a1b7867d2e638b42d93ccf7454c97e20334960084b`.
Speech WAV SHA-256:
`407e544c5382a957f4fe475f80a0dc3817b845d48d8ed25ad1da20ad955f190f`.

Each fixture uses a two-second 160x96/24fps color video and AAC/320k audio.
Mono is unchanged; stereo maps left=mono, right=0.75*mono; 5.1 maps speech
to FL/FR/FC/LFE/BL/BR and low-passes **only LFE at 120 Hz**. Every channel
is active. Source probes and generated local artifacts are committed.

Predeclared requirements: exact channel count/layout and decoded sample count,
per-channel peak >0.0001, absolute RMS change <=1 dB, zero-lag normalized
correlation >=0.98. Measurements use float PCM at 48kHz without downmixing.
Each fixture output has 96,256 decoded samples/channel (AAC padding included).
Per-channel peaks, RMS, gains, correlations, and file hashes are in
`artifacts/*/metrics.json`; `SHA256SUMS.json` covers compact proof artifacts.
The largest observed 5.1 RMS change is approximately -0.0463 dB; its lowest
correlation is 0.9979, within the unchanged thresholds.

## Acceptance mapping

| AC | Proof |
|---|---|
| #1 | Mono/1, stereo/2, 5.1/6 survive both real export functions unchanged. |
| #2 | Exact samples/channel, nonzero peaks, per-channel RMS and zero-lag correlation measured from real speech. |
| #3 | All active channels satisfy the predeclared <=1 dB bound; no silent replacement channel. |
| #4 | Definitive RED has two channel-expansion failures; all three layouts GREEN after the four-line deletion. |
| #5 | Diff changes only forced audio conversion plus focused test/fixture/evidence; accepted video geometry untouched. |
| #6 | Focused/full pytest logs, ffprobe data, generated files, metric JSONs and hashes exist on disk. |

## Existing real dogfood re-export

The coordinator also re-exported job `61721c5f2c27` locally from the unchanged
generated MP4 and original stereo source, retaining all original artifacts.
Final: 768x512; comparison: 1536x512 with two aspect-correct 768x512 tiles.
Both retain 141 frames/24fps and 282,624 audio samples/channel, stereo/48kHz.
Both channels: gain about 0.99992357; RMS change about -0.00065545 dB;
zero-lag correlation about 0.99999903.

New final SHA-256:
`f69e776234249ee45dfbea199aba49adbd8d9c7c5a261ae7fd0d63329a9130c9`.
New comparison SHA-256:
`062b8f59140981e0eefcf4be69958fc77fcdd5249fc65e0fe7594d4e107fb2a5`.
Private raw export receipt: dogfood-repairs-20261017/repaired/verification.json.
This proves export/audio preservation, **not identity quality or phoneme sync**.

## LEARNINGS

High speech correlation did not prove preserved loudness: forced stereo-to-5.1
conversion attenuated mono playback. Test layouts and per-channel RMS explicitly.
Use a valid band-limited LFE fixture, not full-band speech falsely treated as LFE.

## OBSERVATIONS / limitations

- Existing FastAPI/Starlette TestClient httpx deprecation warning remains.
- An unscoped `pvg verify` reports three pre-existing findings: thin CLI wrapper,
  thin package initializer, and the empty `WorkflowError` exception class.
  The scoped changed-file scan passes; no claim of a clean global scan is made.
- Root's earlier frontend/aspect integration run hit ENOSPC. After safe UV cache
  cleanup, its rerun passed 38 tests; this full audio run passed 41 tests.
- `bd sync --from-main` cannot run because this repository has no Beads database;
  existing shared nd/Paivot remains the tracker. No competing database created.
- No public publication/push and no additional media-generation spend.
