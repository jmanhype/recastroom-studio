# OJ-yf2c final browser capstone evidence

Date: 2026-10-18

## Result

This pass closes the two browser-evidence gaps left by the earlier checkpoint:

1. Actual reduced-motion suppression is now proven on the completed `#result`
   surface, not inferred from body-level CSS.
2. Keyboard focus is proven for the brand link, every DOM control, all three
   native video containers, all six exposed subcontrols in each native video
   player, all download/recovery links, and the conditional legacy
   renderer-recovery control.

The deterministic browser jobs used only local synthetic fixtures and the real
loopback backend. No cloud inference, GPU, credential, publication, push, or
public tunnel was used.

## Real dry-run proof

- Dry-run server: `127.0.0.1:8894`, backend `dry_run`.
- Health before teardown: HTTP 200, `workflow_exists=true`,
  `renderer_ready=true`, renderer code `local_dry_run`.
- Real browser job `8f999d26dab4`: prepare, run, status polling, final review,
  and side-by-side review all reached `complete`.
- Independent real browser replay job `0a8128290f64` also reached `complete`.
- Both jobs used:
  - `synthetic_source.mp4`
  - `synthetic_reference.png`
  - `word_timings.json`
- Fixture hashes are recorded in `browser-runtime.json`.
- Both generated/final artifacts matched the synthetic source hash
  `6fecc6baff45fa6bc210e3864d15a99e663f7215f97b5a3c8f4fc7d91c51165f`;
  both comparison artifacts matched
  `3d5c132e059afe3888ce396a1e5ee122cd11d5ae7b3f775f47fa12a0931b765d`.

## Reduced-motion proof

Artifact: `reduced-motion-devtools-proof.jpg` (2582x1900).

The inspected browser was native Google Chrome `155.0.8059.80`, identified
through `navigator.userAgentData.getHighEntropyValues`. DevTools explicitly
emulated `prefers-reduced-motion: reduce`; this is browser media emulation, not
a body class or source-code mutation.

The visible DevTools/console receipt records all of the following on the
completed `.result` element:

- `matchMedia('(prefers-reduced-motion: reduce)').matches === true`
- `animationName === "none"`
- `animationDuration === "0s"`
- `transitionDuration === "0s"`

This closes the prior gap where only body CSS or a failed native capture was
available.

## Keyboard focus proof

The complete control-to-artifact map is in `focus-sequence.json`.

### Non-native controls

- `non-native-focus-sheet-1.jpg` (1620x2632): steps 8-15.
- `non-native-focus-sheet-2.jpg` (1620x2632): steps 16-20 and 35-37.
- `native-focus/brand-link-focus.jpg` (1280x720): brand link.

These cover brand, source/reference/timing inputs, identity textarea, seed,
consent, prepare, reset, workflow/prompt links, run, and all three download
links with visible focus outlines.

### Native media controls

- `native-focus/source-control-bars2-sheet.jpg` (830x1728):
  six source-player controls.
- `native-focus/final-control-bars2-sheet.jpg` (610x1668):
  six final-player controls.
- `native-focus/comparison-control-bars2-sheet.jpg` (610x1946):
  six paired-review controls.

Each sheet shows the browser focus indicator moving through play, volume,
mute, fullscreen, overflow menu, and timeline. The earlier "traversed but no
visible subcontrol ring" gap is therefore closed with per-control image
evidence.

### Conditional recovery control

`health-retry-focus.jpg` (1280x720) shows the disconnected legacy backend and
the `Check connection again` control reached by keyboard with a visible focus
outline. The isolated legacy server on `127.0.0.1:8895` reported
`renderer_ready=false` / `renderer_unreachable`, while local app health
remained truthful.

## Regression reconciliation

The first two focused runs and first two full runs intentionally recorded RED:
the stale capstone assertion expected the pre-OJ-c1vo four-field health body.
The accepted readiness work correctly adds `renderer_ready` and `renderer`.

`tests/test_frontend_regression.py` now checks the original four fields as a
subset and additionally requires dry-run renderer readiness
`local_dry_run`. No production code was changed in this story.

### Commands

From the story worktree, using the repository virtual environment:

```sh
PYTHONPATH=src <repo>/.venv/bin/python -m pytest -q tests/test_frontend_regression.py
PYTHONPATH=src <repo>/.venv/bin/python -m pytest -q
```

### RED evidence

- `test-runs/focused-1.txt`: 1 failed, 3 passed, 1 warning.
- `test-runs/focused-2.txt`: 1 failed, 3 passed, 1 warning.
- `test-runs/full-1.txt`: 1 failed, 104 passed, 1 warning.
- `test-runs/full-2.txt`: 1 failed, 104 passed, 1 warning.

### GREEN evidence

- `test-runs/focused-green-1.txt`: 4 passed, 1 warning.
- `test-runs/focused-green-2.txt`: 4 passed, 1 warning.
- `test-runs/full-green-1.txt`: 105 passed, 1 warning.
- `test-runs/full-green-2.txt`: 105 passed, 1 warning.

The warning is the existing Starlette/httpx deprecation. No regression is
skipped.

## Runtime and cleanup

- Native Chrome proof engine: Google Chrome `155.0.8059.80`.
- IAB replay viewport: 1280x720, runtime `26.1002.52244`.
- Native reduced-motion proof used DevTools responsive width 849 CSS px;
  its saved raster is 2582x1900.
- Servers on loopback ports 8894 and 8895 were stopped; final `lsof` showed
  no listener on either port.
- The two temporary IAB QA tabs were explicitly closed.
- The temporary native Chrome Openjutsu QA tab was explicitly closed; the
  operator's pre-existing browser tabs were preserved.
- DevTools reduced-motion emulation was tab-scoped and was removed when that
  QA tab closed. No OS accessibility setting was changed.
- Checked-in text was sanitized for user-specific worktree and pytest temporary
  paths and contains no credentials.

## Acceptance verification

| AC | Verification | Result |
|---|---|---|
| 1 | Two real dry-run browser jobs completed through the real loopback API with synthetic fixtures and no mocks | PASS |
| 2 | Prior desktop/mobile evidence retained; new reduced-motion proof is a completed-state image with hash in `SHA256SUMS` | PASS |
| 3 | Brand, every DOM control, all 18 exposed native media subcontrols, both media containers, all downloads, and conditional health recovery show keyboard focus | PASS |
| 4 | Prior negative/stale evidence retained; disconnected legacy state and recovery control re-proved against accepted OJ-c1vo behavior | PASS |
| 5 | Focused and full deterministic suites each pass twice after the RED-to-GREEN contract reconciliation | PASS |
| 6 | Exact native engine version, IAB runtime, viewports/rasters, fixture hashes, commands, and clean teardown are recorded | PASS |
| 7 | Story changes are limited to one stale test assertion and browser/test evidence; no production semantics or external spend changed | PASS |

LEARNINGS: Native video subcontrols need cropped control-bar sheets; full-page
traversal screenshots do not make the small focus ring legible. A completed
job is also necessary for reduced-motion proof because the target animation
lives on `#result`.

OBSERVATIONS: The stale health assertion was useful, not a false failure: it
exposed that the capstone had not yet reconciled with the accepted readiness
contract. Browser emulation must be tab-scoped and removed with the QA tab.
