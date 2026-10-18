---
id: OJ-a7l6
title: "Cinematic local Openjutsu studio frontend upgrade"
status: open
priority: 1
type: epic
labels: [frontend, local]
created_at: 2026-10-18T01:53:45Z
created_by: speed
updated_at: 2026-10-18T03:51:58Z
content_hash: "sha256:d18cd6a19770f55960a8b955fc8617ba73fbfbc63323cc368f4629039e2837ee"
---

## Description

## Description
## Goal
Upgrade the existing rights-aware vanilla Openjutsu Studio interface into a cinematic, truthful, local-first production surface while preserving the accepted backend/API and generation boundary.

## USER INTENT
An authorized creator can clearly upload owned source material and performer references, understand every production stage, compare output to source, download real artifacts, and recover from local errors without fabricated progress or rights shortcuts.

## Scope
- Static frontend work under `app/web/`, including the owner-approved portrait intrinsic-preview repair in OJ-4rht.
- Owner-approved bounded local media export repairs: paired-review aspect preservation (OJ-xtk4) and source audio layout/loudness preservation (OJ-inuo).
- Local dry-run browser verification and deterministic regressions; all generated evidence stays local.
- Preserve generation/API semantics. These are post-generation export/UI defects, not generation redesign work.

## Global Out Of Scope
- No publication, social posting, remote deployment, push, credentials, GPU/compute spend, or cloud inference.
- No mandatory React migration or new runtime/package dependency.
- No backend/API/generation redesign, generation-workflow change, progress-UX redesign, remote inference, or paid API/GPU spend.
- The coarse-progress dogfood observation is intentionally out of this approved repair epic.

## nd_contract
status: new

### evidence
- Approved local frontend upgrade at main `7ab3b8c`.
- Previous contest epic is closed; baseline full suite is 31 passing tests.

### proof
- [ ] OJ-4rht rework, OJ-xtk4, OJ-inuo, and dependent capstone OJ-yf2c are delivered with local deterministic evidence; no push, GPU, paid API, or cloud inference is used.

## Acceptance Criteria


## Design


## Notes
REVIEW_RESULT: APPROVED
Independent backlog Anchor frontend_backlog_anchor approved current two-story scope after native nd recovery. pvg lint: 0 errors, 2 nonblocking credential-provisioning reviews because all API use is local dry_run with no keys. RTM extracted 0 requirements; not coverage proof. Developer OJ-4rht gate opened. Local commits/merges only; no remote configured.

## History


## Links


## Comments


## Goal
Upgrade the existing rights-aware vanilla Openjutsu Studio interface into a cinematic, truthful, local-first production surface while preserving the accepted backend/API and generation boundary.

## USER INTENT
An authorized creator can clearly upload owned source material and performer references, understand every production stage, compare output to source, download real artifacts, and recover from local errors without fabricated progress or rights shortcuts.

## Scope
- Static frontend work under `app/web/`.
- Local dry-run browser verification and deterministic regressions.
- Preserve backend/API behavior and generation semantics.

## Global Out Of Scope
- No publication, social posting, remote deployment, push, credentials, GPU/compute spend, or cloud inference.
- No mandatory React migration or new runtime/package dependency.
- No backend/API/generation redesign.

## nd_contract
status: new

### evidence
- Approved local frontend upgrade at main `7ab3b8c`.
- Previous contest epic is closed; baseline full suite is 31 passing tests.

### proof
- [ ] The two dependent child stories are delivered with local browser/screenshot evidence and deterministic test output.

## Acceptance Criteria


## Design


## Notes
REVIEW_RESULT: APPROVED
Independent backlog Anchor frontend_backlog_anchor approved current two-story scope after native nd recovery. pvg lint: 0 errors, 2 nonblocking credential-provisioning reviews because all API use is local dry_run with no keys. RTM extracted 0 requirements; not coverage proof. Developer OJ-4rht gate opened. Local commits/merges only; no remote configured.

## History


## Links


## Comments
