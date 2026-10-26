# Coordinator browser verification

2026-10-18, real local CUA, production patch SHA-256
`ace2ab9e2a658fdb60e9f75594a53271f8adc3f40b53430ecfce9e8649b24aa1`.

The actual ASGI app ran in `dry_run` on `127.0.0.1:8894`, with an isolated
data directory and passive request logging. The logging wrapper only recorded
response status and request User-Agent; it did not replace routes or responses.
All three repository synthetic fixtures were selected through keyboard-opened
file choosers. These are test media, not a new creative render.

1. Prepare job `85b97f14514e` through the UI with rights consent.
2. Temporarily move only its isolated uploaded source file aside. Enter on Run
   produces an actual terminal ERROR. Restore the same source file.
3. Enter on Run retries the real backend. CUA observes DOWNLOADING then COMPLETE,
   no status error, and all three artifact links. The downloaded final is byte
   identical to the persisted final; SHA-256 is in `browser/receipt.json`.
4. Separately move the prepared job directory aside and Enter Run: actual404,
   conservative duplicate-run lock. Restore it; Tab reaches Check job status
   again with visible 2px focus; Enter recovers to COMPLETE.

The captured run has four status GETs, all HTTP200; no HTTP500. The one run404
is the intentional missing-job scenario. This finite browser observation is
not a probabilistic guarantee; deterministic publication barriers and the
180-request concurrent test in REPORT.md establish the specific regression.

Runtime evidence: 1440x1000 viewport; observed request User-Agent declares
Chrome/155.0.0.0 (reduced UA, not an exact Chromium patch build), in Codex IAB.
See `browser/requests.jsonl`, sanitized AX/DOM `events.json`, screenshot hashes,
and `receipt.json`. The coordinator independently reran the focused suite:
7 passed, 1 preexisting warning in 0.52s; all worker SHA256SUMS entries matched.

Both temporary QA tabs were explicitly closed before server shutdown. Tab list
then contained only the original `http://127.0.0.1:8893/`. Viewport reset.
Test server PID28235 terminated with143, Uvicorn confirmed shutdown complete;
no8894/8895 listener remained, approved8893 still PID82602. No inference spend,
approved render changes, design changes, external publication, or push.

LEARNINGS: Close QA tabs before stopping their server to avoid error-page
navigation policy preventing explicit tab cleanup.

OBSERVATIONS: The approved8893 process has not yet been restarted onto the fix;
this receipt proves the isolated test process. Deployment is separate from code acceptance.
