---
id: OJ-vwzl
title: "Complete hosted upload-to-output execution"
status: open
priority: 1
type: feature
labels: [contest, app, e2e]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T16:26:04Z
content_hash: "sha256:9e4afa4e2822ba2b0b6deb8d8af1ff3474be1d9969562a0fe8438fc500544ab6"
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


## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[OJ-fnna]]

## Comments
