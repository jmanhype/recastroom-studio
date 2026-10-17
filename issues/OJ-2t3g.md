---
id: OJ-2t3g
title: "Stand up the reviewer trial deployment"
status: in_progress
priority: 2
type: feature
labels: [contest, deployment, hosting]
parent: OJ-fnna
created_at: 2026-10-17T16:26:05Z
created_by: speed
updated_at: 2026-10-17T20:55:47Z
content_hash: "sha256:18cbc7dadfef4a2a5c24ea679a87b2283e8553ff56de8636f883ca7dc20d0047"
blocks: [OJ-mbn5]
was_blocked_by: [OJ-vwzl]
assignee: dev-OJ-2t3g
follows: [OJ-vwzl]
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


## History
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-vwzl
- 2026-10-17T16:26:05Z dep_added: blocks OJ-mbn5
- 2026-10-17T20:52:52Z dep_removed: was_blocked_by OJ-vwzl
- 2026-10-17T20:55:47Z status: open -> in_progress
- 2026-10-17T20:55:47Z auto-follows: linked to predecessor OJ-vwzl
- 2026-10-17T20:55:47Z claimed by dev-OJ-2t3g

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-mbn5]]
- Was blocked by: [[OJ-vwzl]]
- Follows: [[OJ-vwzl]]

## Comments
