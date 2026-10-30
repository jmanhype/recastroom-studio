# OJ-vqyg native M1 capstone receipts

This directory contains only native local-runtime evidence. It does not claim
provider execution, H3 qualification, deployment, or publication.

## Initial focused journey

- Managed HEAD: `6ccfa7ccd064628ff9edf2f72c40903688526fa1`
- Command: `APP/.venv/bin/python -m pytest -q tests/e2e/test_m1_journey.py`
- Result: exit 0, **1 passed in 19.09s**, 0 skipped
- Boundaries: actual headless Chrome channel, four isolated uvicorn processes,
  one SQLite workspace, in-process managed worker plus real FFmpeg/ffprobe,
  real multipart uploads, replay import, selection CAS, export, and attachment
  download. No test doubles or provider transport.
- The only browser resource error was the app's pre-existing `/favicon.ico`
  404. There were zero browser JavaScript page errors. The two 422 responses
  are required unchecked-attestation refusals and the one 409 is the required
  stale selection protection.

## Receipts

| Artifact | Fact |
|---|---|
| `journey-receipt.json` | Public source/CPU/replay/export hashes, restarts, counts, frames, PTS, pixel/audio checks, qualification boundary |
| `phase-receipts.json` | Browser phase states, requests, attestation refusals, duplicate authorization, challenger/cancel, review/selection/export state |
| `server-receipts.json` | Four loopback server log hashes, process start/finish, response-class counts, server-3 worker-disabled mode |
| `focused-managed-inherited.json` / `.txt` | Exact focused command, inherited environment, HEAD, exit, pass count, and log hash |
| `01-source-cuts.png` | Browser project/character/source upload and exact three-shot partition |
| `02-cpu-dry-runs.png` | Two explicit CPU dry-run completions and idempotent duplicate authorizations |
| `03-challenger-truthful-cancel.png` | Challenger authorization and provider-confirmed cancellation without refund claims |
| `04-review-selection.png` | Retained replay lineage, synchronized review, reselect/deselect/select evidence |
| `05-export-download.png` | Frozen trim/reorder/pass-through/audio-policy export and actual download |
| `actual-download.mp4` | Bytes downloaded by Chrome; SHA-256 matches the API export record |
| `SHA256SUMS` | Hash index for all files in this receipt bundle |

The full managed/ordinary inherited/strict matrix and final delivery proof are
intentionally absent until those synchronous commands run at the committed HEAD.
