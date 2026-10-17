---
id: OJ-mbn5
title: "Run the final contest submission gate"
status: in_progress
priority: 0
type: feature
labels: [contest, compliance, capstone, delivered]
parent: OJ-fnna
created_at: 2026-10-17T16:26:05Z
created_by: speed
updated_at: 2026-10-17T21:24:54Z
content_hash: "sha256:6d157e45765699cb02e916ba7c1f598a50571d4effca191e8ae29ed3bb818245"
was_blocked_by: [OJ-ef2q, OJ-i6n6, OJ-fgc3, OJ-vwzl, OJ-2t3g]
assignee: dev-OJ-mbn5
follows: [OJ-ef2q, OJ-i6n6, OJ-fgc3, OJ-vwzl, OJ-2t3g]
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


## Observable outcome
The story returns pass/fail evidence and stores every artifact referenced by its proof block.

## MANDATORY SKILLS
None identified.


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

## MANDATORY SKILLS
None identified.


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
## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - python -m pytest -q
  - python -m pip check
  - pvg verify tools/final_submission_gate.py tests/test_final_submission_gate.py docs/FINAL_SUBMISSION_PACKET.md docs/evidence/OJ-mbn5-final-gate
  - git diff --check
  - python tools/final_submission_gate.py --commit fb1e745 --demo <approved-demo> --output work/final-gate-v2
  - python tools/selftest_keeper_evidence.py docs/evidence/slate/manifest.json --report work/keeper-selftest.txt
- Summary: unit/in-process integration PASS (31 tests), pip PASS, verify PASS, deterministic archive PASS, keeper verification and tamper test PASS; submission gate FAIL-CLOSED due to documented predecessor audit regression, mandatory OWNER_BLOCKED items retained.
- Key output: 31 passed, 1 warning; No broken requirements found.; VERIFY: PASSED (2 files scanned, 0 issues); eligible_to_submit=false.

### Commit
- Branch: story/OJ-mbn5
- SHA: eb626d244c181e0cd406fc3b2b856a87b3030c92

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|------|-------------|---------------|---------------|--------|
| 1 | Concrete tri-state matrix | tools/final_submission_gate.py | tests/test_final_submission_gate.py | PASS: matrix records release FAIL |
| 2 | Demo probe and provenance boundary | docs/evidence/OJ-mbn5-final-gate/gate.json | real ffprobe and fixture tests | PASS measured duration; rights OWNER_BLOCKED |
| 3 | Package audit/hash and local checks | docs/evidence/OJ-mbn5-final-gate/gate.json | full extracted-package pytest | PASS assessment; release audit FAIL recorded |
| 4 | Unpublished owner runbook | docs/FINAL_SUBMISSION_PACKET.md | manual evidence review | PASS |

### DISCOVERED_BUG
title: OJ-2t3g synthetic test literals fail public release audit
context: Existing audit rejects tests/test_local_trial.py absolute-user-path and credential-like negative-test literals. Reproduce by final gate against fb1e745. Dispatcher requests separate repair, no waiver.
affected_files: tests/test_local_trial.py
discovered_during: OJ-mbn5

## nd_contract
status: delivered

### evidence
- Commit: eb626d244c181e0cd406fc3b2b856a87b3030c92 on story/OJ-mbn5; clean worktree. No push, publication, submission, credentials, network, GPU or cloud operations.
- Gate-selected source commit: fb1e745 (full revision/tree in docs/evidence/OJ-mbn5-final-gate/gate.json). Final commit adds evidence and corrects packet's local archive location only; not claimed as same archive.
- python -m pytest -q: 31 passed, 1 Starlette deprecation warning in 9.27s. Extracted-package full suite also passed; output in gate.json.
- python -m pip check: No broken requirements found. Repeated in extracted package.
- pvg verify changed source/docs/evidence: VERIFY: PASSED (2 files scanned, 0 issues). git diff --check: exit 0. Credential/local-user-path scan changed source/docs/evidence: 0 matches, rg exit 1.
- Final gate exited 1, eligible_to_submit=false. Existing release audit rejects tests/test_local_trial.py synthetic absolute-user-path and credential-like literals. DISCOVERED_BUG.md records this predecessor OJ-2t3g regression; dispatcher explicitly requested separate repair, no scanner waiver.
- Public package built twice deterministically at work/final-gate-v2/public-package.zip; SHA-256 aa86e002eb549b55e70094e4bd58e3059c28133109866830279e2c50f8f900b7. This failing candidate is NOT approved for release.
- Gate evidence SHA-256 aed021538b62093ecfb6fbfc82777cf47b094423ada115d248fef22ee9f208f8.
- Actual named public demo probe: 108.052 seconds, 1152x768, 24fps H264/MP4, AAC stereo 48000Hz, 24873113 bytes; SHA-256 7cbe824a3e7dc4ff515c23fe1672630e938e2520e9b7c3686c87fa90a4db089d. No private media inspected.
- Keeper verification: 11 keepers/48 artifacts; mutation selftest rejects changed byte and preserves committed pack. Evidence: docs/evidence/OJ-mbn5-final-gate/keeper-selftest.txt.
- OWNER_BLOCKED: public repo/tag, public demo/final URL card, social post, Typeform, optional deployment, exact-demo timeline/audio rights and third-party model licenses, official live SDK smoke, fresh environment install/launch. No URLs fabricated; no risk waiver promoted to pass.

### proof
- [x] AC #1: Every official requirement has a concrete evidence citation and PASS/OWNER_BLOCKED/FAIL row in docs/evidence/OJ-mbn5-final-gate/gate.json; final submission remains ineligible.
- [x] AC #2: Actual demo duration/resolution/container/audio/hash independently measured; bounded rights-clean keeper provenance cited in demo-provenance.md. Exact-demo composition/audio clearance explicitly OWNER_BLOCKED, not fabricated.
- [x] AC #3: Public package built/hash-verified locally, audit executed and FAIL retained; keepers verified; full package tests and pip check pass. Public URLs, clean install and optional deployment remain owner-blocked, never asserted verified.
- [x] AC #4: docs/FINAL_SUBMISSION_PACKET.md provides explicit unpublished owner-only publication/X/Typeform/local-VPN runbooks, pre-publication stop, verification, timeout handling, rollback and do-not-submit rule.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-17.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Commit: eb626d244c181e0cd406fc3b2b856a87b3030c92 on story/OJ-mbn5; clean worktree. No push, publication, submission, credentials, network, GPU or cloud operations.
- Gate-selected source commit: fb1e745 (full revision/tree in docs/evidence/OJ-mbn5-final-gate/gate.json). Final commit adds evidence and corrects packet's local archive location only; not claimed as same archive.
- python -m pytest -q: 31 passed, 1 Starlette deprecation warning in 9.27s. Extracted-package full suite also passed; output in gate.json.
- python -m pip check: No broken requirements found. Repeated in extracted package.
- pvg verify changed source/docs/evidence: VERIFY: PASSED (2 files scanned, 0 issues). git diff --check: exit 0. Credential/local-user-path scan changed source/docs/evidence: 0 matches, rg exit 1.
- Final gate exited 1, eligible_to_submit=false. Existing release audit rejects tests/test_local_trial.py synthetic absolute-user-path and credential-like literals. DISCOVERED_BUG.md records this predecessor OJ-2t3g regression; dispatcher explicitly requested separate repair, no scanner waiver.
- Public package built twice deterministically at work/final-gate-v2/public-package.zip; SHA-256 aa86e002eb549b55e70094e4bd58e3059c28133109866830279e2c50f8f900b7. This failing candidate is NOT approved for release.
- Gate evidence SHA-256 aed021538b62093ecfb6fbfc82777cf47b094423ada115d248fef22ee9f208f8.
- Actual named public demo probe: 108.052 seconds, 1152x768, 24fps H264/MP4, AAC stereo 48000Hz, 24873113 bytes; SHA-256 7cbe824a3e7dc4ff515c23fe1672630e938e2520e9b7c3686c87fa90a4db089d. No private media inspected.
- Keeper verification: 11 keepers/48 artifacts; mutation selftest rejects changed byte and preserves committed pack. Evidence: docs/evidence/OJ-mbn5-final-gate/keeper-selftest.txt.
- OWNER_BLOCKED: public repo/tag, public demo/final URL card, social post, Typeform, optional deployment, exact-demo timeline/audio rights and third-party model licenses, official live SDK smoke, fresh environment install/launch. No URLs fabricated; no risk waiver promoted to pass.

### proof
- [x] AC #1: Every official requirement has a concrete evidence citation and PASS/OWNER_BLOCKED/FAIL row in docs/evidence/OJ-mbn5-final-gate/gate.json; final submission remains ineligible.
- [x] AC #2: Actual demo duration/resolution/container/audio/hash independently measured; bounded rights-clean keeper provenance cited in demo-provenance.md. Exact-demo composition/audio clearance explicitly OWNER_BLOCKED, not fabricated.
- [x] AC #3: Public package built/hash-verified locally, audit executed and FAIL retained; keepers verified; full package tests and pip check pass. Public URLs, clean install and optional deployment remain owner-blocked, never asserted verified.
- [x] AC #4: docs/FINAL_SUBMISSION_PACKET.md provides explicit unpublished owner-only publication/X/Typeform/local-VPN runbooks, pre-publication stop, verification, timeout handling, rollback and do-not-submit rule.

## History
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-i6n6
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-fgc3
- 2026-10-17T16:26:05Z dep_added: blocked_by OJ-2t3g
- 2026-10-17T16:27:21Z dep_added: blocked_by OJ-vwzl
- 2026-10-17T16:27:21Z dep_added: blocked_by OJ-ef2q
- 2026-10-17T16:56:46Z dep_removed: was_blocked_by OJ-ef2q
- 2026-10-17T18:52:21Z dep_removed: was_blocked_by OJ-i6n6
- 2026-10-17T20:28:18Z dep_removed: was_blocked_by OJ-fgc3
- 2026-10-17T20:52:52Z dep_removed: was_blocked_by OJ-vwzl
- 2026-10-17T21:14:50Z dep_removed: was_blocked_by OJ-2t3g
- 2026-10-17T21:18:45Z status: open -> in_progress
- 2026-10-17T21:18:45Z auto-follows: linked to predecessor OJ-ef2q
- 2026-10-17T21:18:45Z auto-follows: linked to predecessor OJ-i6n6
- 2026-10-17T21:18:45Z auto-follows: linked to predecessor OJ-fgc3
- 2026-10-17T21:18:45Z auto-follows: linked to predecessor OJ-vwzl
- 2026-10-17T21:18:45Z auto-follows: linked to predecessor OJ-2t3g
- 2026-10-17T21:18:45Z claimed by dev-OJ-mbn5
- 2026-10-17T21:24:32Z status: in_progress -> in_progress
- 2026-10-17T21:24:54Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-fnna]]
- Was blocked by: [[OJ-ef2q]], [[OJ-i6n6]], [[OJ-fgc3]], [[OJ-vwzl]], [[OJ-2t3g]]
- Follows: [[OJ-ef2q]], [[OJ-i6n6]], [[OJ-fgc3]], [[OJ-vwzl]], [[OJ-2t3g]]

## Comments
