---
id: OJ-2t3g
title: "Stand up the reviewer trial deployment"
status: in_progress
priority: 2
type: feature
labels: [contest, deployment, hosting, delivered]
parent: OJ-fnna
created_at: 2026-10-17T16:26:05Z
created_by: speed
updated_at: 2026-10-17T21:08:53Z
content_hash: "sha256:822c67eda5cf1490fc1321cf3e7016c0580008008a208816547f6ee9a6eda8d0"
blocks: [OJ-mbn5]
was_blocked_by: [OJ-vwzl]
assignee: dev-OJ-2t3g
follows: [OJ-vwzl, OJ-fgc3]
---

## Description

## Context

A deployed app is optional but encouraged by the contest. No deployment exists yet.

## Required outcome

Provide a reviewer-safe trial deployment path that does not embed credentials or
create an open-rights bypass.

## Acceptance evidence

1. Document the hosting architecture, public URL policy, rate limits, rights gate, storage lifetime, and required environment variables.
2. Provide a repeatable deployment command or workflow.
3. Verify health, home page, prepare endpoint, rights rejection, and generation status from the deployed URL.
4. Keep all secrets in the host environment and scan artifacts/logs for exposure.

## nd_contract
status: new

### evidence
- Created from the deployment gap in `docs/CONTEST.md` and `STATUS.md`.

### proof
- [ ] AC #1: Deployment instructions run without source changes beyond configuration.
- [ ] AC #2: Live health and reviewer walkthrough probes return expected responses.
- [ ] AC #3: The hosted rights gate rejects unattested work.
- [ ] AC #4: Secret scan finds zero credentials in source, logs, and artifacts.


## Observable outcome
The story returns pass/fail evidence and stores every artifact referenced by its proof block.

## MANDATORY SKILLS
None identified.


## Context

A deployed app is optional but encouraged by the contest. No deployment exists yet.

## Required outcome

Provide a reviewer-safe trial deployment path that does not embed credentials or
create an open-rights bypass.

## Acceptance evidence

1. Document the hosting architecture, public URL policy, rate limits, rights gate, storage lifetime, and required environment variables.
2. Provide a repeatable deployment command or workflow.
3. Verify health, home page, prepare endpoint, rights rejection, and generation status from the deployed URL.
4. Keep all secrets in the host environment and scan artifacts/logs for exposure.

## nd_contract
status: new

### evidence
- Created from the deployment gap in `docs/CONTEST.md` and `STATUS.md`.

### proof
- [ ] AC #1: Deployment instructions run without source changes beyond configuration.
- [ ] AC #2: Live health and reviewer walkthrough probes return expected responses.
- [ ] AC #3: The hosted rights gate rejects unattested work.
- [ ] AC #4: Secret scan finds zero credentials in source, logs, and artifacts.

## MANDATORY SKILLS
None identified.


## Context

A deployed app is optional but encouraged by the contest. No deployment exists yet.

## Required outcome

Provide a reviewer-safe trial deployment path that does not embed credentials or
create an open-rights bypass.

## Acceptance evidence

1. Document the hosting architecture, public URL policy, rate limits, rights gate, storage lifetime, and required environment variables.
2. Provide a repeatable deployment command or workflow.
3. Verify health, home page, prepare endpoint, rights rejection, and generation status from the deployed URL.
4. Keep all secrets in the host environment and scan artifacts/logs for exposure.

## nd_contract
status: new

### evidence
- Created from the deployment gap in `docs/CONTEST.md` and `STATUS.md`.

### proof
- [ ] AC #1: Deployment instructions run without source changes beyond configuration.
- [ ] AC #2: Live health and reviewer walkthrough probes return expected responses.
- [ ] AC #3: The hosted rights gate rejects unattested work.
- [ ] AC #4: Secret scan finds zero credentials in source, logs, and artifacts.


## Acceptance Criteria


## Design


## Notes
Commit SHA: 9776ba126bd416c6d2ba4ba0c0317780d7acb433

## Implementation Evidence

### CI/Test Results
Commands run:
- `../../../.venv/bin/python scripts/local_trial.py --host 127.0.0.1 --port 8890`
- `../../../.venv/bin/python -m pip check`
- `../../../.venv/bin/python -m pytest -q`
- `git diff --check`
- `pvg verify docs/LOCAL_TRIAL_DEPLOYMENT.md scripts/local_trial.py tests/test_local_trial.py docs/evidence/OJ-2t3g-local-trial/receipt.json docs/evidence/OJ-2t3g-local-trial/secret-scan.json docs/evidence/OJ-2t3g-local-trial/server.log --format=text`

Summary: local trial PASS (`ok:true`, job `2e0c7c137ef8`, terminal `complete`); dependency check PASS (`No broken requirements found.`); full test suite PASS (`27 passed, 1 warning`); whitespace PASS; pvg verify PASS (`2 files scanned, 0 issues`). Exposure scan PASS (`158` files, zero findings). Coverage: not configured or measured.

### Commit
- Branch: `story/OJ-2t3g`
- Commit SHA: `9776ba126bd416c6d2ba4ba0c0317780d7acb433`

### AC Verification
| AC # | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Deployment architecture, no-public-default policy, VPN boundary, rate-limit posture, rights gate, storage lifetime, and environment variables documented. | `docs/LOCAL_TRIAL_DEPLOYMENT.md:1-78` | PASS |
| 2 | Repeatable loopback-only dry-run command/workflow. | `scripts/local_trial.py:205-330`; `docs/LOCAL_TRIAL_DEPLOYMENT.md:80-109` | PASS |
| 3 | Health, home, prepare, rights rejection, and generation status probes run against `http://127.0.0.1:8890`. | `docs/evidence/OJ-2t3g-local-trial/receipt.json` | PASS |
| 4 | Credential/local-path exposure scan records zero findings across 158 files. | `docs/evidence/OJ-2t3g-local-trial/secret-scan.json` | PASS |

The detailed command output, hashes, rights response, terminal status, learnings, and pre-existing test warning are in the preceding delivered evidence note.

## nd_contract
status: delivered

### evidence
- Commit SHA: `9776ba126bd416c6d2ba4ba0c0317780d7acb433` on `story/OJ-2t3g`.
- Local trial evidence: `docs/evidence/OJ-2t3g-local-trial/receipt.json` SHA-256 `b010ca4923bc3b9fee0235ec48a15c69e6ed97ae980c50f17362bb244aa66f09`.
- Exposure scan: `docs/evidence/OJ-2t3g-local-trial/secret-scan.json`, 158 files, zero findings, PASS.
- Tests/dependencies: 27 passed with one pre-existing Starlette warning; pip check found no broken requirements.

### proof
- [x] AC #1: Deployment policy, boundary, rate-limit posture, rights gate, storage lifetime, architecture, and variables are documented.
- [x] AC #2: The loopback dry-run workflow is repeatable through `scripts/local_trial.py`.
- [x] AC #3: Live health/home/prepare/rights/status probes returned the expected responses and are recorded in machine-readable evidence.
- [x] AC #4: Credential and local-path exposure scan completed with zero findings.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Deployment and probe results
- Command: `../../../.venv/bin/python scripts/local_trial.py --host 127.0.0.1 --port 8890`
- Output: `{"base_url":"http://127.0.0.1:8890","job_id":"2e0c7c137ef8","ok":true,"terminal_state":"complete",...}`; process exit code 0.
- Binding: loopback-only `127.0.0.1:8890`; backend `dry_run`; public URL `null`; credential environment forwarding false; GPU/cloud backend selection false.
- Real URL probes recorded in `docs/evidence/OJ-2t3g-local-trial/receipt.json`:
  - `GET /api/health` -> 200, `backend=dry_run`, `workflow_exists=true`.
  - `GET /` -> 200 HTML with the rights attestation control.
  - `POST /api/prepare` without rights -> 422, `Rights attestation is required.`
  - `POST /api/prepare` with rights -> 200, job `2e0c7c137ef8`, attested manifest.
  - `POST /api/jobs/2e0c7c137ef8/run` -> 200 queued; status polling reached 200 `complete` with backend `dry_run`.
- Evidence hashes:
  - `receipt.json` SHA-256 `b010ca4923bc3b9fee0235ec48a15c69e6ed97ae980c50f17362bb244aa66f09`.
  - `secret-scan.json` SHA-256 `552cf8c3f8a25a108d464c86b6b61c5c228abc7aa577957f438cbe297fcc8dc2`.
  - `server.log` SHA-256 `34248dcd8623d2565c1ab79d98de9ca2bdc27e9fbdb4d2b1b09bc3a6a2bcd6b3`.

### Exposure scan
- Command: executed by `scripts/local_trial.py` after probe/artifact generation.
- Machine-readable result: `docs/evidence/OJ-2t3g-local-trial/secret-scan.json`.
- Scope: `app`, `docs`, `scripts`, `src`, `tests/fixtures`, `tools`, `workflows`, generated trial artifacts/log.
- Result: 158 files scanned, findings `[]`, status `PASS`.
- The script fails closed if credential-shaped values, credential-like filenames, absolute user paths, private network addresses, or raw credential assignments are detected.

### CI/Test and dependency results
- Commands run:
  - `../../../.venv/bin/python -m pip check`
  - `../../../.venv/bin/python -m pytest -q`
  - `git diff --check`
  - `pvg verify docs/LOCAL_TRIAL_DEPLOYMENT.md scripts/local_trial.py tests/test_local_trial.py docs/evidence/OJ-2t3g-local-trial/receipt.json docs/evidence/OJ-2t3g-local-trial/secret-scan.json docs/evidence/OJ-2t3g-local-trial/server.log --format=text`
- Summary: dependency check PASS (`No broken requirements found.`); full suite PASS (`27 passed, 1 warning in 8.84s`); diff whitespace check PASS; `VERIFY: PASSED (2 files scanned, 0 issues)`.
- Coverage: not measured; this repository defines no coverage command or threshold. The full configured test suite was executed.
- Existing warning: `fastapi.testclient` emits `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead` in the shared venv (FastAPI 0.143.3, Starlette 1.8.0, httpx 0.28.1, no httpx2). It is unrelated to this story's files but remains visible in test output.

### Commit
- Branch: `story/OJ-2t3g`
- SHA: `9776ba126bd416c6d2ba4ba0c0317780d7acb433`
- Commit: `9776ba1 feat(OJ-2t3g): add local reviewer trial`
- Files: 6 changed, 756 insertions; no push, merge, or publication performed.

### AC Verification
| AC # | Requirement | Code/Evidence Location | Status |
|---|---|---|---|
| 1 | Architecture, no-public-default, local/VPN boundary, rate-limit posture, rights gate, storage lifetime, and environment variables documented. | `docs/LOCAL_TRIAL_DEPLOYMENT.md:1-78` | PASS |
| 2 | Repeatable loopback-only dry-run deployment/probe workflow. | `scripts/local_trial.py:205-330`, `docs/LOCAL_TRIAL_DEPLOYMENT.md:80-109`, `tests/test_local_trial.py:7-12` | PASS |
| 3 | Real local URL health/home/prepare/rights rejection/generation-status probes recorded. | `docs/evidence/OJ-2t3g-local-trial/receipt.json` (11 probe records, job `2e0c7c137ef8`) | PASS |
| 4 | Credentials stay out of source/docs/artifacts/logs and exposure scan records zero findings. | `scripts/local_trial.py:140-202`, `docs/evidence/OJ-2t3g-local-trial/secret-scan.json` | PASS |

LEARNINGS:
- Reusing the existing E2E `Server` kept backend selection, credential-variable removal, process cleanup, and dry-run semantics aligned with the already accepted upload-to-output path.
- A review-only deployment must compensate for the app's lack of auth/rate limiting with a loopback-only default and explicit owner-gated VPN requirements rather than inventing a public-hosting claim.
- The exposure scan must include the receipt itself; scanning only logs leaves the newest generated artifact unverified.

### DISCOVERED_BUG
  title: Test suite emits Starlette httpx deprecation warning
  context: Full pytest run passes 27/27 but emits one StarletteDeprecationWarning from `fastapi.testclient` because the shared venv has FastAPI 0.143.3, Starlette 1.8.0, and httpx 0.28.1 but not httpx2. This predates OJ-2t3g and is not exercised by the new local trial script.
  affected_files: `tests/test_app.py`, `tests/test_app_e2e.py`, `pyproject.toml`
  discovered_during: OJ-2t3g

## nd_contract
status: delivered

### evidence
- Local loopback dry-run probe receipt: `docs/evidence/OJ-2t3g-local-trial/receipt.json` SHA-256 `b010ca4923bc3b9fee0235ec48a15c69e6ed97ae980c50f17362bb244aa66f09`.
- Exposure scan: 158 files, zero findings, PASS.
- Full tests: 27 passed, 1 pre-existing warning; dependency check PASS.
- Commit `9776ba126bd416c6d2ba4ba0c0317780d7acb433` on `story/OJ-2t3g`.

### proof
- [x] AC #1: Reviewer deployment policy and architecture are documented with loopback/no-public defaults and explicit owner-gated VPN controls. (Docs: `docs/LOCAL_TRIAL_DEPLOYMENT.md:1-78`)
- [x] AC #2: A repeatable script starts the loopback dry-run app and records real HTTP evidence. (Code: `scripts/local_trial.py:205-330`; Evidence: `docs/evidence/OJ-2t3g-local-trial/receipt.json`)
- [x] AC #3: The hosted rights gate rejects unattested work with HTTP 422 before job creation. (Evidence: receipt `/api/prepare` probe)
- [x] AC #4: Source/docs/artifacts/log scan records 158 files, zero credential or local-path findings. (Evidence: `docs/evidence/OJ-2t3g-local-trial/secret-scan.json`)


## History
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-vwzl
- 2026-10-17T16:26:05Z dep_added: blocks OJ-mbn5
- 2026-10-17T20:52:52Z dep_removed: was_blocked_by OJ-vwzl
- 2026-10-17T20:55:47Z status: open -> in_progress
- 2026-10-17T20:55:47Z auto-follows: linked to predecessor OJ-vwzl
- 2026-10-17T20:55:47Z claimed by dev-OJ-2t3g
- 2026-10-17T21:06:44Z status: in_progress -> in_progress
- 2026-10-17T21:06:45Z auto-follows: linked to predecessor OJ-fgc3

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-mbn5]]
- Was blocked by: [[OJ-vwzl]]
- Follows: [[OJ-vwzl]], [[OJ-fgc3]]

## Comments
