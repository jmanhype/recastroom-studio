---
id: OJ-fnna
title: "Ship the Openjutsu contest production lane"
status: closed
priority: 0
type: epic
labels: [contest, openjutsu, accepted]
created_at: 2026-10-17T16:25:53Z
created_by: speed
updated_at: 2026-10-17T22:44:01Z
content_hash: "sha256:d0d68252a18f15494c6953f3dcf0f792cb0ae6e871a8de69e7609b8806d15bdc"
closed_at: 2026-10-17T22:27:51Z
close_reason: "All stories accepted"
---

## Description

## Goal

Finish the rights-clean Openjutsu Studio submission with independently verifiable
execution, packaging, deployment, demo, and compliance evidence.

## Global out-of-scope

- No worker publishes the repository, posts socially, or submits the Typeform.
- No worker handles credentials or spends GPU/compute units.
- Those actions remain owner-gated after the evidence gate passes.

## nd_contract
status: new

### evidence
- Initialized from `docs/CONTEST.md`, `docs/SUBMISSION_CHECKLIST.md`, and `STATUS.md`.
- Baseline repository commit: `d9ff276` (`Openjutsu Studio v0.1.1`).

### proof
- [ ] AC #1: All six child stories are closed with command output, artifact paths, and hashes where applicable.
- [ ] AC #2: The final gate proves the public package uses only rights-clean material and passes the contest checklist without publishing.


## Acceptance Criteria


## Design


## Notes
# Retrospective: OJ-fnna - Ship the Openjutsu contest production lane

## Source Stories
- OJ-ef2q — accepted; no labeled `LEARNINGS:`; raw implementation/AC evidence used.
- OJ-i6n6 — accepted; no labeled `LEARNINGS:`; raw delivery, rework, rejection comment, and evidence used.
- OJ-fgc3 — accepted; no labeled `LEARNINGS:`; raw delivery, recovery comment, and evidence used.
- OJ-vwzl — accepted; raw `LEARNINGS:` and `OBSERVATIONS (unrelated): None` used.
- OJ-2t3g — accepted; raw `LEARNINGS:` and `DISCOVERED_BUG` used.
- OJ-b71t — accepted/superseded; raw story body and history used; no developer delivery.
- OJ-mbn5 — accepted; no labeled `LEARNINGS:`; raw capstone evidence, rejection, corrected acceptance, and `DISCOVERED_BUG` used.
- OJ-2gs4 — post-capstone remediation, accepted; no labeled `LEARNINGS:`; raw implementation/evidence/PM review used.
- OJ-v983 — post-capstone remediation, accepted; no labeled `LEARNINGS:`; raw implementation/evidence/PM differential review used.
- OJ-fnna anchor — raw `REVIEW_RESULT: GAPS_FOUND` and recheck `REVIEW_RESULT: VALIDATED` used.

## Raw Learning Extraction
- Labeled `LEARNINGS:` present: OJ-2t3g and OJ-vwzl.
- Explicit `OBSERVATIONS` present: OJ-vwzl only; it records `None`.
- Missing required `LEARNINGS:`: OJ-ef2q, OJ-i6n6, OJ-fgc3, OJ-b71t, OJ-2gs4, OJ-v983, and OJ-mbn5. This is a process defect; their insights below were reconstructed only from raw delivery/AC/comment evidence and current code/test state, not from a prior summary.
- OJ-b71t was superseded by OJ-2gs4 and has no developer-delivery learning section.

## Learnings (Actionable)
1. Rerun accepted cross-story release gates after every merge (Action: integration AC must include merged-main release audit, full tests, API/browser E2E, keeper verification, scans, and regenerated receipts; Applies to: integration/release stories). Source: OJ-vwzl rejection/redelivery and OJ-fgc3.
2. Make evidence public-safe as it is generated (Action: expose artifact names, redact paths in generation code, scan generated receipts/screenshots, regenerate after changes; Applies to: app/E2E/release evidence). Source: OJ-vwzl LEARNINGS and OJ-2t3g.
3. Construct scanner negative fixtures at runtime (Action: forbid complete absolute-path/credential-like literals in source while asserting both real findings; Applies to: security/release tests). Source: OJ-mbn5 DISCOVERED_BUG and OJ-2gs4.
4. Preserve explicit FAIL versus OWNER_BLOCKED boundaries (Action: use a tri-state matrix and never fabricate credentials, URLs, rights, live SDK, or deployment evidence; Applies to: final gates and external integrations). Source: OJ-i6n6, OJ-mbn5, and the epic boundary.
5. Bind media claims to tamper-evident rights packs (Action: exact keeper enumeration plus provenance/consent/QC/human verdict/probe/hash and controlled mutation failure; Applies to: public media evidence). Source: OJ-ef2q.
6. Preserve staged work before Git recovery and prove stream identity (Action: snapshot all staged blobs, hash inventory, match packet hashes before remux recovery, reject regressing source; Applies to: incident recovery). Source: OJ-fgc3.
7. Prove verifier refactors differentially (Action: preserve public signatures/exceptions, compare real pack plus controlled failures, require gates; Applies to: gate/verifier maintenance). Source: OJ-v983 and anchor gap/recheck.
8. Own every warning and verify the actual backlog schema (Action: every warning is fixed or centrally owned by DISCOVERED_BUG; repeat raw query before rejection; Applies to: developer/PM delivery checks). Source: OJ-mbn5 rejection/corrected acceptance and OJ-2t3g.
9. Reuse accepted E2E infrastructure and default review deployments to loopback (Action: use accepted launcher/server semantics, bind 127.0.0.1, dry_run, and owner-gate broader exposure; Applies to: reviewer trials). Source: OJ-2t3g LEARNINGS and current local trial.
10. Require exact labeled learnings in every delivery (Action: add a deterministic delivery/PM check for nonempty `LEARNINGS:` and relevant `OBSERVATIONS:`; Applies to: story templates and acceptance). Source: raw accepted-story extraction defect.

## Rejection Patterns
- Environment-key forwarding validated but original argument passed to SDK client -> add an explicit fake-client probe for both explicit and environment credential sources before acceptance. Source: OJ-i6n6.
- Functional branch based behind accepted release cleanup -> merge accepted main and rerun public gates before acceptance. Source: OJ-vwzl.
- Warning query projection missed an existing story block -> query the actual nd fields/raw story and require central DISCOVERED_BUG ownership. Source: OJ-mbn5.
- Synthetic scanner fixture literals failed public audit -> generate fixture bytes at runtime and rerun exact pattern scan/final gate. Source: OJ-mbn5 -> OJ-b71t/OJ-2gs4.
- Concentrated verifier accumulated stages -> decompose behind stable public API and prove differential behavior. Source: anchor gap -> OJ-v983.

## Hard-TDD Effectiveness
- No child story carried a `hard-tdd` label, so this epic provides no valid hard-TDD versus normal-story rejection-rate or overhead comparison. Do not infer a scope change from this epic.

## Independent Current-State Check (2026-10-17)
- Clean worktree at `bf764110720aa29f38329562419a9f6ac4ff9b91`.
- `pvg gates app src scripts tools`: exit 0, `GATES: PASS (9 warn, 0 skipped)`.
- Full pytest: exit 0, `31 passed, 1 warning in 10.46s`; the warning is the disclosed Starlette/httpx deprecation.
- `pip check`: exit 0, `No broken requirements found.`
- Keeper verifier: exit 0, 11 keepers, 48 artifacts, manifest SHA-256 `ada599a6e327b83e3b426bece75887f2b1d3a1aa1180047bbf6edd24e8659d33`.
- Fresh loopback local trial: exit 0, dry-run job completed with loopback binding, public URL null, credential/cloud forwarding false, exposure scan PASS.
- Fresh offline final gate at HEAD: expected exit 2 only for eight owner blockers; 11 PASS / 0 FAIL / 8 OWNER_BLOCKED; `release_audit.errors=[]`; `eligible_to_submit=false`.

## Backlog Follow-Ups
- [ ] Create story: eliminate or centrally remediate the Starlette/httpx TestClient deprecation warning without suppressing test coverage. (Reason: current full suite still discloses one warning.)
- [ ] Create story: enforce a nonempty exact `LEARNINGS:` block in delivery verification. (Reason: seven accepted children lacked the contract section.)
- [ ] Update story template: release/integration AC must require merged-main gates, public-safe generated evidence, runtime-constructed negative fixtures, and differential proof for verifier/gate refactors.
- [ ] Update PM checklist: query raw accepted stories with actual nd field casing before rejecting warning ownership; distinguish FAIL from OWNER_BLOCKED.

## Vault Knowledge And UAT
- Pattern notes created under `.vault/knowledge/patterns/`: Rerun Cross-Story Release Gates After Merges; Create Public-Safe Evidence At Generation Time; Use Tamper-Evident Rights Evidence Packs; Reuse Accepted E2E Infrastructure With Loopback Defaults.
- Debug notes created under `.vault/knowledge/debug/`: Build Negative Scanner Fixtures Without Forbidden Literals; Recover Staged Media By Stream Hash Before Cleanup; Own Every Warning And Verify Backlog Queries.
- Convention notes created under `.vault/knowledge/conventions/`: Keep External Actions Owner-Blocked; Prove Refactors With Differential Gate Evidence; Require Labeled LEARNINGS In Every Delivery.
- Mandatory UAT: `.vault/knowledge/uat/UAT OJ-fnna.md`.

## Boundary
Knowledge capture only. This retro changed epic notes/project vault knowledge, not story statuses, source code, public state, credentials, cloud/GPU state, or publication/submission state.

## ANCHOR REVIEW (MILESTONE_REVIEW RECHECK)
REVIEW_RESULT: VALIDATED

### Gaps
- None. Both prior milestone-review gaps are resolved.

### Recheck Evidence
- Reviewed clean `main` at `bf764110720aa29f38329562419a9f6ac4ff9b91`; implementation `80821d7` is an ancestor and no tracked working-tree changes were present.
- Prior dangling-reference gap resolved: capstone `OJ-mbn5` historical blockers resolve to eight closed/accepted children (`OJ-ef2q`, `OJ-i6n6`, `OJ-fgc3`, `OJ-vwzl`, `OJ-2t3g`, `OJ-b71t`, `OJ-2gs4`, `OJ-v983`). `OJ-b71t` specifically resolves as closed with `release-audit,regression,superseded,accepted`. `pvg nd dep cycles` found no cycles and `pvg nd stale --days=14` found no stale issues.
- Prior quality-gate gap resolved: `pvg gates app src scripts tools` exited 0 with `GATES: PASS (9 warn, 0 skipped)`; `verify_manifest` is now CCN 26 and no BLOCK finding remains. Accepted `OJ-v983` records `evidence.py` at 303 non-blank lines and `manifest_verifier.py` at 174.
- Type/refactor spot check: `pvg verify src/openjutsu/evidence.py src/openjutsu/manifest_verifier.py docs/evidence/OJ-v983-quality-gate` exited 0 with 2 files/0 issues; AST scan found 3 public functions in `evidence.py` and 0 signature gaps. Real keeper verification passed with 11 keepers, 48 artifacts, manifest SHA-256 `ada599a6e327b83e3b426bece75887f2b1d3a1aa1180047bbf6edd24e8659d33`.
- E2E existence: `pvg verify --check-e2e` exited 0 and found `tests/test_app_e2e.py` plus `tools/build_e2e_receipts.py`. Independent full pytest exited 0 with `31 passed, 1 warning in 9.38s` (disclosed Starlette/httpx deprecation); independent `pip check` exited 0.
- Fresh offline final gate at HEAD: `tools/final_submission_gate.py --commit HEAD --demo ../openjutsu_planb/demo_v1/openjutsu-demo-v1.mp4 --output work/anchor-oj-fnna-final-gate-bf76411` exited 2 solely for the eight intentional owner blockers. Matrix was 11 PASS / 0 FAIL / 8 OWNER_BLOCKED; `release_audit.errors=[]`; embedded pytest and pip check both exited 0. Generated gate SHA-256: `de99e6f1faa9b69f0c54d1db14afecceb4ab163a5868eff5ff446dd02c6a5b32`; public package SHA-256: `a6d49ddd1267aad1b346518cf55442e1e61ffd98ab2759f731d4ea882e0950f8`.
- Boundary preserved: review only; no story status change, code edit, commit, merge, push, publication, credential use, or cloud/GPU operation.

## ANCHOR REVIEW (MILESTONE_REVIEW)
REVIEW_RESULT: GAPS_FOUND

### Gaps
1. Boundary-reference preflight fails: capstone OJ-mbn5 retains `was_blocked_by: OJ-b71t`, but `pvg issues show OJ-b71t` and `pvg nd show OJ-b71t` both return not-found. `pvg nd search OJ-b71t` confirms the unresolved reference in `issues/OJ-mbn5.md` history/links. (Impact: milestone ordering/capstone evidence cites an issue that cannot be resolved or accepted; Fix: repair the live dependency history/link using a supported nd/pvg maintenance path—restore or replace the phantom reference with the actual OJ-2gs4 repair relationship, or remove the stale historical edge without altering accepted story statuses—then rerun cycle/reference preflight.)
2. New-module quality gate fails: `pvg gates app src scripts tools` exits 1 with `src/openjutsu/evidence.py:verify_manifest` CCN 74 (threshold 30) at line 240 and the same file at 417 non-blank lines (threshold 400). (Impact: the fail-closed evidence verifier is too concentrated for safe maintenance and violates the active production quality gate; Fix: decompose manifest/approval/keeper/artifact/path verification into focused helpers while retaining public signatures and all fail-closed tests, then require `pvg gates app src scripts tools` to pass.)

### Missing Story Types
- None identified. The epic has a capstone/final gate, real local API/browser E2E wiring, rights/security scanning, packaging, deployment-boundary documentation, and owner-gated external actions.

### Evidence Expectations
- Repair evidence must show every issue ID referenced by epic-subtree CONSUMES/blocked-by/capstone links resolving via `pvg issues show`, `pvg nd dep cycles` clean, and no stale issues.
- Repair evidence must show production quality gates passing (`pvg gates app src scripts tools`) plus the existing full suite and final gate.
- Production type coverage passed an AST scan of 37 changed Python files: 149 public functions found, 0 production signature gaps; the 18 unannotated functions are tests/helpers only.
- Owner-gated publication/live-SDK/fresh-install items are not classified as epic gaps. At integrated main 0685930, hash-verified final-gate evidence reports release audit errors=[], tests exit 0 (31 passed/1 disclosed warning), pip check exit 0, and matrix PASS=11/FAIL=0/OWNER_BLOCKED=8.
- Verified at review: epic and all seven children are closed/accepted; no dependency cycles; no stale issues; `pvg verify --check-e2e` passes with two e2e files; independent full pytest=31 passed/1 disclosed warning and pip check clean; keeper verifier=11 keepers/48 artifacts; worktree clean.

## History
- 2026-10-17T21:32:35Z status: open -> closed
- 2026-10-17T21:35:23Z status: closed -> open (reopened)
- 2026-10-17T21:51:57Z status: open -> closed
- 2026-10-17T22:05:49Z status: closed -> open (reopened)
- 2026-10-17T22:27:51Z status: open -> closed

## Links


## Comments
