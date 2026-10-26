# Backend readiness evidence

## Scope delivered

- Added a legacy-only readiness check using one side-effect-free `GET /system_stats`, short connect/read timeouts, no retries, no redirects, and Comfy `system`/`devices` schema validation.
- Kept local app health (`ok`) separate from renderer readiness. Dry run remains explicitly local/no-AI; SDK reachability remains explicitly unchecked.
- Added an independent run-endpoint refusal before queued status, upload, or renderer submission. Existing missing-job 404 and active-job 409 behavior is preserved.
- Added UI Run gating, visible disconnected/checking state, connection recheck, pre-submit fresh check, and prepared-state preservation. A proven pre-submit failure says no request was sent; a structured legacy guard 503 says the server refused before queueing. Other post-submit failures retain uncertain/running safety.
- Kept errors sanitized and actionable without exposing configured URLs, credentials, or raw exceptions.

## Verification

- Focused readiness suite: 15 passed; one pre-existing Starlette/httpx deprecation warning.
- Full suite run 1: 63 passed; exit 0; same warning.
- Full suite run 2: 63 passed; exit 0; same warning.
- `node --check app/web/studio.js`: passed.
- Python compile check for the modified backend/readiness modules and new test module: passed.
- Transport failures tested with actual TestClient calls plus a labelled loopback HTTP fixture: offline refusal, timeout, malformed JSON, non-Comfy schema, schema mismatch, HTTP error, redirect, and fresh-check recovery. Bounded mocks are used only for exception sanitization and runner-task boundaries.
- No browser QA, deployment, GPU use, credentials, media/workflow changes, commits, tracker transition, or non-loopback network access is claimed.
