# OJ-xtk4 paired-review aspect-ratio repair evidence

## Scope

- Repair: `src/openjutsu/media.py:156-184` validates an even common tile, scales each input from its input DAR into square-SAR even dimensions, centers/pads both onto the common tile, and stacks them without changing the audio path.
- Regression tests: `tests/test_media.py:42-239` generate local solid red/green inputs and inspect ffprobe geometry plus decoded RGB pixels.
- Audio mapping/encoding, generation APIs, GPU work, publication, and push were not changed.

## Red/green proof

Red command against the original fixed `960x384` stretch implementation:

```text
PYTHONPATH=src <checkout>/.venv/bin/python -m pytest tests/test_media.py -q
```

Result in `pytest-red.txt`:

```text
4 failed, 1 passed in 1.44s
```

Each new aspect case failed at the expected black tile edge and observed red there instead, proving that the test detects stretch. Green result in `pytest-focused.txt`:

```text
7 passed in 1.75s
```

## Measured geometry and decoded pixels

All paired outputs are `1920x384`, SAR `1:1`, DAR `5:1`, composed from two even `960x384` tiles. Full values are in `measurements.json`.

| Case | Inputs (WxH, SAR, DAR) | Expected/decoded content widths | Source padding | Final padding |
|---|---|---:|---:|---:|
| 3:2 | `576x384`, `1:1`, `3:2` / same | `576`, `576` | `192+192` | `192+192` |
| Portrait 9:16 | `216x384`, `1:1`, `9:16` / same | `216`, `216` | `372+372` | `372+372` |
| 16:9 | `640x360`, `1:1`, `16:9` / same | `682`, `682` | `138+140` | `138+140` |
| Mixed | `576x384`, `3:2` / `216x384`, `9:16` | `576`, `216` | `192+192` | `372+372` |
| Non-square SAR | `288x384`, SAR `2:1`, DAR `3:2` / `576x384`, SAR `1:1`, DAR `3:2` | `576`, `576` | `192+192` | `192+192` |

The 16:9 content is `682x384`, the nearest even-pixel representation at this tile height; its asymmetric `138+140` padding is the one-pixel consequence. Odd requested tiles fail before ffmpeg with `ValueError: width and height must be even integers of at least 2 pixels`.

The non-square-SAR output is byte-identical to the equivalent square-pixel 3:2 case (`cmp` status 0), directly demonstrating DAR-based sizing rather than storage-ratio scaling.

## Artifact hashes

Generated and independently checked in `SHA256SUMS.json` and `hash-check.txt`:

```text
dfda5d3e0dd53fc99469aa94e8fce87db84a7894b1de89afdac63882431ec551  16-9-paired.mp4
39617c93e19d1f923d175cbb77124500cfb1690d0a807d25bf5d74f906a435f8  3-2-paired.mp4
9bd21d88b0d5bb780a944fc79497ed53d16d7e9393941a48a5c81d56becefa7e  9-16-portrait-paired.mp4
31b330381fa13e21425d91798f199626d927cf485943c070b41e610c2f72b923  mixed-3-2-9-16-paired.mp4
39617c93e19d1f923d175cbb77124500cfb1690d0a807d25bf5d74f906a435f8  non-square-sar-3-2-dar-paired.mp4
```

## Exact verification commands

```text
PYTHONPATH=src <checkout>/.venv/bin/python -m pytest tests/test_media.py -q
PYTHONPATH=src <checkout>/.venv/bin/python -m pytest
PYTHONPATH=src <checkout>/.venv/bin/python docs/evidence/dogfood-repairs/OJ-xtk4/generate_evidence.py
PYTHONPATH=src <checkout>/.venv/bin/python docs/evidence/dogfood-repairs/OJ-xtk4/measure_media_coverage.py
pvg verify src/openjutsu/media.py tests/test_media.py docs/evidence/dogfood-repairs/OJ-xtk4/generate_evidence.py --include-tests --format=text
git diff --check
```

Results:

- Focused: `7 passed in 1.75s` (`pytest-focused.txt`).
- Full: `37 passed, 1 warning in 12.59s` (`pytest-full.txt`).
- Changed-function executable statement coverage: `4/4 = 100.00%` (`coverage-media.txt`, measured by the checked-in stdlib AST/`sys.settrace` harness; no coverage dependency added).
- Generator: exit `0`; measurements and hashes above.
- `pvg verify`: `VERIFY: PASSED (3 files scanned, 0 issues)`.
- `git diff --check`: exit `0`.

## Caveat

The full suite emits the repository's pre-existing `StarletteDeprecationWarning` from `fastapi/testclient.py` (`httpx` with `starlette.testclient` is deprecated; install `httpx2`). It is unrelated to this media-only change and was not cleaned up under the story boundary. Verification used local FFmpeg/ffprobe 8.0.1.
