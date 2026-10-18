---
id: OJ-tfyt
title: "Package the recorded H3 environment without paid deployment"
status: in_progress
priority: 0
type: feature
parent: OJ-a7l6
created_at: 2026-10-18T16:04:00Z
created_by: speed
updated_at: 2026-10-18T16:34:08Z
content_hash: "sha256:813de87201238c2596498960d40cd7230e429031cb0127242e7af3313098651f"
blocks: [OJ-yf2c]
assignee: dev-OJ-tfyt
follows: [OJ-c1vo, OJ-p8rd]
---

## Description
Scope: User approved unpaid pre-deployment engineering, not GPU/subscription/storage activation. Extend existing Openjutsu epic OJ-a7l6 from accepted preview98de3ff. Own deploy/comfy/**, docs/deployment/PREDEPLOY.md, NEW tests/test_deployment_manifest.py only. Preserve app/SDK/workflow/media/dependencies and all concurrent edits. No recursive delegation, credentials, paid calls, model downloads, remote uploads, commits or merges by worker.

Inputs: sibling work/comfy-package-20261018 contains validated candidate, model-resolution.json, pinned-source/, base-images.json, build-targets.json; only use safe public metadata, not account-status.json. Sibling work/frontend-evidence/comfy-deployment-20261018 has inventory/report. Pinned repo commits and seven explicit files45,687,037,691 bytes are known. Historical hashes absent; current HF metadata is not historical byte proof.

AC1: Add reproducible local deployment candidate + machine-readable asset manifest pinned to recorded core/four custom-node commits, immutable model revisions/digests and sizes. Preserve workflow hash06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21. No private account IDs/tokens/absolute private paths.
AC2: Trace pinned upstream code for implicit BiRefNet-general + support code/config and YuNet/SFace ONNX assets; record exact paths, revisions, current digests/sizes/license sources where verified. Do not pretend unknowns are resolved or guess destinations. Public metadata/source reads allowed, no weights. Explicit compatibility status must fail closed if model closure is incomplete.
AC3: Analyze recorded Python3.13.15/Torch2.11.0+cu130 vs catalog bases3.12/3.13 Torch2.12.1 CUDA13 (or3.11 Torch2.8 CUDA12.8). Document actual dependency/source-build blockers and immutable supported selection if justified. No false GPU import compatibility from manifest validation. Do not install into root .venv or modify global tools.
AC4: Add offline structural/hash/model-closure tests with no network and no skips; CLI build validate and push --dry-run only are allowed. No remote build/release/deploy. Tests/report distinguish candidate vs runnable deployment and unknown rights/model licenses.
AC5: Report exact commands/test results/hashes and remaining blockers. Manifest must note SDK asset bridge may be pending in parallel story; do not claim all build contents final if custom bridge is required. Parent independently tests and commits; PM accepts later.

## nd_contract
status: new
### evidence
- User agreed to finish unpaid packaging/SDK engineering before buying a plan.
### proof
- [ ] AC1-5 evidence-backed unpaid package, no generation claim.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T16:04:00Z dep_added: blocks OJ-yf2c
- 2026-10-18T16:06:53Z status: open -> in_progress
- 2026-10-18T16:06:53Z auto-follows: linked to predecessor OJ-c1vo
- 2026-10-18T16:06:53Z claimed by dev-OJ-tfyt
- 2026-10-18T16:34:08Z status: in_progress -> in_progress
- 2026-10-18T16:34:08Z auto-follows: linked to predecessor OJ-p8rd

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]
- Follows: [[OJ-c1vo]], [[OJ-p8rd]]

## Comments
