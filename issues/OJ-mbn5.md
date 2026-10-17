---
id: OJ-mbn5
title: "Run the final contest submission gate"
status: closed
priority: 0
type: feature
labels: [contest, compliance, capstone, accepted]
parent: OJ-fnna
created_at: 2026-10-17T16:26:05Z
created_by: speed
updated_at: 2026-10-17T21:32:26Z
content_hash: "sha256:f814b4e4e8f69fd8a35b85e52130b854ab4cee9dc5fbccc85a563990d3b8cd4a"
was_blocked_by: [OJ-ef2q, OJ-i6n6, OJ-fgc3, OJ-vwzl, OJ-2t3g, OJ-b71t, OJ-2gs4, OJ-v983]
follows: [OJ-ef2q, OJ-i6n6, OJ-fgc3, OJ-vwzl, OJ-2t3g]
closed_at: 2026-10-17T21:32:26Z
close_reason: "Accepted: final packet is complete and correctly fail-closed"
led_to: [OJ-2gs4]
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


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-10-17.

### proof
- [x] Story closed after accepted label was applied.


## PM Accepted Evidence
ACCEPTED [2026-10-17]: Final evidence-based review passes after correcting the PM's interim backlog-query projection.

- The prior rejection asserted that no Starlette/httpx2/deprecation bug report existed. Repeating the live query with the actual uppercase pvg JSON fields found the accepted predecessor OJ-2t3g DISCOVERED_BUG block titled "Test suite emits Starlette httpx deprecation warning" (affected files tests/test_app.py, tests/test_app_e2e.py, pyproject.toml). The warning is therefore already centrally owned; the zero-warning ownership requirement is satisfied.
- Delivered commit and worktree verified at eb626d244c181e0cd406fc3b2b856a87b3030c92; gate-selected commit fb1e745 and tree 214950b00e38869adb48df45000095cd3f0772ce match evidence.
- gate.json SHA-256 aed021538b62093ecfb6fbfc82777cf47b094423ada115d248fef22ee9f208f8, local candidate archive SHA-256 aa86e002eb549b55e70094e4bd58e3059c28133109866830279e2c50f8f900b7, and demo SHA-256 7cbe824a3e7dc4ff515c23fe1672630e938e2520e9b7c3686c87fa90a4db089d all match recorded proof.
- Independent ffprobe confirmed 108.052 seconds, 1152x768 H.264 at 24 fps, AAC stereo at 48 kHz, and 24,873,113 bytes. Keeper verification passed with 11 keepers and 48 artifacts.
- All five matrix artifact hashes match fb1e745; archive exclusions are absent; security-like added-line scan is clean; scoped stub scan is clean; git diff --check passes; targeted final-gate tests pass 4/4.
- Reunpacking and auditing the exact archive reproduced only the two documented OJ-2t3g synthetic-literal release-audit failures, with the same 137/94/43 counts. The gate correctly remains exit 1, eligible_to_submit=false.
- The requirement matrix is concrete and non-fabricated: local PASS/FAIL results are evidence-backed, mandatory owner actions remain OWNER_BLOCKED, and no URL/rights/live-SDK claim is fabricated. The owner packet includes fresh-install/SDK/rights stops, publication/X/Typeform procedures, timeout and rollback handling, and the explicit do-not-submit-while-gated rule.

## nd_contract
status: accepted

### evidence
- Corrected warning-ownership query against accepted predecessor OJ-2t3g.
- Full evidence-based ladder rerun from pinned delivered worktree without code changes.

### proof
- [x] AC #1: Official/checklist requirements map to concrete PASS/FAIL/OWNER_BLOCKED rows with artifact evidence.
- [x] AC #2: Demo bytes, duration, media properties, and bounded provenance are hash-verified; exact-demo rights remain OWNER_BLOCKED.
- [x] AC #3: Package, hashes, local tests/dependencies, audit failure, exclusions, and owner-blocked public/deployment checks are correctly represented without credential exposure.
- [x] AC #4: Unpublished owner-only runbook is complete with rollback, timeout, and do-not-submit handling.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-17.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## Implementation Evidence

PROOF:

### CI/Test Results
Commands run:
  - python -m pytest -q
  - python -m pip check
  - pvg verify tools/final_submission_gate.py tests/test_final_submission_gate.py docs/FINAL_SUBMISSION_PACKET.md docs/evidence/OJ-mbn5-final-gate
  - git diff --check
  - python tools/final_submission_gate.py --commit fb1e745 --demo <approved-demo> --output work/final-gate-v2
  - python tools/selftest_keeper_evidence.py docs/evidence/slate/manifest.json --report work/keeper-selftest.txt
Summary: unit/in-process integration PASS (31 tests), pip PASS, verify PASS, deterministic archive PASS, keeper verification and tamper test PASS; submission gate FAIL-CLOSED due to documented predecessor audit regression, mandatory OWNER_BLOCKED items retained.
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
- 2026-10-17T21:30:43Z status: in_progress -> open
- 2026-10-17T21:30:43Z released by speed
- 2026-10-17T21:32:26Z status: open -> closed
- 2026-10-17T21:36:07Z dep_added: blocked_by OJ-b71t
- 2026-10-17T21:36:40Z dep_removed: was_blocked_by OJ-b71t
- 2026-10-17T21:36:41Z dep_added: blocked_by OJ-2gs4
- 2026-10-17T21:51:20Z dep_removed: was_blocked_by OJ-2gs4
- 2026-10-17T22:05:49Z dep_added: blocked_by OJ-v983
- 2026-10-17T22:27:36Z dep_removed: was_blocked_by OJ-v983

## Links
- Parent: [[OJ-fnna]]
- Was blocked by: [[OJ-ef2q]], [[OJ-i6n6]], [[OJ-fgc3]], [[OJ-vwzl]], [[OJ-2t3g]], [[OJ-b71t]], [[OJ-2gs4]], [[OJ-v983]]
- Follows: [[OJ-ef2q]], [[OJ-i6n6]], [[OJ-fgc3]], [[OJ-vwzl]], [[OJ-2t3g]]
- Led to: [[OJ-2gs4]]

## Comments

### 2026-10-17T21:30:43Z speed
## PM Decision
REJECTED [2026-10-17]:

EXPECTED: The delivery standard requires zero warnings/errors, or a DISCOVERED_BUG block owning every warning in the recorded test/build output.
DELIVERED: docs/evidence/OJ-mbn5-final-gate/gate.json records the extracted-package full-suite output as "31 passed, 1 warning" with a StarletteDeprecationWarning from fastapi.testclient.py. The delivery contains a DISCOVERED_BUG block only for the predecessor release-audit regression; a live-backlog search found no Starlette/httpx2/deprecation bug report.
GAP: The warning is acknowledged in evidence but not owned by a corresponding DISCOVERED_BUG block or eliminated, so the mandatory zero-warning/error ownership gate fails.
FIX: Either eliminate the Starlette/httpx deprecation warning and rerun the full suite with zero warnings, or add the required centralized DISCOVERED_BUG block for it (without waiving the warning), then redeliver from a new pinned commit with updated hashes. Do not change the correct FAIL/OWNER_BLOCKED submission verdict.

## nd_contract
status: rejected

### evidence
- Reviewed delivered SHA eb626d244c181e0cd406fc3b2b856a87b3030c92 and matching gate/archive/demo hashes.
- Reproduced targeted gate tests (4 passed), keeper verification, exact demo hash/probe, matrix artifact hashes, archive exclusions, and predecessor release-audit failure.
- Recorded full-suite warning at docs/evidence/OJ-mbn5-final-gate/gate.json has no matching bug block.

### proof
- [ ] Delivery evidence: every recorded warning is either eliminated or backed by a DISCOVERED_BUG block.
- [x] AC #1: requirement matrix is concrete, evidence-backed, fail-closed, and non-fabricated.
- [x] AC #2: demo duration/media/hash and bounded provenance verified; exact rights remain OWNER_BLOCKED.
- [x] AC #3: package/archive/license/setup/workflow/deployment posture verified without credential exposure; release audit FAIL is correctly retained.
- [x] AC #4: unpublished owner runbook includes publication/X/Typeform, timeout, rollback, and do-not-submit-while-gated instructions.
