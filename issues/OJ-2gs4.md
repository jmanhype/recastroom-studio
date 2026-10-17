---
id: OJ-2gs4
title: "Bug: OJ-2t3g synthetic test literals fail public release audit"
status: in_progress
priority: 0
type: task
labels: [release-audit, regression]
parent: OJ-fnna
created_at: 2026-10-17T21:36:40Z
created_by: speed
updated_at: 2026-10-17T21:45:18Z
content_hash: "sha256:6aadd05f7a7d1ab9c1096e8886639eac49b592513cbfaec1aa082d7d47e5a161"
blocks: [OJ-mbn5]
assignee: dev-OJ-2gs4
follows: [OJ-mbn5, OJ-2t3g]
---

## Description
## Context

The accepted final gate `OJ-mbn5` correctly returns `eligible_to_submit=false`. Its deterministic public release audit fails on two synthetic literals in `tests/test_local_trial.py`:

- one literal absolute user path;
- one credential-like string used to test the scanner.

These are not known real secrets, but they make the otherwise rights-clean public package fail the final release audit and therefore block contest publication.

## Root Cause (known)

The local-trial tests encode scanner fixtures as literal strings that the stricter public release audit treats as forbidden content.

## Affected Components

- `tests/test_local_trial.py`
- `scripts/local_trial.py` (only if fixture construction must move into a safe helper)
- fresh release/final-gate evidence under `docs/evidence/`

## USER INTENT

The owner must be able to build the final public package without false-positive private-path or credential-looking literals while retaining real negative-path scanner tests.

## OUT OF SCOPE

- Publishing, posting, Typeform submission, cloud/GPU work, or credentials; owner-gated or forbidden here.
- Changing final-gate semantics or contest requirements; this bug only repairs audit-blocking fixtures and regenerates evidence.
- The separately disclosed Starlette/httpx deprecation warning; it does not cause this release-audit failure.

## DIFF BUDGET

~3 files, under 120 changed LOC.

## Interface Contract

The fix consumes the existing scanner function `scan_exposure(paths: list[Path]) -> list[dict]` from `scripts/local_trial.py`. The repaired test must still prove that scanner findings are produced for unsafe constructed fixture bytes, without storing a literal absolute user path or credential-like release-audit match in source.

## Acceptance evidence

1. The filtered public package release audit reports zero findings, including no absolute-user-path or credential-like synthetic literals.
2. Local-trial scanner negative behavior remains covered by real constructed fixtures and continues to produce findings without forbidden-looking source literals.
3. The loopback trial and final submission gate run into fresh evidence directories; the final gate no longer reports the OJ-2t3g release-audit local FAIL.
4. Owner-gated items may remain OWNER_BLOCKED, but no local FAIL remains and no credential/private path is added to source, logs, or evidence.

## Observable outcome

The fixed final gate returns an audited public package with zero local release-audit findings and records fresh evidence for the loopback trial and final gate.

## Testing Requirements

- Unit: prove constructed negative fixtures still trigger scanner findings without forbidden-looking source literals.
- Integration: MANDATORY (no mocks)—run `scripts/local_trial.py` against loopback with isolated output and verify receipt/status.
- Release: run `tools/final_submission_gate.py` on the explicit fixed commit with the known demo candidate and verify the local release audit passes.
- Commands: full pytest, pip check, `pvg verify`, `git diff --check`, loopback trial, final gate, and credential/private-path scan.

## MANDATORY SKILLS

None identified.

## Delivery Requirements

- Paste exact commands and pass/fail summaries in nd evidence.
- Include an AC-by-AC verification table and final gate exit code.
- Include commit SHA and evidence paths.

## nd_contract
status: new

### evidence
- Created: 2026-10-17
- Source: OJ-mbn5 PM review and `docs/evidence/OJ-mbn5-final-gate/DISCOVERED_BUG.md`

### proof
- [ ] AC #1: Pending implementation.
- [ ] AC #2: Pending implementation.
- [ ] AC #3: Pending implementation.
- [ ] AC #4: Pending implementation.

## Acceptance Criteria


## Design


## Notes
## nd_contract
status: delivered

### evidence
- Implementation commit: `7381af42a00936305b20b74f5ded1febf5f94805` (source tree `c94b81691ab3f0aa5af319ca97d9ebaf38e0836c`).
- Evidence commit: `92b175d114a1f90a9c6b8fa2487b266306fe3082`.
- Changed `tests/test_local_trial.py` so negative fixture bytes are constructed at runtime. Target test SHA-256: `cef3da5202d539891a8fabbf7db7bc3e17c2bd9f04a6338820baec18c3f3d626`.
- Target check: `python -m pytest -q tests/test_local_trial.py` -> exit 0, `2 passed in 0.17s`; both `possible-credential-value` and `absolute-or-private-network-path` findings remain asserted.
- Full final-state test: `python -m pytest -q` -> exit 0, `31 passed, 1 warning in 9.08s` (known Starlette/httpx deprecation).
- Dependency consistency: `python -m pip check` -> exit 0, `No broken requirements found.`
- Changed-file scan: `pvg verify tests/test_local_trial.py docs/evidence/OJ-2gs4-release-audit` -> exit 0, `VERIFY: PASSED (1 files scanned, 0 issues)`.
- Whitespace: `git diff --check` and `git diff --check HEAD^ HEAD` -> exit 0, no output.
- Isolated loopback trial: `python scripts/local_trial.py --host 127.0.0.1 --port 8890 --output-dir work/OJ-2gs4-local-trial` -> exit 0; job `ecbc04d8b2fb` terminal state `complete`; dry-run backend; exposure scan `PASS`, 0 findings.
- Final gate: `python tools/final_submission_gate.py --commit HEAD --demo <approved-demo-v1> --output work/OJ-2gs4-final-gate` on commit `7381af42a00936305b20b74f5ded1febf5f94805` -> exit 2 (expected owner gate), `eligible_to_submit=false`.
- Final-gate release audit: PASS, `errors=[]`; 141 tracked files, 98 text, 43 binary, 43 probed media. Matrix: 11 PASS, 0 FAIL, 8 OWNER_BLOCKED.
- Reproducible package: filtered content SHA-256 `51c213437a2669ea58b7dffcd18f5513fd72cfe357f14eb549a44f773ef3b284`; archive SHA-256 `3faede7ccf6a7de02c15c62b126ffaf6d92d079ec564d62465a225a1aa351217`, 83398293 bytes.
- Gate-embedded checks: pytest exit 0 (`31 passed, 1 warning in 9.24s`); pip check exit 0 (`No broken requirements found.`).
- Credential/private-path regex scan over target test plus six-file evidence set -> exit 0, `files_scanned=6`, `matches=[]`, status PASS.
- Committed machine-readable evidence: `docs/evidence/OJ-2gs4-release-audit/validation.json`, `docs/evidence/OJ-2gs4-release-audit/final-gate/gate.json`, `docs/evidence/OJ-2gs4-release-audit/local-trial/receipt.json`, and `docs/evidence/OJ-2gs4-release-audit/local-trial/secret-scan.json`.
- Boundary: no publish, push, merge, credential use, cloud/GPU operation, or final-gate semantic change.

### proof
- [x] AC #1: Filtered public release audit reports zero findings on commit `7381af42a00936305b20b74f5ded1febf5f94805`.
- [x] AC #2: Constructed unsafe fixtures still produce both scanner findings; targeted test passes without forbidden-looking complete literals in source.
- [x] AC #3: Fresh isolated loopback trial completed and final gate ran on the explicit fixed commit; release-audit local FAIL is gone.
- [x] AC #4: No local FAIL or OWNER_BLOCKED status changed; exit 2 is solely the unchanged owner-gated matrix. Evidence contains no forbidden-looking credential match or local-user-path match.


## History
- 2026-10-17T21:36:41Z dep_added: blocks OJ-mbn5
- 2026-10-17T21:36:58Z status: open -> in_progress
- 2026-10-17T21:36:58Z auto-follows: linked to predecessor OJ-mbn5
- 2026-10-17T21:36:58Z claimed by dev-OJ-2gs4
- 2026-10-17T21:45:18Z status: in_progress -> in_progress
- 2026-10-17T21:45:18Z auto-follows: linked to predecessor OJ-2t3g

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-mbn5]]
- Follows: [[OJ-mbn5]], [[OJ-2t3g]]

## Comments
