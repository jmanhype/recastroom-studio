---
id: OJ-b71t
title: "Bug: OJ-2t3g synthetic test literals fail public release audit"
status: open
priority: 0
type: task
labels: [release-audit, regression]
parent: OJ-fnna
created_at: 2026-10-17T21:35:23Z
created_by: speed
updated_at: 2026-10-17T21:35:23Z
content_hash: "sha256:6b2f3ab844d01bc47fc048c3d6b6b50be48bad300721946a3ae4fee7a898a6a1"
---

## Description
## Context

The accepted final gate `OJ-mbn5` correctly reports `eligible_to_submit=false`. Its deterministic public release audit fails on two synthetic literals in `tests/test_local_trial.py`:

- one literal absolute user path;
- one credential-like string used to test the scanner.

These are not known real secrets, but they make the otherwise rights-clean public package fail the final release audit and therefore block contest publication.

## Root Cause (known)

The local-trial tests encode scanner fixtures as literal strings that the stricter public release audit treats as forbidden content.

## Affected Components

- `tests/test_local_trial.py`
- `scripts/local_trial.py` (only if fixture generation must move into test helpers)
- release-audit evidence under `docs/evidence/`
- final gate evidence under `docs/evidence/OJ-mbn5-final-gate/`

## USER INTENT

The owner must be able to build the final public package without any false-positive private-path or credential-looking literals while retaining real negative-path scanner tests.

## OUT OF SCOPE

- Publishing, posting, Typeform submission, cloud/GPU work, or credentials; owner-gated and forbidden here.
- Changing final-gate semantics or contest requirements; this bug only repairs audit-blocking test fixtures and regenerates evidence.
- The unrelated Starlette/httpx deprecation warning; it is separately disclosed and does not block this audit fix.

## DIFF BUDGET

~3 files, under 120 changed LOC.

## Boundary Map

PRODUCES:
- tests/test_local_trial.py -> scanner negative-path fixtures with no literal absolute user path and no credential-like release-audit match

CONSUMES:
- OJ-2t3g: scripts/local_trial.py -> scan_exposure(paths: list[Path]) -> list[dict]; scanner findings must still be exercised through constructed safe fixture data, not by shipping forbidden-looking literals.

## Acceptance Criteria

1. The release audit for the filtered public package reports zero findings, including no absolute-user-path or credential-like synthetic literals.
2. Existing local-trial scanner behavior remains tested with real negative-path fixtures that are constructed without releasing forbidden-looking content into source.
3. The local loopback trial and final submission gate are rerun into fresh evidence directories; the final gate no longer reports the OJ-2t3g release-audit FAIL.
4. Owner-gated items may remain OWNER_BLOCKED, but no local FAIL remains and no credential/private path is added to source, logs, or evidence.

## Testing Requirements

- Unit: tests proving negative scanner fixtures are constructed safely and still produce findings without literal forbidden strings.
- Integration: MANDATORY, no mocks—run `scripts/local_trial.py` against loopback with isolated output and verify receipt/status.
- Release: run `tools/final_submission_gate.py` on the explicit fixed commit with the known demo candidate and verify release audit passes locally.
- Commands: full pytest, pip check, `pvg verify`, `git diff --check`, loopback trial, final gate, and release/credential scan.

## Skills To Use

- None identified

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
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[OJ-fnna]]

## Comments
