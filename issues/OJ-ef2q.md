---
id: OJ-ef2q
title: "Package the eleven-workflow rights-clean QC evidence set"
status: in_progress
priority: 1
type: feature
labels: [contest, qc, rights, evidence]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T16:42:58Z
content_hash: "sha256:4554a2751c687aae2cff9c85eaf180fe853dbdfb76bd4383cd74c69cf2c15375"
blocks: [OJ-fgc3, OJ-mbn5]
assignee: dev-OJ-ef2q
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


## Observable outcome
The story returns pass/fail evidence and stores every artifact referenced by its proof block.

## MANDATORY SKILLS
None identified.


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

## MANDATORY SKILLS
None identified.


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
## nd_contract
status: delivered

### evidence
- Commit on `story/OJ-ef2q` (no push): `d4299eae5275571e83925a5cd41ae0674902d2fa`.
- Imported 44 approved keeper artifacts (11 finals, 11 compares, 11 contacts, 11 Qwen reports) plus 4 provenance receipts under `docs/evidence/slate/`.
- Machine manifest: `docs/evidence/slate/manifest.json`; verifier: `tools/verify_keeper_evidence.py`.
- Immutable verifier result: `PASS`, `keeper_count=11`, `artifact_count=48`, manifest SHA-256 `5e3220dbce12bab2f792975abc96359e389b6af2a0b731731d6e6ede34f780cf`.
- Controlled mutation proof: `docs/evidence/slate-verification.md`; temporary copy changed `cameramove_jay_stretch_qwen.md` byte `[-2] XOR 0x01`, original SHA-256 `853edbf8b0a37fa46e7aec03bdc6302fdee5791189cfcef2a4482159288c6882`, mutated SHA-256 `2df22b65b3ae39a29b6f011fdaca263428bcc0afb9cf66923e93f6afdde9f5e8`, and verification failed on `sha256 changed`.
- Rights/privacy scan found 0 private/unconsented entries among all 48 manifest entries and no private film/TV, credential, URL, or absolute user-path markers in the staged textual evidence.
- Scoped tests: `/opt/homebrew/bin/pytest tests/test_evidence.py -q` → `3 passed in 3.16s`.
- Full tests: `/opt/homebrew/bin/pytest -q` → `10 passed in 3.16s`.
- Documentation: `docs/KEEPER_EVIDENCE.md`; importer: `tools/build_keeper_evidence.py`; mutation self-test: `tools/selftest_keeper_evidence.py`.

### proof
- [x] AC #1: Exactly 11 intended keepers and their nine format-concept labels are enumerated; rejected anime variant is excluded.
- [x] AC #2: Every one of 48 imported entries has rights provenance, recorded operator/Jay consent, byte size, and SHA-256; all finals/compares/contacts have media probes.
- [x] AC #3: Manifest verification passes on the immutable pack and fails after a controlled one-byte mutation in a temporary copy.
- [x] AC #4: Each keeper traces to its included Qwen report and final all-11 human approval receipt.

## History
- 2026-10-17T16:26:05Z dep_added: blocks OJ-fgc3
- 2026-10-17T16:27:21Z dep_added: blocks OJ-mbn5
- 2026-10-17T16:31:40Z status: open -> in_progress
- 2026-10-17T16:31:40Z claimed by dev-OJ-ef2q
- 2026-10-17T16:42:58Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-fnna]]
- Blocks: [[OJ-fgc3]], [[OJ-mbn5]]

## Comments
