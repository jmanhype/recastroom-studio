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
updated_at: 2026-10-17T16:26:04Z
content_hash: "sha256:8a477ef0374aef36fce51115c856035da9c8db7bbeb41f25a8c06b9449ab722b"
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


## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[OJ-fnna]]

## Comments
