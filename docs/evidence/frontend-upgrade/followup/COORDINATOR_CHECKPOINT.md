# OJ-yf2c follow-up checkpoint — not capstone acceptance

Date: 2026-10-18. This is the authoritative follow-up to the earlier REPORT.md and
the evidence worker's FOLLOWUP.md. Those snapshots are retained unchanged except
for a navigation note in REPORT.md; their pending/live-state statements are historical.

## Accepted status repair

- OJ-p8rd was independently accepted by PM at source commit
  `a7ed346407ad0f97cdf80795132c6655995e5a9b` and locally merged into epic
  `7881cb0762ef53556995f036166bb6a85c95a899`.
- The accepted source makes status publication atomic using a unique same-directory
  temporary file, closed before os.replace, under an in-process status lock.
  It does not add multiprocess coordination or fsync/power-loss durability.
- The deterministic old-source control fails at HTTP 500 versus expected 200;
  repaired focused tests pass repeatedly. Nine source/evidence hashes were rechecked.
- Real CUA retry on an isolated dry-run job completed: four status GETs returned 200,
  zero status 500s, and the final download matched persisted bytes. The single run
  404 was intentional missing-job recovery, not the status race. See the accepted
  `docs/evidence/status-atomic/OJ-p8rd/BROWSER.md` and browser receipts.

## Combined tests and evidence

From capstone HEAD `5bc83e8`, with the accepted repair merged:

```sh
PYTHONPATH=src <repo>/.venv/bin/python -m pytest -q
```

- integrated-tests-1.txt: **52 passed, 1 warning in 17.31s**.
- integrated-tests-2.txt: **52 passed, 1 warning in 16.67s**.
- The warning is the existing Starlette/httpx deprecation. No skipped regression.
- Parent independently verified all 47 worker screenshot hashes against both the
  copied bytes and originals, checked dimensions with sips, and verified both text
  hashes. Worker manifest hash:
  `b93cb4119232fe7ba120bf13dc6377fe02740569758df21da46ba132a8c9b791`.
- The screenshots show synthetic QA fixtures, not a replacement creative reference
  and not a new AI render. These tests did not alter the approved media.
- Application controls, three native media containers and six native subcontrols
  per player were traversed by keyboard. Download, reset, status recovery, and
  genuine unavailable-then-restored backend health recovery were exercised.
- Clarification to the worker narrative: the isolated job directory was moved aside
  to produce the deliberate run 404, then restored before keyboard status recovery.
- Both new QA tabs were explicitly closed before stopping their servers; the observed
  IAB tab inventory retained only the original 8893 tab. Viewport override reset.
  Ports 8894 and 8895 have no listener in the final check.

## Local recovery incident and current preview

After context recovery, the required `pvg loop recover` unexpectedly removed the
preview checkout and its epic branch while the preview process was still alive.
A page GET returned 500 and health reported workflow_exists=false. This was a
checkout-removal incident, separate from the fixed status-file race. No data or
approved media was stored in that checkout.

The coordinator restored the exact epic commit `7881cb0` and branch at the original
preview path from the retained capstone history, restored the accepted OJ-p8rd
source branch, and restarted the same startup script/config/data as PID 49984.
No production code was changed during recovery. `LIVE_CHECK.json` records:

- page, health, and original job status HTTP 200;
- workflow_exists=true, backend legacy, original job state complete;
- preview HEAD 7881cb0 and clean worktree;
- final and comparison files still byte-identical to the pre-repair hashes;
- no QA listeners and zero GPU/API inference spend for this repair.

The owner preview remains intentionally running on loopback 127.0.0.1:8893.
This is not a new render or a proof of current external Comfy/GPU availability.
No push, publication, public tunnel, design change, or approved-media overwrite.

## Remaining acceptance gaps

| AC | Checkpoint |
|---|---|
| 1 | Real dry-run flow and keyboard download proven, including repaired retry |
| 2 | Prior desktop/mobile/motion screenshots retained; follow-up hashes verified |
| 3 | Keyboard traversal improved; exhaustive native visible-focus proof and actual reduced-motion suppression remain OPEN |
| 4 | Earlier negative/stale tests retained; corrected retry and real health recovery added |
| 5 | Integrated full suite 52 passes twice; previous focused evidence retained |
| 6 | Commands/fixture/evidence hashes and new QA cleanup recorded; exact IAB patch version remains OPEN |
| 7 | This checkpoint adds only evidence; production repair separately accepted in OJ-p8rd |

Two fresh native Chrome capture attempts failed with ScreenCaptureKit error -3811.
The earlier computed body CSS is insufficient to prove suppression of the actual
`#result` animation. Do not count it as full reduced-motion proof. The request UA's
Chrome/155.0.0.0 is a reduced token, not an exact engine patch build. Native media
traversal does not by itself establish a visible focus ring on every subcontrol.
No full WCAG, release, or capstone acceptance claim is made; OJ-yf2c stays open.

LEARNINGS: Capture failure must leave the animation-specific proof open. Paivot
recovery can remove a serving checkout; verify retained commits and restore the
identical preview before reporting liveness.

OBSERVATIONS: The status fix is accepted and live. Full frontend regression
acceptance remains pending the explicitly listed browser evidence.
