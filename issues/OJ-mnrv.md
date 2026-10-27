---
id: OJ-mnrv
title: "Build RecastRoom connected studio foundation"
status: open
priority: 1
type: epic
labels: [studio, foundation, local, no-spend]
created_at: 2026-10-27T03:45:27Z
created_by: speed
updated_at: 2026-10-27T04:27:25Z
content_hash: "sha256:375448a729a1b959f4b96e63ae7409ddd83256a582c975375367ad3496f88194"
---

## Description
TEMP_DESCRIPTION_PROBE

## Description
Implement the first connected studio foundation: saved projects, protected asset references, reusable versioned character bundles and inspectable prepared-job history connected to the existing prepare/review flow.

## USER INTENT
A creator can return to the same project, reuse the chosen character references, prepare a real existing-workflow job without re-uploading the identity each time, and inspect its saved configuration without hidden inference or lost context.

## Acceptance Criteria
1. All children pass independent PM review, including a real local E2E capstone.
2. Project/character/configuration records survive application restart; original inputs and accepted evidence remain byte-identical.
3. Existing no-project prepare/run/review routes remain compatible, with no generation or attestation-policy redesign.
4. No spend, credentials, remote publication or paid backend is needed to demonstrate M0. Later engine milestones remain explicitly planned.

## Out of scope
Multi-shot orchestration, generic person selection, multi-person generation, effects/camera engines, managed rendering queue and hosted paid execution belong to later architecture milestones, not permanent concept-card substitutes.

## Context and hard boundaries
Brownfield RecastRoom at main c2a18a5; current Python/FastAPI/browser app is the base, not a rewrite. Architecture: ../ntm-recastroom-superapp-architecture-20261026/SUPER_APP_BLUEPRINT.md. This epic covers M0 only; scenes, multi-person engines, effects and camera remain later milestones, not rejected scope.
No provider credentials, paid API/GPU/Colab jobs, network collection, push, public deployment, publication or X actions. Use synthetic/temp fixtures for tests; never commit private footage, actual photos, keys, generated keeper media or absolute personal paths. Preserve the pre-existing untracked docs/evidence/recastroom-hook-v6b-keeper/ directory.
Keep existing attestation behavior, C1 graph, source-audio restoration, status and comparison semantics unchanged. Do not market attestation as verified rights. Do not rename or mix C1 and the older BFS/Head0.35 pipeline. New project history is not a claim of renderer recovery, visual QC, generic casting or model inference.
Mandatory skills for execution: developer and codebase-memory; PM review uses pm_acceptor. Use pvg story claim/deliver and append nd_contract evidence; no direct vault edits. Local source commits/merges are authorized after story gates; pushes, remote publication and provider/GPU spending remain prohibited. Developer delivers, independent PM accepts. Follow current repo/global instructions, public type annotations, apply_patch and scope ownership.
Fresh root baseline: env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src .venv/bin/python -m pytest -q =>126 passed,1 existing Starlette/httpx warning; do not suppress tests/warnings or confuse historical results with a new run. Every delivery includes exact LEARNINGS: and OBSERVATIONS: sections, commands/results, artifact paths and hashes where relevant.


## Design


## Notes
Foundation children: OJ-6xh3 (store), OJ-5uq4 (connected app), OJ-wfpy (all-dependency E2E capstone). Old submission epic OJ-fglb preserved. Operator authorization now permits local source commits/merges only after story gates; no push or loop rotation is authorized.
Owner authorization 2026-10-26: build the connected studio foundation using Paivot. Local source-code commits and merges only. No pushes, publication, credentials, provider/GPU jobs or GPU/API spending. Supersedes earlier pending-commit-approval sentence. Root preflight:126 passed,1 disclosed Starlette/httpx warning. Existing old submission epic and its issues remain unchanged.
Dispatcher preflight: local-only source commits/merges explicitly authorized; foundation backlog structural repair is assigned to foundation_backlog_repair. Existing accepted architecture and full product scope preserved. Epic branch/worktree epic/OJ-mnrv/.claude/worktrees/epic-OJ-mnrv created from main c2a18a5 without switching main or touching pre-existing evidence. No developer dispatched before structural lint and independent Anchor approval. SQLite/temp filesystem/FFmpeg and root Python3.11.11 venv available. Use temporary Git transport guard for loop setup automatic remote sync; use pvg nd sync --no-push at manual sync boundaries. No source changes, no provider/GPU calls.

## nd_contract
status: new

### evidence
- Created from the operator-approved connected-studio architecture; no implementation or execution claim.

### proof
- [ ] The story's explicit acceptance criteria are independently verified before acceptance.


## History


## Links


## Comments

## Description
Implement the first connected studio foundation: saved projects, protected asset references, reusable versioned character bundles and inspectable prepared-job history connected to the existing prepare/review flow.

## USER INTENT
A creator can return to the same project, reuse the chosen character references, prepare a real existing-workflow job without re-uploading the identity each time, and inspect its saved configuration without hidden inference or lost context.

## Acceptance Criteria
1. All children pass independent PM review, including a real local E2E capstone.
2. Project/character/configuration records survive application restart; original inputs and accepted evidence remain byte-identical.
3. Existing no-project prepare/run/review routes remain compatible, with no generation or attestation-policy redesign.
4. No spend, credentials, remote publication or paid backend is needed to demonstrate M0. Later engine milestones remain explicitly planned.

## Out of scope
Multi-shot orchestration, generic person selection, multi-person generation, effects/camera engines, managed rendering queue and hosted paid execution belong to later architecture milestones, not permanent concept-card substitutes.

## Context and hard boundaries
Brownfield RecastRoom at main c2a18a5; current Python/FastAPI/browser app is the base, not a rewrite. Architecture: ../ntm-recastroom-superapp-architecture-20261026/SUPER_APP_BLUEPRINT.md. This epic covers M0 only; scenes, multi-person engines, effects and camera remain later milestones, not rejected scope.
No provider credentials, paid API/GPU/Colab jobs, network collection, push, public deployment, publication or X actions. Use synthetic/temp fixtures for tests; never commit private footage, actual photos, keys, generated keeper media or absolute personal paths. Preserve the pre-existing untracked docs/evidence/recastroom-hook-v6b-keeper/ directory.
Keep existing attestation behavior, C1 graph, source-audio restoration, status and comparison semantics unchanged. Do not market attestation as verified rights. Do not rename or mix C1 and the older BFS/Head0.35 pipeline. New project history is not a claim of renderer recovery, visual QC, generic casting or model inference.
Mandatory skills for execution: developer and codebase-memory; PM review uses pm_acceptor. Use pvg story claim/deliver and append nd_contract evidence; no direct vault edits. No source commit/merge until the operator authorizes it for this foundation. Developer delivers, independent PM accepts. Follow current repo/global instructions, public type annotations, apply_patch and scope ownership.
Fresh root baseline: env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src .venv/bin/python -m pytest -q =>126 passed,1 existing Starlette/httpx warning; do not suppress tests/warnings or confuse historical results with a new run. Every delivery includes exact LEARNINGS: and OBSERVATIONS: sections, commands/results, artifact paths and hashes where relevant.


## Acceptance Criteria


## Design


## Notes
Foundation children: OJ-6xh3 (store), OJ-5uq4 (connected app), OJ-wfpy (all-dependency E2E capstone). Old submission epic OJ-fglb preserved. Source-code commit/merge permission has been requested separately; no source work or loop rotation performed.
Owner authorization 2026-10-26: build the connected studio foundation using Paivot. Local source-code commits and merges only. No pushes, publication, credentials, provider/GPU jobs or GPU/API spending. Supersedes earlier pending-commit-approval sentence. Root preflight:126 passed,1 disclosed Starlette/httpx warning. Existing old submission epic and its issues remain unchanged.
Dispatcher preflight: local-only source commits/merges explicitly authorized; foundation backlog structural repair is assigned to foundation_backlog_repair. Existing accepted architecture and full product scope preserved. Epic branch/worktree epic/OJ-mnrv/.claude/worktrees/epic-OJ-mnrv created from main c2a18a5 without switching main or touching pre-existing evidence. No developer dispatched before structural lint and independent Anchor approval. SQLite/temp filesystem/FFmpeg and root Python3.11.11 venv available. Use temporary Git transport guard for loop setup automatic remote sync; use pvg nd sync --no-push at manual sync boundaries. No source changes, no provider/GPU calls.
## nd_contract
status: new

### evidence
- 2026-10-26 SrPM mechanical repair through pvg issues/pvg nd only; baseline pvg lint --backlog --epic OJ-mnrv --json reported 6 errors and 8 review findings.
- Repaired managed-heading duplication, exact MANDATORY SKILLS shape, typed cross-story signatures, safe asset resolution/upload-root contracts, observable outcomes, combined titles, and the operator's local-only commit authorization.

### proof
- [ ] Implementation proof remains pending for this story's substantive acceptance criteria.

## nd_contract
status: new

### evidence
- Created from the operator-approved connected-studio architecture; no implementation or execution claim.

### proof
- [ ] The story's explicit acceptance criteria are independently verified before acceptance.


## History


## Links


## Comments
