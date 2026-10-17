---
id: OJ-i6n6
title: "Verify the official Comfy SDK execution path"
status: in_progress
priority: 0
type: feature
labels: [contest, backend, evidence, delivered]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T17:00:25Z
content_hash: "sha256:2a42c67f6e55299e47fb4953e78dc5241bb542aedece0db13820bdc642ba81ff"
blocks: [OJ-vwzl, OJ-mbn5]
assignee: dev-OJ-i6n6
follows: [OJ-ef2q]
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

### AC Verification
[x] AC #1: PASS — SDK/local/open-weights decision and category impact use official Comfy sources.
[x] AC #2: PASS — missing key/deployment tests fail closed before SDK client construction with JSON-serializable error codes.
[x] AC #3: PASS — explicit owner-gated live-smoke blocker is recorded instead of fabricated execution evidence.
[x] AC #4: PASS — changed-file credential scan found zero matches.

## nd_contract
status: delivered

### evidence
- Rework commit SHA: 84a0c59b90026a3c111ba0ef07dea5fc542a3df1 on story/OJ-i6n6; no push.
- PM defect fixed: ComfySdkRunner now passes resolved_api_key—not the original api_key argument—to the official Comfy client.
- Regression coverage proves explicit api_key and environment COMFY_API_KEY forwarding, while retaining both fail-closed tests.
- No credential, GPU/compute, deployment call, or publication was used.

### proof
- [x] AC #1: PASS — explicit and environment API-key forwarding are regression-tested.
- [x] AC #2: PASS — missing-key and missing-base-url fail-closed coverage still passes.
- [x] AC #3: PASS — full pytest, pip check, and credential-shaped scan pass.
- [x] AC #4: PASS — rework evidence records commands and outputs without credential exposure.

## Implementation Evidence

- Commit SHA: `84a0c59b90026a3c111ba0ef07dea5fc542a3df1` on `story/OJ-i6n6`; no push.
- Implementation: `src/openjutsu/comfy_sdk_runner.py` passes `resolved_api_key` to `Comfy`.
- Forwarding regressions: `tests/test_comfy_sdk_runner.py::test_resolved_api_key_is_forwarded_to_comfy`.
- Retained fail-closed regressions: missing API key and missing deployment URL tests.
- Evidence: `docs/evidence/OJ-i6n6-comfy-sdk.md`, “PM rework — 2026-10-17”.

### CI/Test Results

- Targeted tests: `7 passed in 0.02s`.
- Full test suite: `15 passed in 3.62s`.
- Dependency health: `No broken requirements found.`
- Credential-shaped scan over rework files: `0 matches`; ripgrep exit status `1`, its expected no-match status.

Commands run:
- `../../../.venv/bin/python -m pytest tests/test_comfy_sdk_runner.py tests/test_config.py -q`
- `../../../.venv/bin/python -m pytest -q`
- `../../../.venv/bin/python -m pip check`
- `rg -n --pcre2 -i '<credential-shaped-pattern>' docs/evidence/OJ-i6n6-comfy-sdk.md src/openjutsu/comfy_sdk_runner.py tests/test_comfy_sdk_runner.py`
- `git diff --check`
- `git commit -m 'Forward resolved Comfy SDK credentials'`
- `pvg story deliver OJ-i6n6`
- `pvg story verify-delivery OJ-i6n6`

Summary: Corrected environment/explicit credential forwarding to the official Comfy SDK client, added parameterized forwarding regressions, retained fail-closed coverage, and updated evidence without credentials, compute spend, publication, or push.

### AC Verification
[x] AC #1: PASS — resolved explicit/environment key is forwarded to Comfy.
[x] AC #2: PASS — explicit and environment forwarding paths are covered by regression tests.
[x] AC #3: PASS — missing-key and missing-base-url fail-closed tests remain passing.
[x] AC #4: PASS — full tests, pip check, credential-shaped scan, scoped commit, evidence update, and delivery transition are recorded.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-17.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Commit SHA: dc7454771ecb249edd624fb36739fe7a98804d5e on story/OJ-i6n6; no push.
- Decision/category evidence: docs/evidence/OJ-i6n6-comfy-sdk.md.
- Owner-gated live-smoke blocker is explicit; no credential, GPU/compute, deployment call, or publication was used.

### proof
- [x] AC #1: PASS — primary-source SDK/local/open-weights decision and category impact are documented.
- [x] AC #2: PASS — missing key/deployment tests fail closed before client construction with machine-readable JSON codes.
- [x] AC #3: PASS — explicit owner-gated blocker replaces an unavailable live smoke without fabricated identifiers or hashes.
- [x] AC #4: PASS — changed-file secret scan found zero matches.

## Implementation Evidence

- Commit SHA: `dc7454771ecb249edd624fb36739fe7a98804d5e` on `story/OJ-i6n6`; no push.
- Decision record: `docs/evidence/OJ-i6n6-comfy-sdk.md`.
- Fail-closed implementation: `src/openjutsu/comfy_sdk_runner.py`; configuration surface: `src/openjutsu/config.py`.
- Machine-readable fail-closed tests: `tests/test_comfy_sdk_runner.py`; configuration regression: `tests/test_config.py`.
- No owner-provided deployment/key was supplied; no credential read, live deployment request, GPU/compute spend, or publication was performed.

### CI/Test Results

- Targeted tests: `5 passed in 0.02s`.
- Full test suite: `10 passed in 0.02s`.
- Dependency health: `No broken requirements found.`
- Secret scan: 0 matches over every changed file; `rg` exit status 1 is its expected no-match status.

Commands run:
- `../../../.venv/bin/python -m pytest tests/test_comfy_sdk_runner.py tests/test_config.py -q`
- `../../../.venv/bin/python -m pytest -q`
- `../../../.venv/bin/python -m pip check`
- `rg -n --pcre2 -i '<credential-pattern>' <all changed files>` (exact command in evidence file)
- `git diff --check`
- `git commit -m 'Verify Comfy SDK fail-closed configuration'`
- `pvg story verify-delivery OJ-i6n6`
- `pvg story deliver OJ-i6n6`

Summary: Documented the official-SDK versus local/open-weights contest decision, added pre-network machine-readable missing-key/deployment failures, retained the owner-gated live-smoke blocker, and verified tests, dependencies, and secret-free scoped evidence.

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
- 2026-10-17T16:44:51Z status: in_progress -> in_progress
- 2026-10-17T16:44:57Z status: in_progress -> in_progress
- 2026-10-17T16:57:38Z status: in_progress -> open
- 2026-10-17T16:57:38Z released by speed
- 2026-10-17T16:57:58Z status: open -> in_progress
- 2026-10-17T16:57:58Z auto-follows: linked to predecessor OJ-ef2q
- 2026-10-17T16:57:58Z claimed by dev-OJ-i6n6
- 2026-10-17T17:00:25Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-vwzl]], [[OJ-mbn5]]
- Follows: [[OJ-ef2q]]

## Comments

### 2026-10-17T16:30:57Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)

### 2026-10-17T16:57:38Z speed
EXPECTED: a configured environment key is passed through to the official SDK client when api_key is omitted. DELIVERED: missing-key/missing-base-url fail-closed tests, docs, 10 passing tests, and clean secret scan at dc74547. GAP: independent probe with COMFY_API_KEY=environment-key-for-probe and api_key=None showed FakeComfy received api_key=None; runner validates resolved_api_key but constructs Comfy(api_key=api_key). FIX: pass resolved_api_key to Comfy, add a regression test proving the environment key is forwarded, rerun full tests and secret scan, commit on story/OJ-i6n6, and redeliver.
