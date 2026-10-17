---
id: OJ-fgc3
title: "Prepare the public repository release candidate"
status: open
priority: 1
type: feature
labels: [contest, release, packaging]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T16:26:04Z
content_hash: "sha256:5899988be4886ae4cf3cdd29eaba8ff0cacc4aa3c81aa3fff0b8e87fc3094f24"
blocked_by: [OJ-ef2q]
---

## Description

## Context

The project is at local commit `d9ff276` / v0.1.1, but the public GitHub
repository and release tag remain unpublished.

## Required outcome

Prepare a release candidate that can be published only after explicit owner
authorization.

## Acceptance evidence

1. Remove private development artifacts and audit repository contents for rights and license risks.
2. Verify clean install, all tests, CLI version, API health, home page, and workflow presence from a clean checkout.
3. Add reviewer-facing setup, API examples, screenshots, and archive/tag instructions.
4. Record the tree hash, archive hash, test output, and release notes.

## nd_contract
status: new

### evidence
- Created from `docs/SUBMISSION_CHECKLIST.md` and the v0.1.1 receipts.

### proof
- [ ] AC #1: Clean-checkout install and tests pass.
- [ ] AC #2: License/header and private-artifact audits pass.
- [ ] AC #3: README quickstart reproduces the local app from a clean checkout.
- [ ] AC #4: Release archive and tree hashes are recorded without publishing.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-ef2q

## Links
- Parent: [[OJ-fnna]]
- Blocked by: [[OJ-ef2q]]

## Comments
