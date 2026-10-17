---
id: OJ-fgc3
title: "Prepare the public repository release candidate"
status: closed
priority: 1
type: feature
labels: [contest, release, packaging, delivered, accepted]
parent: OJ-fnna
created_at: 2026-10-17T16:26:04Z
created_by: speed
updated_at: 2026-10-17T20:28:19Z
content_hash: "sha256:486b36021ba336299657867e26c35bae43d1f41afd22fe86e13c1b62172199e0"
was_blocked_by: [OJ-ef2q]
follows: [OJ-ef2q, OJ-i6n6]
assignee: dev-OJ-fgc3
closed_at: 2026-10-17T20:28:18Z
close_reason: "Accepted: independently reproduced 21 passing tests, pip check, CLI 0.1.1, filtered release audit PASS, unpacked-archive app health/home 200, keeper verifier 11/48, controlled mutation failure, identical archive reproduction SHA be52c145d2035fdf7b280d230a0444c50693383cf393f132c9311e1690a1b1c3, and 11/11 identical remux video/audio packet hashes. Commit d020e40 and worktree were clean; publication remains owner-gated."
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
## nd_contract
status: delivered

### evidence
- Authoritative implementation, commands, outputs, commit/tree/archive hashes, recovery decisions, clean-checkout gates, and unpacked-archive gates are recorded in the Implementation Evidence block above.
- Commit: d020e40ef1f906d5851b0a0d8bd5812ed7cca858; archive SHA-256: be52c145d2035fdf7b280d230a0444c50693383cf393f132c9311e1690a1b1c3; published=false; tag_created=false; no push.

### proof
- [x] AC #1: Clean-checkout install, pip check, full tests, CLI version, app health/home, and workflow checks pass.
- [x] AC #2: License/header and private-artifact audits pass on the filtered public tree.
- [x] AC #3: README quickstart and API examples reproduce the local credential-free gates.
- [x] AC #4: Release archive, source tree, filtered-content tree, size, and SHA-256 receipts are recorded without publishing.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Commit SHA: d020e40ef1f906d5851b0a0d8bd5812ed7cca858 on story/OJ-fgc3; source Git tree 7e0e6e5052fc09073faecfe012b808cb48e56936; no push or tag.
- Release archive: work/release/openjutsu-studio-v0.1.1-rc.1.zip, 82039746 bytes, SHA-256 be52c145d2035fdf7b280d230a0444c50693383cf393f132c9311e1690a1b1c3; receipt work/release/openjutsu-studio-v0.1.1-rc.1.receipt.json; filtered-content digest 58909dc728e3be80fb2260100d8f00c1f28c5ca9dcfa2b426a66f5605be4f305.
- A second build of the same commit produced the identical SHA-256; cmp exited 0.
- Public-tree audit: 106 files, 69 text, 37 binaries, 37 probed media, zero errors. Development-tree audit failed only on six intentionally retained local-only paths (.paivot/4, .vault/2, and two local-only tools), which the archive excludes.
- Clean checkout d020e40: pip check reported No broken requirements found; pytest reported 21 passed, 1 warning; openjutsu --version reported 0.1.1; /api/health returned ok=true, workflow=openjutsu_h3_lipsync_local.json, workflow_exists=true, backend=legacy; / returned a 5902-byte HTML page; bundled workflow JSON parsed successfully.
- Unpacked-archive audit passed; archive pytest reported 21 passed, 1 warning; archive verifier passed with 11 keepers, 48 artifacts, manifest SHA-256 ada599a6e327b83e3b426bece75887f2b1d3a1aa1180047bbf6edd24e8659d33; archive /api/health and home checks passed.
- Keeper self-test passed the immutable pack, then failed a controlled one-byte temporary mutation with sha256 changed; the committed pack remained unchanged.
- Recovery decision: restored the clean 9,855-byte workflow, 22 stream-copy-remuxed MP4 blobs, and matching 84,970-byte manifest from recovery/OJ-fgc3-staged-blobs only after proving all 22 original/remuxed video-plus-audio packet MD5s matched. This removes cached private-reference container metadata without recompression.
- Recovery exclusions: rejected recovered src/openjutsu/comfy_sdk_runner.py and src/openjutsu/config.py versions that would regress accepted OJ-i6n6 fail-closed/base-url behavior; retained .paivot/, .vault/, and initialization tools in development while excluding them from the public archive.
- Inventory correction: line for pipeline blob prints ...a35c293..., but the preserved object/tree entry is 0bb323a7339bbc7bcc64dc12a356293cbedfb9b2; the object was recovered by its actual OID.
- No credential, GPU spend, hosted deployment call, publication, social action, tag, or push was used.

### proof
- [x] AC #1: PASS — rights/private-artifact/license/credential/absolute-path audit passes on the filtered public tree; local-only control paths are deliberately retained in development and excluded from the archive.
- [x] AC #2: PASS — reviewer quickstart and API examples are present and reproduce clean-checkout install, tests, CLI, health, home, and workflow gates.
- [x] AC #3: PASS — clean-checkout and unpacked-archive full suites, pip check, CLI version, health, home, workflow JSON, and manifest verifier all pass.
- [x] AC #4: PASS — reproducible filtered archive and commit/tree/content/size/SHA receipts are recorded without publication.
- [x] AC #5: PASS — scoped commit d020e40 exists on story/OJ-fgc3 and delivery evidence is append-only.
- [x] AC #6: PASS — pvg story deliver OJ-fgc3 and pvg story verify-delivery OJ-fgc3 are run as the final workflow transition.

## Implementation Evidence

- Commit SHA: d020e40ef1f906d5851b0a0d8bd5812ed7cca858 on story/OJ-fgc3.
- Reviewer documents: docs/QUICKSTART.md, docs/API_EXAMPLES.md, docs/RELEASE.md, README.md, CHANGELOG.md.
- Audit/archive tools: tools/audit_release.py and tools/build_release_archive.py.
- CLI/app hardening: src/openjutsu/cli.py, scripts/openjutsu.py, app/main.py, src/openjutsu/workflow.py, src/openjutsu/media.py, and src/openjutsu/evidence.py.
- Regression coverage: tests/test_app.py, tests/test_media.py, tests/test_release_tools.py, tests/test_evidence.py, and tests/test_workflow.py.
- Gate artifacts: work/oj-fgc3-release-gates/ (clean/archive commands and outputs) and work/release/ (official/reproduction receipts).
- Recovery source: local recovery/OJ-fgc3-staged-blobs at c251db9b2962cfa8b322cfcd33763196e693688b; no gc/prune was run.

### CI/Test Results

- Clean checkout: pip check No broken requirements found.
- Clean checkout: 21 passed, 1 warning.
- Clean archive: 21 passed, 1 warning.
- Evidence verifier: PASS; keeper_count=11; artifact_count=48; manifest_sha256=ada599a6e327b83e3b426bece75887f2b1d3a1aa1180047bbf6edd24e8659d33.
- Public audit: PASS: release audit.
- Archive reproduction: both SHA-256 values equal be52c145d2035fdf7b280d230a0444c50693383cf393f132c9311e1690a1b1c3.

Commands run:
- git add -A && git write-tree
- python /tmp/audit_oj_candidate.py
- python3.11 -m pytest -q
- python3.11 tools/selftest_keeper_evidence.py docs/evidence/slate/manifest.json --report /tmp/oj-fgc3-selftest.txt
- git diff --cached --check
- git commit -m 'Prepare public release candidate'
- clean-checkout install/gate script using python3.11 -m venv, pip install '.[dev]', pip check, pytest, openjutsu --version, uvicorn health/home, and workflow JSON checks
- python3.11 tools/build_release_archive.py --commit HEAD (official and reproduction outputs)
- shasum -a 256 official.zip reproduction.zip
- cmp official.zip reproduction.zip
- unzip + tools/audit_release.py + pytest + verifier + uvicorn health/home on the unpacked archive
- pvg story deliver OJ-fgc3
- pvg story verify-delivery OJ-fgc3

Summary: Prepared the owner-gated public release candidate with deliberate recovery of stream-preserving rights-clean media, public quickstart/API/release documentation, fail-closed audits, CLI packaging, clean checkout/archive gates, and reproducible receipts; no publication, tag, credential use, GPU spend, or push occurred.

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
- 2026-10-17T19:15:12Z status: in_progress -> in_progress
- 2026-10-17T20:28:18Z status: in_progress -> closed
- 2026-10-17T20:28:18Z dep_removed: no_longer_blocks OJ-mbn5

## Links
- Parent: [[OJ-fnna]]
- Was blocked by: [[OJ-ef2q]]
- Follows: [[OJ-ef2q]], [[OJ-i6n6]]

## Comments

### 2026-10-17T18:55:21Z speed
Recovery incident: the first OJ-fgc3 worker disappeared with a large staged, uncommitted worktree. pvg loop recover removed that worktree/branch. Before any Git cleanup, all 77 staged blobs were preserved on local branch recovery/OJ-fgc3-staged-blobs at commit c251db9b2962cfa8b322cfcd33763196e693688b (tree ad6ac72f1681ed5359071d097e867fb52443bea3). A size/hash inventory is at ../oj-fgc3-unreachable-inventory.txt. No object garbage collection was run.

### 2026-10-17T19:16:12Z speed
## nd_contract
status: delivered

### evidence
- Authoritative implementation, commands, outputs, commit/tree/archive hashes, recovery decisions, clean-checkout gates, and unpacked-archive gates are recorded in the Implementation Evidence block above.
- Commit: d020e40ef1f906d5851b0a0d8bd5812ed7cca858; archive SHA-256: be52c145d2035fdf7b280d230a0444c50693383cf393f132c9311e1690a1b1c3; published=false; tag_created=false; no push.

### proof
- [x] AC #1: Clean-checkout install, pip check, full tests, CLI version, app health/home, and workflow checks pass.
- [x] AC #2: License/header and private-artifact audits pass on the filtered public tree.
- [x] AC #3: README quickstart and API examples reproduce the local credential-free gates.
- [x] AC #4: Release archive, source tree, filtered-content tree, size, and SHA-256 receipts are recorded without publishing.

### 2026-10-17T19:17:08Z speed
AC verification:
[x] AC #1: PASS — clean install, pip check, 21 tests, CLI 0.1.1, health, home, and bundled workflow pass.
[x] AC #2: PASS — filtered public rights/license/credential/absolute-path/media audit reports zero errors.
[x] AC #3: PASS — reviewer quickstart and API examples reproduce the credential-free local app gates.
[x] AC #4: PASS — reproducible archive, tree/content/size/SHA receipts, and no-publication controls are recorded.
