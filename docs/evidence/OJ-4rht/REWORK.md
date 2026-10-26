# OJ-4rht — portrait-preview rework receipt

Rework base: `63b9c005e64fcfa0bdba04ee798acaedd79450e7`
Scope: `app/web/styles.css`, one CSS regression test, and this receipt only.
No backend, media, graph, dependency, browser-automation, GPU, or remote-work
changes are included.

## DISCOVERED_BUG

```yaml
id: OJ-4rht-portrait-reference-clipping
status: fixed-and-browser-verified
severity: visual-regression
component: app/web/styles.css reference previews
evidence: frontend-evidence/dogfood-20261017/live/browser-playback.json (raw evidence outside repository)
observed:
  natural_size: 1086x1448
  box_size: 285x150
  rendered_size: 283x377.328125
  object_fit: contain
diagnosis: >-
  A centered grid item falls back to its content-based automatic minimum size.
  A tall portrait therefore forces the image beyond the fixed 150px reference box
  even though width/height 100% and object-fit contain are present.
repair: >-
  Set min-width:0 and min-height:0 on the shared .reference-screen img rule.
  Both reference boxes use that rule at mobile and desktop heights; object-fit
  contain continues to preserve portrait and landscape aspect ratios.
verification: static regression test plus independent post-fix browser proof at 1649a93.
```

## Baseline warning triage

```yaml
DISCOVERED_BUG:
  id: starlette-httpx-testclient-deprecation
  status: open-existing-warning
  component: repository test dependency stack
  observed: StarletteDeprecationWarning from fastapi/testclient.py advising httpx2
  impact: test warning only; no failed test or frontend behavior demonstrated
  owner-action: centralized dependency triage; intentionally not repaired in this frontend story
```

## Nine-AC proof map

| AC | Current exact proof status |
|---|---|
| 1. Responsive cinematic layout, live source/two-reference previews, accessible controls | PROVED for this rework. Both reference positions were tested with portrait 1086×1448 and landscape 1152×768 at 1440×1000 and 390×844. Boxes were exactly 472×198 desktop and 165×148 mobile, `object-fit` was `contain`, minima computed to `0px`, and no reference overflow occurred. Parent visual inspection of the two screenshots found the complete head/torso and no clipping. `portrait-and-focus.json` records all measurements; keyboard traversal proved six visible 2px gold focus outlines. |
| 2. Guided flow and manual unchecked rights gate | MEASURED + RETAINED. `dryrun-browser-proof.json` records rights false and Prepare disabled before consent; the browser pass manually checked consent, prepared, ran, and exercised reset. `app/web/studio.js:23-35` derives the gate from required files and manual consent, and `app/web/studio.js:73-78` clears consent when media changes. |
| 3. Only API-backed queued/uploading/generating/downloading/complete/error truth | MEASURED + RETAINED. The post-fix pass observed PREPARING, DOWNLOADING, and COMPLETE. `app/web/studio.js:107-131` renders the returned `status.state`/`status.message`, handles complete/error, and schedules polling otherwise; no percentage, ETA, invented state, or QC verdict appears in the browser snapshot. Other API states rely on that unchanged source plus retained prior delivery evidence rather than a claim that this pass exercised all six. |
| 4. Backend-conditional dry-run/no-AI disclosure | MEASURED + RETAINED. Dry-run browser snapshots disclose “No AI inference” during download and completion. `app/web/studio.js:67-69,114-116` applies that wording only when backend is `dry_run`; other backends are labeled without the no-inference claim. |
| 5. Complete source/result review and three real artifact routes | PROVED. Job `c2a3a70973ec` reached COMPLETE, rendered final and paired review players, and exposed exactly the three real API artifact links. Browser downloads and server copies matched byte-for-byte for all three SHA-256 values recorded in `dryrun-browser-proof.json`. |
| 6. Visible recoverable errors and non-reloading reset | MEASURED + RETAINED. Post-fix reset returned rights false, empty source/reference values, hidden review, and disabled Prepare. `app/web/studio.js:38-43,82-86` resets without reload; `app/web/studio.js:104,128-136` exposes prepare/run/status failures with retry or reset. Malformed-input/error-path behavior is retained prior evidence; this CSS rework changed neither path. |
| 7. Static vanilla frontend, backend/API/generation preserved, baseline suite | Diff is CSS/test/receipt only; exact test, Node syntax, and whitespace-diff commands are recorded below. |
| 8. Real browser dry-run loopback health/prepare/run/status/artifact exercise | PROVED at `1649a93` through the real browser/UI job `c2a3a70973ec` on loopback port 8894: consent gate, prepare, run, DOWNLOADING, COMPLETE, review links, all three downloads, and reset. Observation timestamps include tool gaps and are not backend latency. |
| 9. Portrait and landscape performer-reference previews preserve the complete intrinsic image | PROVED. Both slots were tested with 1086×1448 portrait and 1152×768 landscape at 1440×1000 and 390×844. Stated tolerance is `abs(content_ratio - natural_ratio) <= 0.01`; `object-fit: contain` yields uniform scale and content ratios 0.75/1.5 exactly. Measured boxes were 472×198 desktop and 165×148 mobile, with no overflow, and parent visual inspection confirmed the full head/torso (including face/chin) in both screenshots. |

## Verification

Commands planned/recorded for this worktree:

```sh
env -u OPENJUTSU_DATA_DIR PYTHONPATH=src ../../../.venv/bin/python -m pytest -q
node --check app/web/studio.js
git diff --check
```

Exact local pre-commit outputs:

- Pytest: `32 passed, 1 warning in 10.91s`; full output in
  `docs/evidence/OJ-4rht/rework-pytest.txt`.
- Node syntax check: exit `0`, no output; recorded in
  `docs/evidence/OJ-4rht/rework-nodecheck.txt`.
- `git diff --check`: exit `0`, no output; recorded with exit codes in
  `docs/evidence/OJ-4rht/rework-diffcheck.txt`.
- Independent root rerun at `1649a93`: `32 passed, 1 existing warning in
  10.48s`; Node syntax and diff checks also exited `0`.

### Independent post-fix browser evidence

All evidence below was obtained by the parent against fix commit
`1649a937fd8685076abf522158f4783ea830edfe`; raw evidence remains outside the
repository to avoid unrelated Chrome inventory and private download paths.

- `rework/portrait-and-focus.json`: both reference positions, portrait and
  landscape, mobile and desktop; equal image/container boxes, `contain`, zero
  minima, no overflow, and rights false. `portrait-desktop.png` and
  `portrait-mobile.png` visually record the full head/torso without clipping.
- `rework/keyboard-focus.png`: Tab traversal from the second reference summary
  through words, identity, seed, rights, and reset. The JSON records a visible
  `rgb(216, 199, 145) solid 2px` outline on each focused control; disabled
  Prepare was correctly skipped.
- `rework/reduced-motion-proof.txt` and
  `rework/reduced-motion-computed.png`: Chrome DevTools live reduce emulation
  selected body and showed animation-duration/name `0s`/`none`,
  transition-duration/property `0s`/`none`, scroll-behavior `auto`, and the
  active universal reduced-motion rule. Emulation was restored afterward.
- `rework/dryrun-browser-proof.json` and `rework/dryrun-complete.png`: real UI
  dry-run job `c2a3a70973ec`, manual rights gate, prepare/run/download/complete,
  three artifact links, matching server/download hashes, and post-complete reset.

The checked-in browser records are sanitized. `rework/SHA256SUMS` records the
copies; the reduced-motion text records original raw-file hashes and selected
line-number extracts without copying unrelated browser inventory.

The Starlette/httpx warning and separately reported media/backend findings are
not represented as repaired by this frontend change; they remain with their
assigned centralized or media-story owners.

## Boundary statement

`window.StudioUI` remains a read-only observation API (`getState` and
`errorText`). This rework does not add mutable test seams or alter StudioUI.
Tracker BoundaryMap reconciliation belongs to SrPM; dependent user-driven
regression work belongs to OJ-yf2c.
