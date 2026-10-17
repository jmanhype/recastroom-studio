---
id: OJ-i6n6
title: "Verify the official Comfy SDK execution path"
status: open
priority: 0
type: feature
labels: [contest, backend, evidence]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T16:26:46Z
content_hash: "sha256:0eab0f6ac2920cf55b8b94f5813edf09f0831f9d253ddcf38a3d530bc1a19e40"
blocks: [OJ-vwzl, OJ-mbn5]
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


## History
- 2026-10-17T16:26:04Z dep_added: blocks OJ-vwzl
- 2026-10-17T16:26:05Z dep_added: blocks OJ-mbn5

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-vwzl]], [[OJ-mbn5]]

## Comments
