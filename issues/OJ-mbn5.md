---
id: OJ-mbn5
title: "Run the final contest submission gate"
status: open
priority: 0
type: feature
labels: [contest, compliance, release-gate]
parent: OJ-fnna
created_at: 2026-10-17T16:26:05Z
created_by: speed
updated_at: 2026-10-17T16:26:05Z
content_hash: "sha256:ee9c5d2f6df17aeaebd55a0851780091f9a5c0f74930b5788d1de93cfbf103d0"
blocked_by: [OJ-i6n6, OJ-fgc3, OJ-2t3g]
---

## Description

## Context

The contest closes October 30, 2026 at 9:00 AM PT. Required materials include a
public repository, two-minute-or-shorter demo, social post, and Typeform entry.

## Required outcome

Produce one fail-closed final packet and owner checklist. Do not publish, post,
or submit from this story.

## Acceptance evidence

1. Verify every official contest requirement against the final repo, app, workflow, demo, deployment, and social draft.
2. Verify the demo duration is no longer than 120 seconds and uses only rights-clean material.
3. Verify all public links, repo/archive hashes, license, setup, workflow format, and optional deployed link.
4. Produce exact owner-run publication, X post, and Typeform instructions with rollback/timeout handling.

## nd_contract
status: new

### evidence
- Created from `docs/CONTEST.md`, `docs/SUBMISSION_CHECKLIST.md`, and `docs/DEMO_PLAN.md`.

### proof
- [ ] AC #1: Final requirement matrix marks every hard requirement pass/fail with artifact evidence.
- [ ] AC #2: Demo probe proves duration, resolution, audio, rights provenance, and SHA-256.
- [ ] AC #3: Public package and optional deployment checks pass without credential exposure.
- [ ] AC #4: Owner-only publication/submission packet is complete and explicitly unpublished.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-i6n6
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-fgc3
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-2t3g

## Links
- Parent: [[OJ-fnna]]
- Blocked by: [[OJ-i6n6]], [[OJ-fgc3]], [[OJ-2t3g]]

## Comments
