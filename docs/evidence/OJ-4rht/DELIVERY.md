# OJ-4rht — frontend delivery

Implementation commit: b5fd8e4 (follow-up reset/error fixes in delivery commit).
Only app/web and this evidence directory changed. No dependencies, backend,
generation, workflows, credentials, remote calls or GPU execution added.

## Design
Charcoal editorial workspace with a muted ochre accent, large source monitor,
two reference monitors, secondary direction panel, and paired review players.
Vanilla HTML/CSS/JS; system-installed Helvetica Neue/Menlo font stacks; no font
network dependency. Native inputs, labels, focus outlines and reduced-motion CSS.
Visual quality remains subject to operator review, not a machine score.

## Measured verification
- Final browser pass includes word_timings.json, source and reference fixture:
  job b1f444cbd21a reached COMPLETE; timed-review.jpg records this final-code run.
- `env -u OPENJUTSU_DATA_DIR PYTHONPATH=src <root>/.venv/bin/python -m pytest -q`:
  31 passed, one existing Starlette/httpx deprecation warning (pytest.txt).
- `git diff --check` and `node --check app/web/studio.js`: exit 0.
- CUA IAB at http://127.0.0.1:8892 with dry_run backend; real file chooser uploads
  tests/fixtures/synthetic_source.mp4 and synthetic_reference.png.
- Manually checked rights; prepared job `3af79afdac1c`; clicked Run; observed
  DOWNLOADING then COMPLETE. Final and side-by-side video players rendered.
  All three artifact links were present only after completion.
- Browser downloaded side_by_side to `<downloads>/side_by_side.mp4`.
  Download and server source_vs_final.mp4 share SHA256
  `eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9`.
- Screenshots desktop-review.jpg and mobile-review.jpg show actual synthetic
  media and completed job; SHA256SUMS contains exact hashes.
- Widths 375, 414, 768, 1024, 1440: document scrollWidth equalled viewport width
  at each size. No horizontal overflow measured. Viewport override reset.
- Two-reference job `c00bba38d22c` prepared with keyboard Space rights consent.
  Reset immediately after Run hid result, cleared source/reference previews,
  unchecked rights and disabled prepare. After server status reached COMPLETE,
  result remained hidden and prepare disabled. reset.jpg captures cleared state.
- Browser testing exposed form.reset name-clobbering by the reset button.
  Fixed using HTMLFormElement.prototype.reset.call(form), then reloaded and
  repeated reset successfully. Initial console error is historical, not hidden.
- Malformed word-timing input (synthetic PNG deliberately selected as words)
  returned an inline PREPARATION STOPPED error with corrective instructions;
  run stayed disabled and prepare was available for retry. Follow-up fix replaces
  stale uploading text with 'No runnable job was prepared.'

## State safety
Each input change/reset increments an epoch, aborts old requests, clears polling
and result links. Prepare/run/poll capture epoch and job ID before awaiting.
Changing source/reference also clears manual rights. Replaced object URLs are
revoked. API messages use textContent/append text; artifact URLs are constructed
from validated job IDs and fixed artifact names, never arbitrary server URLs.
Unknown health disables preparation; non-dry backends make no cost/local claim.
Uncertain run/status failure offers status retry instead of blind duplicate run.

## Limitations / next acceptance
- No paid/live inference tested; dry_run copies source and explicitly says so.
- No screen-reader session, formal WCAG audit or full error/race regression suite
  claimed. Dependent regression story should test delayed fetch permutations,
  unknown health, run/status failures, object URL lifecycle and malformed payloads.
- Browser codecs determine source-preview compatibility; server preflight remains
  authoritative. Reset does not cancel backend work or delete uploaded data.
- Source is visible above the final player; the paired artifact supplies the
  synchronized comparison. No fabricated stage percentages, ETA or quality score.

## LEARNINGS
Do not call form.reset directly if any form element uses id/name reset.
IAB visibility options are unsupported in subagent threads; omit that option.

## OBSERVATIONS
Baseline tests do not cover frontend interaction. Actual browser smoke caught a
reset bug that Python tests alone could not detect. Independent PM acceptance
and operator aesthetic review remain required.
