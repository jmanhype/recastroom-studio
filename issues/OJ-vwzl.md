---
id: OJ-vwzl
title: "Complete hosted upload-to-output execution"
status: in_progress
priority: 1
type: feature
labels: [contest, app, e2e]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T19:15:24Z
content_hash: "sha256:5798e4f4417217b0eaf4fb9669caa4228dd6a017f40cdc90f24c95865193807d"
blocks: [OJ-2t3g, OJ-mbn5]
was_blocked_by: [OJ-i6n6]
assignee: dev-OJ-vwzl
follows: [OJ-i6n6, OJ-ef2q]
---

## Description

## Context

The app can prepare a job and serve workflow/prompt artifacts, while the hosted
generation-to-download loop is not yet proven end to end.

## Required outcome

A reviewer can upload owned inputs, pass the rights gate, execute a configured
backend, monitor status, download the result, and receive restored-audio review
artifacts.

## Acceptance evidence

1. Exercise upload, preflight, timing, rights attestation, queueing, status, download, audio restoration, and side-by-side output.
2. Include API and browser evidence from a clean checkout.
3. Preserve fail-closed behavior for unattested or invalid rights inputs.
4. Record commands, HTTP responses, media probes, and output hashes.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md`, the app walkthrough in `STATUS.md`, and demo v1 receipts.

### proof
- [ ] AC #1: The full hosted path returns a downloadable final media artifact.
- [ ] AC #2: The rights gate rejects missing or invalid attestation before execution.
- [ ] AC #3: Tests and clean-checkout smoke output pass.
- [ ] AC #4: Every public artifact has a SHA-256 receipt and ffprobe record.


## Observable outcome
The story returns pass/fail evidence and stores every artifact referenced by its proof block.

## MANDATORY SKILLS
None identified.


## Context

The app can prepare a job and serve workflow/prompt artifacts, while the hosted
generation-to-download loop is not yet proven end to end.

## Required outcome

A reviewer can upload owned inputs, pass the rights gate, execute a configured
backend, monitor status, download the result, and receive restored-audio review
artifacts.

## Acceptance evidence

1. Exercise upload, preflight, timing, rights attestation, queueing, status, download, audio restoration, and side-by-side output.
2. Include API and browser evidence from a clean checkout.
3. Preserve fail-closed behavior for unattested or invalid rights inputs.
4. Record commands, HTTP responses, media probes, and output hashes.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md`, the app walkthrough in `STATUS.md`, and demo v1 receipts.

### proof
- [ ] AC #1: The full hosted path returns a downloadable final media artifact.
- [ ] AC #2: The rights gate rejects missing or invalid attestation before execution.
- [ ] AC #3: Tests and clean-checkout smoke output pass.
- [ ] AC #4: Every public artifact has a SHA-256 receipt and ffprobe record.

## MANDATORY SKILLS
None identified.


## Context

The app can prepare a job and serve workflow/prompt artifacts, while the hosted
generation-to-download loop is not yet proven end to end.

## Required outcome

A reviewer can upload owned inputs, pass the rights gate, execute a configured
backend, monitor status, download the result, and receive restored-audio review
artifacts.

## Acceptance evidence

1. Exercise upload, preflight, timing, rights attestation, queueing, status, download, audio restoration, and side-by-side output.
2. Include API and browser evidence from a clean checkout.
3. Preserve fail-closed behavior for unattested or invalid rights inputs.
4. Record commands, HTTP responses, media probes, and output hashes.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md`, the app walkthrough in `STATUS.md`, and demo v1 receipts.

### proof
- [ ] AC #1: The full hosted path returns a downloadable final media artifact.
- [ ] AC #2: The rights gate rejects missing or invalid attestation before execution.
- [ ] AC #3: Tests and clean-checkout smoke output pass.
- [ ] AC #4: Every public artifact has a SHA-256 receipt and ffprobe record.


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: delivered

### evidence
- Implementation commits: `c9e729e832494eb65f5e383fb09a602d3ad2d2f6` (deterministic dry-run backend, fixtures, HTTP driver, tests), `95a8bc7a7d309be79bedc1abf16bb566a234b7e9` (optional-upload routing fix and browser driver), `dc2cd41256db0e030d20df013d35c0c9e39f4f4c` (committed E2E evidence).
- Clean detached checkout under test: `/private/tmp/oj-vwzl-clean.Uj9BdG` at `95a8bc7a7d309be79bedc1abf16bb566a234b7e9`; final evidence commit verified independently in `/private/tmp/oj-vwzl-clean.07Cksk` at `dc2cd41256db0e030d20df013d35c0c9e39f4f4c`.
- Full tests/dependency check at final clean HEAD: `python -m pytest -q` → `19 passed, 1 warning in 5.60s`; `python -m pip check` → `No broken requirements found`.
- API E2E: `tools/e2e_smoke.py --output-dir ... --dry-port 8903 --sdk-port 8904` → dry-run job reached `complete`, all generated/final/side-by-side downloads returned HTTP 200, and isolated SDK job reached error `missing_comfy_api_key` before network/client construction. Missing and invalid rights attestations both returned HTTP 422 before job creation.
- Browser E2E from the clean worktree: real browser uploaded synthetic source/reference/word timing, passed rights checkbox, prepared job `06e10c33b91b`, ran it, polled HTTP 200 to `complete`, and exposed all three download links. Full-page screenshot: `docs/evidence/OJ-vwzl-upload-to-output/browser/app-complete.png`.
- Evidence and probes: `docs/evidence/OJ-vwzl-upload-to-output/README.md`, `api/receipt.json`, `browser/browser-transcript.txt`, and `RECEIPTS.json`. All 12 committed evidence hashes verified from the final clean HEAD.
- No credentials were read or printed; no GPU/compute, deployment call, publication, social action, or push was performed.

### proof
- [x] AC #1: The full hosted dry-run path returns downloadable generated, restored-audio final, and source/final review media artifacts.
- [x] AC #2: Missing and invalid rights attestations are rejected with HTTP 422 before execution.
- [x] AC #3: Final clean-checkout tests and smoke output pass (`19 passed`, clean `pip check`, API E2E `ok:true`).
- [x] AC #4: Every recorded evidence artifact has a SHA-256 receipt; each media/image artifact has an ffprobe record.

## History
- 2026-10-17T16:26:04Z dep_added: blocked_by OJ-i6n6
- 2026-10-17T16:26:05Z dep_added: blocks OJ-2t3g
- 2026-10-17T16:27:21Z dep_added: blocks OJ-mbn5
- 2026-10-17T18:52:21Z dep_removed: was_blocked_by OJ-i6n6
- 2026-10-17T18:55:24Z status: open -> in_progress
- 2026-10-17T18:55:24Z auto-follows: linked to predecessor OJ-i6n6
- 2026-10-17T18:55:24Z claimed by dev-OJ-vwzl
- 2026-10-17T19:15:24Z status: in_progress -> in_progress
- 2026-10-17T19:15:24Z auto-follows: linked to predecessor OJ-ef2q

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-2t3g]], [[OJ-mbn5]]
- Was blocked by: [[OJ-i6n6]]
- Follows: [[OJ-i6n6]], [[OJ-ef2q]]

## Comments
