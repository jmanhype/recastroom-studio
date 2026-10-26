# Parent verification — OJ-c1vo

2026-10-18. No GPU, Comfy server, remote deployment, or AI inference was used.
The real app ran on isolated loopback port 8894; a labelled protocol fixture on
8895 returned either HTTP 503 or a minimal `system` object plus `devices` list.
It rejects all POST requests. Synthetic media here is QA-only, not a creative output.

## Observed browser sequence

1. Renderer HTTP 503: the banner showed disconnected. Selected the repository's
   synthetic source/reference and attested the synthetic fixture permissions.
   Preparation succeeded, job `d79e57214aa7`; Run stayed disabled.
2. Changed the protocol fixture to its minimal success payload and clicked
   **Check connection again**. Same job and consent remained; Run became enabled.
   The banner explicitly did not verify model availability, cost, or location.
3. Changed the fixture back to HTTP 503, then clicked the previously enabled Run.
   Its fresh health check blocked submission. UI showed **RUN BLOCKED**,
   **No run request was sent**, preserved both file selections and consent, kept
   Prepare available, and offered connection retry rather than job-status retry.

`browser/receipt.json` records seven app requests: static/health reads and one
local prepare POST. There were **zero run POSTs** and **zero fixture POSTs**.
The fixture received exactly three GET /system_stats requests: 503, 200, 503.
The prepared workflow exists; no status.json was created (no queued status).
Screenshots and hashes are under `browser/`.

This verifies readiness recovery, not successful rendering or complete SDK
compatibility. The server-side race guard and unknown-submission paths are
covered by code review and tests; the three screenshots do not represent a
successful Comfy job.

## Independent parent checks

- Full pytest run 1: 63 passed, one existing Starlette/httpx warning, 77.02s.
- Full pytest run 2: 63 passed, same warning, 337.84s.
- Worker evidence hashes verified; JavaScript syntax and git diff checks passed.
- No existing tests modified; workflow, models, dependencies and actual app media unchanged.
- Beads sync reported no Beads database. The existing shared Paivot nd tracker
  remains the source of record; no second database was initialized.

Parent test logs are preserved in `browser/parent-pytest-*.txt`. Runtime and
filesystem checks are independent of the worker's reported test results.
