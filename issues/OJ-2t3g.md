---
id: OJ-2t3g
title: "Stand up the reviewer trial deployment"
status: open
priority: 2
type: feature
labels: [contest, deployment, hosting]
parent: OJ-fnna
created_at: 2026-10-17T16:26:05Z
created_by: speed
updated_at: 2026-10-17T16:26:05Z
content_hash: "sha256:22b8f22737100bc186e88a2df15a5a0c5e4b42a10163003296c807ac252fc248"
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


## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[OJ-fnna]]

## Comments
