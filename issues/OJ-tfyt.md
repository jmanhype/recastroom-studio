---
id: OJ-tfyt
title: "Package the recorded H3 environment without paid deployment"
status: in_progress
priority: 0
type: feature
parent: OJ-a7l6
created_at: 2026-10-18T16:04:00Z
created_by: speed
updated_at: 2026-10-18T16:41:10Z
content_hash: "sha256:0b9ef6214b440c917c8a4454f15108e582b47771f089b57ce32e34156fad80eb"
blocks: [OJ-yf2c]
assignee: dev-OJ-tfyt
follows: [OJ-c1vo, OJ-p8rd]
labels: [delivered]
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
CI/Test Results:
- 12 passed in 0.04s (tests/test_deployment_manifest.py).
- 75 passed, 1 pre-existing warning, 17.71s (full suite).
- Offline comfy validate exit 0; push --dry-run exit 0 with zero uploads.

Summary:
Fail-closed local candidate delivered with exact current metadata/source evidence and offline tests; runnable deployment, historical byte identity, several licenses, runtime imports, and SDK asset binding remain unresolved.
### CI/Test Results
- Scoped: 12 passed; full: 75 passed, 1 pre-existing warning.
- Offline comfy validate and push --dry-run both exit 0; dry run uploads zero bytes.

### Proof
| AC | Verified |
| --- | --- |
| AC1 | Yes: exact candidate/manifest pins and workflow hash. |
| AC2 | Yes: exact implicit source/metadata traces; unknowns fail closed. |
| AC3 | Yes: runtime matrix and dependency blockers; no base selected. |
| AC4 | Yes: offline no-skip tests and syntax-only CLI receipts. |
| AC5 | Yes: commands/results/hashes/blockers and SDK-bridge dependency reported. |
Correction: the final PREDEPLOY.md SHA-256 after removing the temporary-directory pathname is 6d205747c2dfc70d2247fb79634f6023dd4b921228afe3344e6c1be96ec0a825; this supersedes the earlier 404ecb4f8f1040e7b059d373be00b87aa3e6a13b77d6a45387632f2eeb3ffc05 hash. All other artifact hashes are unchanged.
Final artifact correction: PREDEPLOY.md now lists deploy/comfy/validation.json and records the final 17.85s full-suite duration. Its final SHA-256 is 1d866ccb24c0228c48b3407a6e8bd0b66eae31c2341d5f03cae75bbce954016e; this supersedes all earlier PREDEPLOY hashes. No other artifact changed.
## Implementation Evidence

Summary: Coordinator integrated and independently reran the fail-closed deployment candidate.

Commit SHA: 70c9c8324dc52083a4ed48e46b26dceeb50a7191

Commands run:
- PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_deployment_manifest.py
- PYTHONPATH=src .venv/bin/python -m pytest -q
- Offline comfy-cli 1.22.0 build validate from an isolated temporary directory
- Offline comfy-cli 1.22.0 build push --dry-run from an isolated temporary directory
- git diff --check

CI/Test Results:
- Focused deployment suite: 12 passed in 0.02s.
- Full suite: 75 passed, 1 pre-existing Starlette/httpx warning, in 18.30s.
- Offline validate: exit 0, ok=true, remote=false, model_count=13, folder_case_checked=false.
- Offline push dry-run: exit 0, created=false, upload_count=0, upload_bytes=0, uploaded=0, deduped=0.
- git diff --check passed.

AC Verification:
- [x] AC1: Local candidate/build spec and 13-entry machine-readable manifest pin commits, immutable current revisions, digests, sizes, destinations, and workflow hash 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.
- [x] AC2: Exact current BiRefNet and YuNet/SFace source traces, revisions, hashes, sizes, destinations, license evidence/unknowns, and fail-closed historical/runtime boundaries are recorded.
- [x] AC3: Python/Torch/CUDA mismatch, missing lock, groundingdino no-build preview, dynamic imports, graph drift, and unfetchable bare BFS ref remain explicit blockers with no selected base.
- [x] AC4: Twelve offline no-network/no-skip structural/hash/closure tests plus syntax-only CLI validate/push dry-run distinguish candidate from runnable deployment.
- [x] AC5: Commands, measured results, artifact hashes, rights boundaries, SDK-bridge dependency, and remaining blockers are reported without weights, paid calls, remote builds, or readiness claims.

Boundaries:
- This remains a fail-closed local candidate. Hosted compatibility, runtime staging/imports, historical byte identity, several licenses, SDK bridge inclusion, and runnable deployment remain unproven.


## nd_contract
status: delivered

### evidence
- Final PREDEPLOY.md SHA-256: 1d866ccb24c0228c48b3407a6e8bd0b66eae31c2341d5f03cae75bbce954016e.
- Final full-suite result: 75 passed, 1 pre-existing Starlette/httpx warning, 17.85s.
- Offline scoped result: 12 passed in 0.04s; comfy validate/push dry-run exit 0 with zero uploads.
- git diff --check and pvg story verify-delivery were rerun after this correction.

### proof
[x] AC1: final owned artifact inventory and workflow hash are accurate.
[x] AC2: exact implicit asset metadata/source evidence is unchanged.
[x] AC3: fail-closed runtime/dependency analysis is unchanged.
[x] AC4: offline test and syntax-only CLI boundaries are accurately recorded.
[x] AC5: final hashes, results, blockers, and pending SDK bridge are reported without readiness claims.

## nd_contract
status: delivered

### evidence
- Final owned artifact hashes: asset-manifest 2fb34f910fca9ad3bb9229ab3883a9b04539d77a457435e0700c096a47e106a0; comfy-build 89a52d508ce9e5bbf2ff52f5540d8b297f76f78982a785858c7c13029cb42342; dependency-matrix 87da3f9341b26c8e3e9ac41ab02d4358ed4c41efdf3433ffd044083285e65e02; validation 485ef1936a6b1d3ff40d72f1876170a4ae4a9aff86dce672228c224e5868d942; PREDEPLOY 6d205747c2dfc70d2247fb79634f6023dd4b921228afe3344e6c1be96ec0a825; test c669f8b7491f38740dbc04ad5cba3cad85f980f93b545f09c987172903c0ef38.

### proof
[x] AC1: final hashes corrected without changing ownership or claims.
[x] AC2: prior exact source/metadata evidence remains unchanged.
[x] AC3: dependency/runtime matrix remains unchanged.
[x] AC4: measured test/CLI evidence remains unchanged.
[x] AC5: final report uses the corrected PREDEPLOY hash.

## nd_contract
status: delivered

### evidence
- Detailed evidence, commands, file hashes, CI/Test Results, Summary, and blocker disclosure above.

### proof
[x] AC1: reproducible local candidate/manifest pins and workflow hash verified.
[x] AC2: exact implicit metadata/source traces verified with fail-closed unknowns.
[x] AC3: runtime matrix and dependency blockers verified without installs.
[x] AC4: offline no-network/no-skip tests and syntax-only receipts verified.
[x] AC5: exact results and remaining blockers reported; SDK bridge remains external.

## nd_contract
status: delivered

### evidence
- Detailed evidence, commands, hashes, and CI/Test Results above.

### proof
- [x] AC1
- [x] AC2
- [x] AC3
- [x] AC4
- [x] AC5

## nd_contract
status: delivered

### evidence
- See detailed Implementation Evidence and CI/Test Results above.

### proof
- [x] AC1-5 delivered as a non-runnable local candidate.

## nd_contract
status: delivered

### evidence
- CI/Test Results and Summary above; detailed evidence and hashes above.

### proof
- [x] AC #1: local candidate and manifest pin exact code/assets while preserving workflow hash.
- [x] AC #2: exact BiRefNet and YuNet/SFace paths/revisions/digests/sizes/licenses-or-unknowns traced from pinned source.
- [x] AC #3: runtime matrix and dependency/source-build/dynamic-import blockers documented; no false compatibility.
- [x] AC #4: offline no-network/no-skip tests and syntax-only CLI receipts distinguish candidate from runnable deployment.
- [x] AC #5: commands, results, hashes, SDK-bridge dependency, and blockers reported without deployment/readiness claims.

## Implementation Evidence
- Commit SHA: 98de3ff (base only; worker made no commit).
- Scoped artifacts: deploy/comfy/{asset-manifest.json,comfy-build.yaml,dependency-matrix.json,validation.json}, docs/deployment/PREDEPLOY.md, tests/test_deployment_manifest.py.
- Artifact SHA-256 values are recorded in the immediately preceding developer evidence and PREDEPLOY.md; canonical workflow SHA-256 is 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.
- Public metadata/source only; no model weights, credentials, account status, provider uploads, remote build, GPU, download, install, commit, merge, or push.

## CI/Test Results
- Offline scoped deployment tests: 12 passed in 0.04s.
- Full repository suite: 75 passed, 1 pre-existing Starlette/httpx deprecation warning, 17.71s.
- Offline comfy-cli 1.22.0 build validate: exit 0, ok=true, remote=false, model_count=13, folder_case_checked=false.
- Offline comfy-cli 1.22.0 build push --dry-run: exit 0, created=false, upload_count=0, upload_bytes=0, uploaded=0, deduped=0, folder_case_checked=false.
- git diff --check: clean.

Commands run:
- pvg nd show OJ-tfyt
- PYTHONPATH=src work/openjutsu-studio/.venv/bin/python -m pytest -q tests/test_deployment_manifest.py
- PYTHONPATH=src work/openjutsu-studio/.venv/bin/python -m pytest -q
- cd /private/tmp && uvx --offline --python 3.12 --from comfy-cli==1.22.0 comfy --json build validate <owned-deploy-comfy-directory>
- cd /private/tmp && uvx --offline --python 3.12 --from comfy-cli==1.22.0 comfy --json build push <owned-deploy-comfy-directory> --dry-run
- git diff --check
- shasum -a 256 deploy/comfy/* docs/deployment/PREDEPLOY.md tests/test_deployment_manifest.py

## Summary
Delivered a fail-closed local candidate, machine-readable 13-asset manifest with current public digests/revisions/sizes and exact implicit-source traces, runtime/dependency blocker matrix, syntax-only CLI receipts, and offline no-skip structural/hash/closure tests. Historical byte identity, runtime staging/import compatibility, hosted compatibility, several licenses, and SDK asset binding remain unresolved; no runnable deployment or readiness is claimed.

## nd_contract
status: delivered

### evidence
- Detailed implementation evidence and measured results above; authoritative file hashes and source citations in the prior developer block and PREDEPLOY.md.

### proof
- [x] AC1 verified
- [x] AC2 verified
- [x] AC3 verified
- [x] AC4 verified
- [x] AC5 verified

## nd_contract
status: delivered

### evidence
- Worktree base 98de3ff; scoped files only: deploy/comfy/asset-manifest.json, comfy-build.yaml, dependency-matrix.json, validation.json; docs/deployment/PREDEPLOY.md; new tests/test_deployment_manifest.py. git diff --check clean; no commit/merge/push.
- Artifact SHA-256: asset-manifest 2fb34f910fca9ad3bb9229ab3883a9b04539d77a457435e0700c096a47e106a0; comfy-build 89a52d508ce9e5bbf2ff52f5540d8b297f76f78982a785858c7c13029cb42342; dependency-matrix 87da3f9341b26c8e3e9ac41ab02d4358ed4c41efdf3433ffd044083285e65e02; validation 485ef1936a6b1d3ff40d72f1876170a4ae4a9aff86dce672228c224e5868d942; PREDEPLOY 404ecb4f8f1040e7b059d373be00b87aa3e6a13b77d6a45387632f2eeb3ffc05; test c669f8b7491f38740dbc04ad5cba3cad85f980f93b545f09c987172903c0ef38.
- Canonical workflow SHA-256 remains 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.
- PYTHONPATH=src work/openjutsu-studio/.venv/bin/python -m pytest -q tests/test_deployment_manifest.py: 12 passed in 0.04s. Full suite: 75 passed, 1 pre-existing Starlette/httpx warning, 17.71s.
- Offline comfy-cli 1.22.0 via uvx --offline --python 3.12 from /private/tmp: build validate exit 0 ok=true remote=false 13 model entries folder_case_checked=false; build push --dry-run exit 0 created=false upload_count=0 upload_bytes=0 uploaded=0 deduped=0 folder_case_checked=false. Receipt: deploy/comfy/validation.json.
- Current public metadata closes evidence paths for BiRefNet-general 77277264c0e8c74149d3ff2fade4fd8176965b7108f3c5fc3b8c9c811edb4519/884878856 bytes plus three support files at 1038lab/BiRefNet revision 4d000788a9698c7f8d67c8c6ce2b40c768f5b909; YuNet 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4/232589 and SFace 0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79/38696353 at opencv/opencv_zoo commit 47534e27c9851bb1128ccc0102f1145e27f23f98. Total current model metadata: 10 weights/46610845489 bytes.
- Exact source traces: RMBG py/AILab_BiRefNet.py:33-45,278-292,308-348; exact BFS parent 7b57eacb7b755ac6d7d7358e0a62e4096d83fce7 plus commit patch SHA256 42202e85dd9dba1c59100171bebb80f7c86518660a328a68e65a359977e48e83 gives bfs_shot_loop.py:728-751,759-786 and SHA256 663541cd85225f6fc4f14b61fb00f4672a8e9330687ebcb3e170988c8c80824d. No weights downloaded.
- Fail-closed blockers are explicit: no exact base image for Python3.13.15/Torch2.11.0+cu130; no selected base; no dependency lock; groundingdino-py no-wheel under no-build preview; dynamic imports; graph schema drift; recorded BFS bare SHA no longer fetchable although exact patch is public; RMBG/BiRefNet and opencv_face staging and licenses unresolved; SDK asset bridge pending parallel story. Candidate/runnable distinction and no legal conclusion are asserted.

### proof
- [x] AC1: reproducible local candidate and machine-readable 13-asset manifest preserve all five commits, immutable current revisions/digests/sizes, workflow hash, and contain no private account IDs/tokens/private local paths.
- [x] AC2: exact pinned source traces and current metadata for BiRefNet-general support/config plus YuNet/SFace; destinations come from code, historical identity and runtime closure remain explicitly false.
- [x] AC3: recorded/catalog runtime matrix, source-build and dynamic-import blockers documented; no base selected and compatibility fails closed; no installs.
- [x] AC4: 12 offline no-network/no-skip structural/hash/model-closure tests; syntax-only CLI validate/push dry-run receipts distinguish candidate from runnable deployment and preserve unknown rights.
- [x] AC5: exact commands, results, hashes, source citations, SDK-bridge dependency, and remaining blockers recorded here and in PREDEPLOY.md; parent review/commit/PM acceptance remains outside worker.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


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
