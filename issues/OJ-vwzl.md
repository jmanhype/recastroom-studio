---
id: OJ-vwzl
title: "Complete hosted upload-to-output execution"
status: in_progress
priority: 1
type: feature
labels: [contest, app, e2e]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T18:55:24Z
content_hash: "sha256:6b2b7acf5a73ac03703a3679c7b168d031334ebccb39c0c5406f576b79a7d3fd"
blocks: [OJ-2t3g, OJ-mbn5]
was_blocked_by: [OJ-i6n6]
assignee: dev-OJ-vwzl
follows: [OJ-i6n6]
---

## Description

## Context

The app can prepare a job and serve workflow/prompt artifacts, while the hosted
generation-to-download loop is not yet proven end to end.

## Required outcome

A reviewer can upload owned inputs, pass the rights gate, execute a configured
backend, monitor status, download the result, and receive restored-audio review
artifacts.

## Acceptance evidence

1. Exercise upload, preflight, timing, rights attestation, queueing, status, download, audio restoration, and side-by-side output.
2. Include API and browser evidence from a clean checkout.
3. Preserve fail-closed behavior for unattested or invalid rights inputs.
4. Record commands, HTTP responses, media probes, and output hashes.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md`, the app walkthrough in `STATUS.md`, and demo v1 receipts.

### proof
- [ ] AC #1: The full hosted path returns a downloadable final media artifact.
- [ ] AC #2: The rights gate rejects missing or invalid attestation before execution.
- [ ] AC #3: Tests and clean-checkout smoke output pass.
- [ ] AC #4: Every public artifact has a SHA-256 receipt and ffprobe record.


## Observable outcome
The story returns pass/fail evidence and stores every artifact referenced by its proof block.

## MANDATORY SKILLS
None identified.


## Context

The app can prepare a job and serve workflow/prompt artifacts, while the hosted
generation-to-download loop is not yet proven end to end.

## Required outcome

A reviewer can upload owned inputs, pass the rights gate, execute a configured
backend, monitor status, download the result, and receive restored-audio review
artifacts.

## Acceptance evidence

1. Exercise upload, preflight, timing, rights attestation, queueing, status, download, audio restoration, and side-by-side output.
2. Include API and browser evidence from a clean checkout.
3. Preserve fail-closed behavior for unattested or invalid rights inputs.
4. Record commands, HTTP responses, media probes, and output hashes.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md`, the app walkthrough in `STATUS.md`, and demo v1 receipts.

### proof
- [ ] AC #1: The full hosted path returns a downloadable final media artifact.
- [ ] AC #2: The rights gate rejects missing or invalid attestation before execution.
- [ ] AC #3: Tests and clean-checkout smoke output pass.
- [ ] AC #4: Every public artifact has a SHA-256 receipt and ffprobe record.

## MANDATORY SKILLS
None identified.


## Context

The app can prepare a job and serve workflow/prompt artifacts, while the hosted
generation-to-download loop is not yet proven end to end.

## Required outcome

A reviewer can upload owned inputs, pass the rights gate, execute a configured
backend, monitor status, download the result, and receive restored-audio review
artifacts.

## Acceptance evidence

1. Exercise upload, preflight, timing, rights attestation, queueing, status, download, audio restoration, and side-by-side output.
2. Include API and browser evidence from a clean checkout.
3. Preserve fail-closed behavior for unattested or invalid rights inputs.
4. Record commands, HTTP responses, media probes, and output hashes.

## nd_contract
status: new

### evidence
- Created from `docs/ARCHITECTURE.md`, the app walkthrough in `STATUS.md`, and demo v1 receipts.

### proof
- [ ] AC #1: The full hosted path returns a downloadable final media artifact.
- [ ] AC #2: The rights gate rejects missing or invalid attestation before execution.
- [ ] AC #3: Tests and clean-checkout smoke output pass.
- [ ] AC #4: Every public artifact has a SHA-256 receipt and ffprobe record.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-17T16:26:04Z dep_added: blocked_by OJ-i6n6
- 2026-10-17T16:26:05Z dep_added: blocks OJ-2t3g
- 2026-10-17T16:27:21Z dep_added: blocks OJ-mbn5
- 2026-10-17T18:52:21Z dep_removed: was_blocked_by OJ-i6n6
- 2026-10-17T18:55:24Z status: open -> in_progress
- 2026-10-17T18:55:24Z auto-follows: linked to predecessor OJ-i6n6
- 2026-10-17T18:55:24Z claimed by dev-OJ-vwzl

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-2t3g]], [[OJ-mbn5]]
- Was blocked by: [[OJ-i6n6]]
- Follows: [[OJ-i6n6]]

## Comments
