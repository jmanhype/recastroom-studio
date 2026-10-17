---
id: OJ-fgc3
title: "Prepare the public repository release candidate"
status: in_progress
priority: 1
type: feature
labels: [contest, release, packaging]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T18:55:23Z
content_hash: "sha256:eec1c1b89614e6e6bb36f55170cf0ce8839e8490ddcfe6f0536c79cd5bd0eeb9"
blocks: [OJ-mbn5]
was_blocked_by: [OJ-ef2q]
follows: [OJ-ef2q, OJ-i6n6]
assignee: dev-OJ-fgc3
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


## Observable outcome
The story returns pass/fail evidence and stores every artifact referenced by its proof block.

## MANDATORY SKILLS
None identified.


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

## MANDATORY SKILLS
None identified.


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
- 2026-10-17T16:26:05Z dep_added: blocks OJ-mbn5
- 2026-10-17T16:56:45Z dep_removed: was_blocked_by OJ-ef2q
- 2026-10-17T16:57:59Z status: open -> in_progress
- 2026-10-17T16:57:59Z auto-follows: linked to predecessor OJ-ef2q
- 2026-10-17T16:57:59Z claimed by dev-OJ-fgc3
- 2026-10-17T18:52:56Z status: in_progress -> open
- 2026-10-17T18:52:56Z released by speed
- 2026-10-17T18:55:23Z status: open -> in_progress
- 2026-10-17T18:55:23Z auto-follows: linked to predecessor OJ-i6n6
- 2026-10-17T18:55:23Z claimed by dev-OJ-fgc3

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-mbn5]]
- Was blocked by: [[OJ-ef2q]]
- Follows: [[OJ-ef2q]], [[OJ-i6n6]]

## Comments

### 2026-10-17T18:55:21Z speed
Recovery incident: the first OJ-fgc3 worker disappeared with a large staged, uncommitted worktree. pvg loop recover removed that worktree/branch. Before any Git cleanup, all 77 staged blobs were preserved on local branch recovery/OJ-fgc3-staged-blobs at commit c251db9b2962cfa8b322cfcd33763196e693688b (tree ad6ac72f1681ed5359071d097e867fb52443bea3). A size/hash inventory is at ../oj-fgc3-unreachable-inventory.txt. No object garbage collection was run.
