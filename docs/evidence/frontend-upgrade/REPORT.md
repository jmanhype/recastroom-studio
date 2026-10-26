# OJ-yf2c local browser regression checkpoint

> Historical checkpoint. See `followup/COORDINATOR_CHECKPOINT.md` for the accepted
> status-race repair, repeated 52-test results, current preview recovery, and the
> corrected reduced-motion evidence boundary. The capstone is still not accepted.

Date: 2026-10-18. Production source: `2b22504`. **Not an all-green release gate.**
No production source, approved render, design, workflow, dependency, or GPU session changed.

## Results

- Real CUA upload/consent/prepare/run/status/compare/download completed against isolated
  `http://127.0.0.1:8894/`, backend `dry_run`, using all three repository synthetic fixtures.
  These QA fixtures do not replace the approved real performer reference or render on port 8893.
- Job `34b7d2ac2f9a` showed PREPARED, then real DOWNLOADING in CUA accessibility output,
  then COMPLETE. The later DOM sample labelled active was already COMPLETE; the receipt
  explicitly corrects that label rather than claiming it as active-state evidence.
- The final download was activated with Enter and is byte-identical to the persisted final.
  All three artifact links were visible only after completion. Both review videos decoded
  with readyState 4, duration 2.048s; final 640x240, comparison 1920x384.
- Desktop 1440x1000 and mobile 390x844 had no document horizontal overflow. Actual review
  crops are 1344x835 and 350x1198. Screenshot byte encoding is JPEG despite historical
  `.png` filenames; bytes were not converted or edited. See `browser/receipt.json`.
- Missing consent kept Prepare disabled. Invalid timing JSON produced an actual HTTP422
  and actionable preparation error. Replacing the timing file recovered to a new prepared job.
- Moving only the isolated prepared source aside produced a real terminal ERROR with no
  artifacts. Restoring it and retrying revealed the status-file race below. Check status again
  recovered to COMPLETE, with three artifacts. No provider response was mocked.
- Moving only an isolated prepared job directory aside gave a real 404 and conservative
  duplicate-run lock. After restoring the directory, an explicitly labelled unknown-state
  `status.json` fixture was read by the real endpoint; the UI kept Run disabled and showed
  zero artifacts. This injected unknown state is not real provider progress.
- Keyboard reset cleared inputs/rights/results and focused Source. Temporary file moves
  were restored. A new prepared job was proven, separate from the completed job.
- The UI disclosed source-copy/no AI, with no invented percent, ETA, QC score, or success.

## Keyboard and motion boundary

Keyboard traversal reached brand, source, reference 1, optional reference 2, details summary,
timings, identity, seed, rights, Prepare, Reset, workflow/prompt links, Run, video controls,
and download links. Source/reference/timings pickers were opened with Space; the CUA chooser
API supplied files. Prepare/Run/final download/status recovery/reset used keyboard activation.
Visible 2px accent outlines were measured for rights, Prepare, workflow link, Run and final
download; the consent-focus screenshot is retained. This is **not yet exhaustive focus proof
for every native media subcontrol or the conditional health-retry control**, nor a WCAG audit.

Chrome's real DevTools Rendering preference was set to `prefers-reduced-motion: reduce`.
Computed body CSS showed animation duration 0s/name none, transition duration 0s/property none,
and scroll-behavior auto. Screenshot and filtered native accessibility evidence are included.
Preference restored to No emulation and only the temporary Chrome tab was closed.

## Open defect: OJ-p8rd

The retry of job `5ead8146d6ad` produced a real GET status HTTP500, not an injected status.
Observed server traceback excerpt (transcribed from the tool output; private prefixes omitted):

```text
GET /api/jobs/5ead8146d6ad/status HTTP/1.1 500 Internal Server Error
app/main.py, line 330, in job_status
  return json.loads(status_path.read_text(encoding="utf-8"))
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

Source inspection: `_set_status` at app/main.py:141-144 uses truncating `write_text` while
the status route reads the same file concurrently. This supports a non-atomic publication
race diagnosis; the deterministic serial TestClient suite does not reproduce it.
The UI safely exposed status-unavailable and blocked duplicate submission; Enter on
Check job status again recovered to COMPLETE. See `browser/status-race-500.png`.
Backend repair is tracked separately, not silently bundled into this test-only story.

## Runtime and commands

- CUA In-app Browser, Codex app version 26.623.101652. Exact IAB engine/version was not
  exposed by the selected interface and is not inferred. This part of AC6 remains open.
- Native motion check: Google Chrome 155.0.8059.80 (installed app plist), responsive width
  855 and visible device-toolbar height 1520; captured native window is 3024x1900 pixels.
- Private raw evidence: operator workspace `work/frontend-evidence/capstone-20261018/`.
  Committed text replaces private prefixes; full terminal-error screenshot remains private.

Server command, with private paths normalized:

```sh
cd <repo>/.claude/worktrees/dev-OJ-yf2c
export PYTHONPATH="$PWD/src"
export OPENJUTSU_BACKEND=dry_run
export OPENJUTSU_DATA_DIR=<private-evidence>/app-data
<repo>/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8894
```

Automated focused/full commands and both outputs are in
`automated/AUTOMATED_REGRESSION_RECEIPT.md`: **4 focused tests twice; 45 full tests twice**,
one preexisting Starlette/httpx warning each. Prior 41 tests remain unchanged.
Parent independently reran the full suite; see `browser/parent-tests.txt`.

Teardown: PID379 received TERM, reported application shutdown complete and exit143;
`lsof` confirmed no listener on8894. Approved port8893 still listens under PID82602.
IAB viewport override reset. Explicit QA-tab close was blocked by the browser's error-page
URL policy after server shutdown; it was left unmarked for normal temporary-tab cleanup.
Do not count that as independently confirmed tab deletion. User's original tab was untouched.

## AC checkpoint (not acceptance)

| AC | Evidence / status |
|---|---|
| #1 | Proven real local dry-run flow and downloaded artifact |
| #2 | Desktop/mobile/reduced-motion screenshots and hashes present |
| #3 | Substantial keyboard and reduced-motion proof; exhaustive every-control focus proof remains open |
| #4 | Required negative scenarios exercised; real backend race reported, recovery proven |
| #5 | Focused/full repeated green; parent independent rerun; one disclosed warning |
| #6 | Commands, fixture hashes, app/Chrome versions, server teardown present; exact IAB engine version and explicit QA-tab cleanup not proven |
| #7 | Only tests/evidence added; no production semantics, dependency, spend, or publication changes |

LEARNINGS: Serial TestClient success cannot establish concurrent status-poll reliability.
Capture active UI state immediately; a later DOM sample can already be terminal.

OBSERVATIONS: OJ-p8rd is an actual backend defect, not a design regression. Keep the capstone
open until missing browser evidence is filled; do not promote this checkpoint to full acceptance.
