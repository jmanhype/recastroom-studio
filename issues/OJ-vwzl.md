---
id: OJ-vwzl
title: "Complete hosted upload-to-output execution"
status: in_progress
priority: 1
type: feature
labels: [contest, app, e2e, rejected]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T20:33:02Z
content_hash: "sha256:1832765fd6468994be87b12b37f724354f570d079abb88ac85a2b65156ef2187"
blocks: [OJ-2t3g, OJ-mbn5]
was_blocked_by: [OJ-i6n6]
follows: [OJ-i6n6, OJ-ef2q, OJ-fgc3]
assignee: dev-OJ-vwzl
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
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-17.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence

- Changed implementation: `app/main.py`, `app/web/index.html`, `src/openjutsu/config.py`.
- Tests, fixtures, and reproducible drivers: `tests/fixtures/`, `tests/test_app_e2e.py`, `tests/test_config.py`, `tools/e2e_smoke.py`, `tools/browser_smoke.sh`, `tools/build_e2e_receipts.py`.
- Public evidence: `docs/evidence/OJ-vwzl-upload-to-output/`.

### CI/Test Results

- `python -m pytest -q` at final clean HEAD → `19 passed, 1 warning in 5.60s`.
- `python -m pip check` at final clean HEAD → `No broken requirements found`.
- Final clean API E2E → dry-run complete; generated/final/side-by-side HTTP 200; SDK missing-key fail closed; `ok:true`.
- Receipt audit → all 12 committed evidence hashes verified.

### AC Verification

All four acceptance criteria are checked in the contract below.

## nd_contract
status: delivered

### evidence
Commands run:
- `python -m pytest -q`
- `python -m pip check`
- `python tools/e2e_smoke.py --output-dir /private/tmp/oj-vwzl-head-api.K2SETi --dry-port 8903 --sdk-port 8904`
- `./tools/browser_smoke.sh http://127.0.0.1:8901 ...`
- `./tools/build_e2e_receipts.py --evidence-dir docs/evidence/OJ-vwzl-upload-to-output --source-commit 95a8bc7a7d309be79bedc1abf16bb566a234b7e9`
- Commit SHA: dc2cd41256db0e030d20df013d35c0c9e39f4f4c

Summary: Complete rights-gated upload-to-output dry-run path, browser evidence, downloadable restored-audio/review artifacts, and fail-closed SDK proof.

### proof
- [x] AC #1: complete hosted dry-run path and downloadable outputs
- [x] AC #2: missing/invalid rights rejected before execution
- [x] AC #3: clean tests and smoke pass
- [x] AC #4: SHA-256 and ffprobe receipts complete

### Proof
| AC | Status | Evidence |
|---|---|---|
| AC #1 | PASS | API `complete`; generated/final/side-by-side HTTP 200; browser job complete |
| AC #2 | PASS | missing and invalid rights both HTTP 422 before job creation |
| AC #3 | PASS | 19 tests, clean pip check, API and browser E2E |
| AC #4 | PASS | `RECEIPTS.json` records 12 hashes and media probes |

## Implementation Evidence

- Changed implementation: `app/main.py`, `app/web/index.html`, `src/openjutsu/config.py`.
- Tests, fixtures, and reproducible drivers: `tests/fixtures/`, `tests/test_app_e2e.py`, `tests/test_config.py`, `tools/e2e_smoke.py`, `tools/browser_smoke.sh`, `tools/build_e2e_receipts.py`.
- Public evidence: `docs/evidence/OJ-vwzl-upload-to-output/`.

### CI/Test Results

- `python -m pytest -q` at final clean HEAD → `19 passed, 1 warning in 5.60s`.
- `python -m pip check` at final clean HEAD → `No broken requirements found`.
- Final clean API E2E → dry-run complete; generated/final/side-by-side HTTP 200; SDK missing-key fail closed; `ok:true`.
- Receipt audit → all 12 committed evidence hashes verified.

## nd_contract
status: delivered

### evidence
Commands run:
- `python -m pytest -q`
- `python -m pip check`
- `python tools/e2e_smoke.py --output-dir /private/tmp/oj-vwzl-head-api.K2SETi --dry-port 8903 --sdk-port 8904`
- `./tools/browser_smoke.sh http://127.0.0.1:8901 ...`
- `./tools/build_e2e_receipts.py --evidence-dir docs/evidence/OJ-vwzl-upload-to-output --source-commit 95a8bc7a7d309be79bedc1abf16bb566a234b7e9`
- Commit SHA: dc2cd41256db0e030d20df013d35c0c9e39f4f4c

Summary: Complete rights-gated upload-to-output dry-run path, browser evidence, downloadable restored-audio/review artifacts, and fail-closed SDK proof.

### proof
- [x] AC #1: complete hosted dry-run path and downloadable outputs
- [x] AC #2: missing/invalid rights rejected before execution
- [x] AC #3: clean tests and smoke pass
- [x] AC #4: SHA-256 and ffprobe receipts complete

### Proof
| AC | Status | Evidence |
|---|---|---|
| AC #1 | PASS | API `complete`; generated/final/side-by-side HTTP 200; browser job complete |
| AC #2 | PASS | missing and invalid rights both HTTP 422 before job creation |
| AC #3 | PASS | 19 tests, clean pip check, API and browser E2E |
| AC #4 | PASS | `RECEIPTS.json` records 12 hashes and media probes |

## Implementation Evidence

- Deterministic backend and routing: `app/main.py`, `src/openjutsu/config.py`.
- Browser output links and optional-upload handling: `app/main.py`, `app/web/index.html`.
- Synthetic owned fixtures and tests: `tests/fixtures/`, `tests/test_app_e2e.py`, `tests/test_config.py`.
- Reproducible API/browser/receipt drivers: `tools/e2e_smoke.py`, `tools/browser_smoke.sh`, `tools/build_e2e_receipts.py`.
- Public evidence pack: `docs/evidence/OJ-vwzl-upload-to-output/`.
- Clean-checkout API job `8091736d2cc3` reached `complete`; generated/final/side-by-side artifact downloads all returned HTTP 200.
- Clean-checkout browser job `06e10c33b91b` reached `complete`; the full-page screenshot shows all three download links.
- Official SDK job `ae102cf4381d` failed closed with `missing_comfy_api_key`; missing and invalid rights attestations returned HTTP 422 before execution.

## CI/Test Results

- Final clean HEAD `dc2cd41256db0e030d20df013d35c0c9e39f4f4c`: `19 passed, 1 warning in 5.60s`.
- Final clean HEAD dependency check: `No broken requirements found`.
- Final clean HEAD API smoke: dry-run complete, three artifact downloads HTTP 200, SDK fail-closed error, driver returned `{"ok": true}`.
- Final clean HEAD receipt audit: verified all 12 committed evidence hashes.
- Credential-shaped scan across changed app/test/tool/evidence paths: 0 matches.

## nd_contract
status: delivered

### evidence

Commands run:
- `git worktree add --detach /private/tmp/oj-vwzl-clean.07Cksk dc2cd41256db0e030d20df013d35c0c9e39f4f4c`
- `python -m pytest -q`
- `python -m pip check`
- `python tools/e2e_smoke.py --output-dir /private/tmp/oj-vwzl-head-api.K2SETi --dry-port 8903 --sdk-port 8904`
- `./tools/browser_smoke.sh http://127.0.0.1:8901 ...`
- `shasum -a 256 ...` and ffprobe records via `docs/evidence/OJ-vwzl-upload-to-output/RECEIPTS.json`
- `pvg story verify-delivery OJ-vwzl`

Summary: Complete credential-free upload → preflight → rights gate → preparation → dry-run backend routing/status → downloads → restored-audio final → source/final review artifacts path, plus real-browser evidence and fail-closed SDK proof.

Commit SHA: `dc2cd41256db0e030d20df013d35c0c9e39f4f4c`

### proof
- [x] AC #1: The full hosted dry-run path returns downloadable final and review media artifacts.
- [x] AC #2: Missing and invalid rights attestations are rejected with HTTP 422 before execution.
- [x] AC #3: Final clean-checkout tests and smoke output pass.
- [x] AC #4: Every recorded evidence artifact has a SHA-256 receipt; media/image artifacts have ffprobe records.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


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
- 2026-10-17T20:32:50Z status: in_progress -> open
- 2026-10-17T20:32:50Z released by speed
- 2026-10-17T20:33:02Z status: open -> in_progress
- 2026-10-17T20:33:02Z auto-follows: linked to predecessor OJ-fgc3
- 2026-10-17T20:33:02Z claimed by dev-OJ-vwzl

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-2t3g]], [[OJ-mbn5]]
- Was blocked by: [[OJ-i6n6]]
- Follows: [[OJ-i6n6]], [[OJ-ef2q]], [[OJ-fgc3]]

## Comments

### 2026-10-17T20:32:50Z speed
EXPECTED: the delivered E2E path must remain compatible with the accepted public release-candidate gates on current main 91407a9. DELIVERED: deterministic dry_run backend, strict backend registry, rights rejection, SDK fail-closed, API/browser upload-to-output evidence, 19 passing branch tests, pip check, and 12/12 evidence hashes verified. GAP: the branch is based on pre-FGC3 7223c99. Its committed OJ-vwzl evidence and receipt generator expose absolute local paths (/Users/speed and /private/tmp), and the old workflow evidence retains cached private-reference data. Running the accepted tools/audit_release.py against this branch fails; merging it unchanged would regress the accepted public release audit. FIX: merge current main 91407a9 into story/OJ-vwzl, preserve both FGC3 release cleanup and VWZL E2E, sanitize or normalize all committed evidence/receipt paths, regenerate E2E artifacts/receipts on the merged tree, make the filtered public release audit pass, rerun full tests/API/browser E2E, commit, append delivery evidence, and redeliver.
