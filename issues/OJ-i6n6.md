---
id: OJ-i6n6
title: "Verify the official Comfy SDK execution path"
status: in_progress
priority: 0
type: feature
labels: [contest, backend, evidence]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T16:44:03Z
content_hash: "sha256:f39e46bd261a2d0aaafe8e303bcd5858f70ee8c6b3d12bd5e906edd08621d05f"
blocks: [OJ-vwzl, OJ-mbn5]
assignee: dev-OJ-i6n6
---

## Description

## Context

`src/openjutsu/comfy_sdk_runner.py` exists, but STATUS records that the official
Comfy Developer Platform path has not been live-smoke-tested and currently fails
closed without `COMFY_API_KEY`.

## Required outcome

Prove or explicitly block the official SDK execution path without exposing a
credential or spending compute from this story.

## Acceptance evidence

1. Record the SDK-versus-local/open-weights eligibility decision and its contest-category impact.
2. Keep and test the fail-closed behavior when the API key or deployment configuration is absent.
3. If owner-provided configuration exists, run one minimum live smoke and record workflow hash, execution identifier, output hash, and elapsed time.
4. Ensure no credential, bearer token, or secret appears in source, logs, issue notes, or artifacts.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md` and the SDK blocker recorded in `STATUS.md`.

### proof
- [ ] AC #1: SDK/Open Weights eligibility decision is documented with primary-source links.
- [ ] AC #2: Missing-key and missing-deployment tests fail closed with machine-readable errors.
- [ ] AC #3: Live smoke either records verifiable hashes and identifiers or records an explicit owner-gated blocker.
- [ ] AC #4: Secret scan of all new evidence finds zero credentials.


## Observable outcome
The story returns pass/fail evidence and stores every artifact referenced by its proof block.

## MANDATORY SKILLS
None identified.


## Context

`src/openjutsu/comfy_sdk_runner.py` exists, but STATUS records that the official
Comfy Developer Platform path has not been live-smoke-tested and currently fails
closed without `COMFY_API_KEY`.

## Required outcome

Prove or explicitly block the official SDK execution path without exposing a
credential or spending compute from this story.

## Acceptance evidence

1. Record the SDK-versus-local/open-weights eligibility decision and its contest-category impact.
2. Keep and test the fail-closed behavior when the API key or deployment configuration is absent.
3. If owner-provided configuration exists, run one minimum live smoke and record workflow hash, execution identifier, output hash, and elapsed time.
4. Ensure no credential, bearer token, or secret appears in source, logs, issue notes, or artifacts.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md` and the SDK blocker recorded in `STATUS.md`.

### proof
- [ ] AC #1: SDK/Open Weights eligibility decision is documented with primary-source links.
- [ ] AC #2: Missing-key and missing-deployment tests fail closed with machine-readable errors.
- [ ] AC #3: Live smoke either records verifiable hashes and identifiers or records an explicit owner-gated blocker.
- [ ] AC #4: Secret scan of all new evidence finds zero credentials.

## MANDATORY SKILLS
None identified.


## Context

`src/openjutsu/comfy_sdk_runner.py` exists, but STATUS records that the official
Comfy Developer Platform path has not been live-smoke-tested and currently fails
closed without `COMFY_API_KEY`.

## Required outcome

Prove or explicitly block the official SDK execution path without exposing a
credential or spending compute from this story.

## Acceptance evidence

1. Record the SDK-versus-local/open-weights eligibility decision and its contest-category impact.
2. Keep and test the fail-closed behavior when the API key or deployment configuration is absent.
3. If owner-provided configuration exists, run one minimum live smoke and record workflow hash, execution identifier, output hash, and elapsed time.
4. Ensure no credential, bearer token, or secret appears in source, logs, issue notes, or artifacts.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md` and the SDK blocker recorded in `STATUS.md`.

### proof
- [ ] AC #1: SDK/Open Weights eligibility decision is documented with primary-source links.
- [ ] AC #2: Missing-key and missing-deployment tests fail closed with machine-readable errors.
- [ ] AC #3: Live smoke either records verifiable hashes and identifiers or records an explicit owner-gated blocker.
- [ ] AC #4: Secret scan of all new evidence finds zero credentials.


## Acceptance Criteria


## Design


## Notes

## nd_contract
status: delivered

### evidence
- Commit on `story/OJ-i6n6`: `dc7454771ecb249edd624fb36739fe7a98804d5e`.
- Decision/category evidence: `docs/evidence/OJ-i6n6-comfy-sdk.md`.
- Targeted tests: `../../../.venv/bin/python -m pytest tests/test_comfy_sdk_runner.py tests/test_config.py -q` → `5 passed in 0.02s`.
- Full tests: `../../../.venv/bin/python -m pytest -q` → `10 passed in 0.02s`.
- Dependency health: `../../../.venv/bin/python -m pip check` → `No broken requirements found.`
- Secret scan over every changed file → 0 matches (`rg` exit status 1, its no-match status); command recorded in the evidence file.
- Live SDK smoke remains owner-gated: no owner deployment/key was supplied to this bounded worker; no credential read, deployment call, GPU/compute spend, or publication was performed.

### proof
- [x] AC #1: SDK/Open Weights eligibility decision is documented with primary-source links and category impact in `docs/evidence/OJ-i6n6-comfy-sdk.md`.
- [x] AC #2: Missing-key and missing-deployment tests fail closed before SDK client construction with JSON-serializable codes `missing_comfy_api_key` and `missing_comfy_base_url`.
- [x] AC #3: Live smoke records an explicit owner-gated blocker rather than fabricating hashes, identifiers, output, or elapsed time.
- [x] AC #4: Secret scan of all changed/evidence files finds zero credential matches.

## History
- 2026-10-17T16:26:04Z dep_added: blocks OJ-vwzl
- 2026-10-17T16:26:05Z dep_added: blocks OJ-mbn5
- 2026-10-17T16:30:56Z status: open -> in_progress
- 2026-10-17T16:30:56Z claimed by dev-OJ-i6n6
- 2026-10-17T16:30:57Z status: in_progress -> open
- 2026-10-17T16:31:09Z status: open -> in_progress
- 2026-10-17T16:31:10Z claimed by dev-OJ-i6n6

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-vwzl]], [[OJ-mbn5]]

## Comments

### 2026-10-17T16:30:57Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)
