---
id: OJ-ef2q
title: "Package the eleven-workflow rights-clean QC evidence set"
status: open
priority: 1
type: feature
labels: [contest, qc, rights, evidence]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T16:26:04Z
content_hash: "sha256:b2ddf83fcde350175931e066c5814b41e5555bc69e6ad6dc0dd9a375b4d61db6"
blocks: [OJ-fgc3]
---

## Description

## Context

STATUS claims eleven approved rights-clean keeper candidates and a human-approved
demonstration slate. Those receipts are not yet packaged as a contest-grade,
byte-verified evidence set inside the project.

## Required outcome

Build a public-safe evidence pack that makes the quality claim independently
inspectable without including private film/TV experiments.

## Acceptance evidence

1. Enumerate the eleven keeper candidates and their intended format concepts.
2. Import or regenerate only owned/licensed/original assets into a stable evidence directory.
3. Record source/reference consent or ownership status, workflow parameters, seed, QC result, human verdict, media probe, and SHA-256 for every asset.
4. Include one manifest that fails closed on a missing, changed, private-IP, or unconsented asset.

## nd_contract
status: new

### evidence
- Created from the Plan B update in `STATUS.md`; the eleven-keeper claim remains to be verified by this story.

### proof
- [ ] AC #1: Exactly the intended keeper set is enumerated with no private film/TV material.
- [ ] AC #2: Every included asset has rights provenance and a SHA-256 receipt.
- [ ] AC #3: Manifest verification passes, then fails after a controlled byte mutation.
- [ ] AC #4: Human approval and machine QC evidence are traceable to each keeper.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-17T16:26:05Z dep_added: blocks OJ-fgc3

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-fgc3]]

## Comments
