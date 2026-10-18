---
id: OJ-krar
title: "Bind SDK assets and preserve submission identity without paid inference"
status: in_progress
priority: 0
type: feature
parent: OJ-a7l6
created_at: 2026-10-18T16:04:00Z
created_by: speed
updated_at: 2026-10-18T16:17:20Z
content_hash: "sha256:c94f66e5f8287b04249a133e92bf8ee6bd5c5433393b0e5d92992435c99bcf0b"
blocks: [OJ-yf2c]
assignee: dev-OJ-krar
follows: [OJ-c1vo, OJ-p8rd]
---

## Description
Scope: User approved unpaid engineering only. Pipeline correctness/security-sensitive bounded task for one Astra worker. Base accepted preview98de3ff. Own src/openjutsu/comfy_sdk_runner.py, new src/openjutsu/sdk_*.py if necessary, SDK portions app/main.py and src/openjutsu/cli.py if called, pyproject.toml/requirements.txt SDK floor only, new custom_nodes/openjutsu_assets/** if a proven bridge is necessary, NEW tests/test_sdk_assets.py and tests/test_sdk_protocol.py, docs/deployment/SDK_ASSETS.md and docs/evidence/sdk-assets/**. Do not change static workflow JSON/media/audio/LoRA parameters, legacy renderer guard, frontend design, existing tests, unrelated code. No recursive delegation, credentials, real provider upload, GPU, purchases, remote builds, commits/merges by worker.

Parent findings: installed official comfy-sdk0.5.0. Current adapter run_workflow merely from_json->run->outputs; app _run_sdk_job has source/ref paths in job.json but does not upload/bind. Node1189.inputs.plan is a serialized JSON string containing video/global_ref/global_ref2. Official lazy Asset handles become core/ASSET objects at submit, and cannot simply be embedded as strings and assumed hydrated. Asset.upload/commit alone does not prove remote BFS file visibility. Research exact v2 binding/materialization semantics first from installed SDK and primary source. Official docs https://docs.comfy.org/development/api-development/sdks and https://docs.comfy.org/api-reference/v2/overview. No public media/account data provided to worker. Graph indexed project openjutsu-studio-OJ-inuo generation2026-10-18T04:17:38Z is missing source paths; use exact checkout source fallback for these modules. No exhaustive graph claims.

AC1: Validate source/reference files + planner shape locally before upload/submission; support optional ref2. Use installed official SDK public APIs, real explicit asset binding through a compatible graph interface; do not assume local filenames or asset IDs inside JSON strings resolve. If v2 cannot expose a path within existing nodes, implement a minimal well-tested explicit custom-node bridge and document required deployment inclusion, keeping pinned BFS behavior and all untouched graph fields. Fail closed if unproven unsupported; do not invent SDK methods.
AC2: Wire actual app job manifest inputs to adapter, preserve canonical on-disk workflow/hash, original source audio finalization and existing legacy/dry_run behavior. Output selection should be deterministic correct generation node751 rather than arbitrary first MP4/comparison. Sanitize provider error data and filenames/paths; never write output outside job dir or expose secrets in status.
AC3: Persist a stable submit key before submission and provider job ID immediately after response, before wait/download. No blind resubmit or fresh key after ambiguous failure, including restart/retry. Recover known IDs by read/wait/download. Official v2 duplicate keys return422 not prior job. Distinguish pre-submit failure from unknown submission. Keep duplicate run safety; bounded single-job/process test scope not distributed queue claim.
AC4: Add deterministic tests using actual official SDK against clearly labelled local HTTP protocol fixture (no model/inference). Cover source/ref1/ref2 content binding + graph route, missing input before network, correct output selection/audio call wiring, terminal error, upload failure, submit-response loss, resume known job ID with zero extra POST, restart-like persistence and traversal filename rejection. Synthetic fixtures only; no paid/free remote media uploads. Existing tests unchanged and full suite passes.
AC5: Preserve minimum legacy constructor contract tests; version floor at least SDK version required by used surface. Explain unproven deployment/provider stages and SDK bridge build inclusion. Report artifacts and test evidence, no live render or production-ready claim. Parent integrates/verifies, independent PM accepts.

## nd_contract
status: new
### evidence
- Source inspection verified SDK missing file binding and serialized BFS plan; primary SDK doc says assets lazy + stable-key/job-ID recovery.
### proof
- [ ] AC1-5 verified in no-GPU protocol tests, paid smoke remains separate.


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: delivered

### evidence
- Bounded uncommitted OJ-krar diff at story worktree dev-OJ-krar, base98de3ff. Parent integrates; PM accepts. No commits/pushes by worker.
- Full suite with root .venv/bin/python and PYTHONPATH=src: 89 passed, 1 warning in 25.05s. Focused constructor/assets/protocol suite: 30 passed in 6.92s. git diff --check passed.
- Logs: docs/evidence/sdk-assets/pytest.txt and focused.txt. Implementation/evidence hashes: docs/evidence/sdk-assets/SHA256SUMS.txt. Detail: docs/evidence/sdk-assets/DELIVERY.md.
- Canonical workflow SHA256 unchanged: 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.
- Real installed comfy-sdk0.5.0 exercised against synthetic-only localhost HTTP protocol fixture. No credentials, provider upload, inference, model download or remote build.

### proof
- [x] AC1: local planner/file validation, optional ref2, explicit core/ASSET filename bridge to BFS plan STRING, runtime input-root/file checks; deployment configuration fails closed by default.
- [x] AC2: actual manifest inputs passed, canonical workflow unchanged, node751 output chosen, original source finalization retained, filenames/errors sanitized; legacy/dry-run/existing tests unchanged.
- [x] AC3: stable durable key and immediate durable provider ID, known-ID GET recovery, ambiguous-loss refusal, prepared upload-failure distinction, local duplicate submission serialization tested.
- [x] AC4: real SDK localhost fixture covers required content/route, missing input, output/audio wiring, upload/terminal failures, response loss, restart-like recovery, traversal paths; full suite passes.
- [x] AC5: constructor contract retained, SDK floor0.5.0, docs/deployment/SDK_ASSETS.md explains build inclusion and unproven stages.
- [ ] Separate hosted acceptance: materialization, bridge registration, build/model execution and output quality remain unproven. No live-render/production-ready claim. Explicit bridge flag is not attestation; real server must materialize filenames or bridge fails closed.

## History
- 2026-10-18T16:04:00Z dep_added: blocks OJ-yf2c
- 2026-10-18T16:06:50Z status: open -> in_progress
- 2026-10-18T16:06:50Z auto-follows: linked to predecessor OJ-c1vo
- 2026-10-18T16:06:50Z claimed by dev-OJ-krar
- 2026-10-18T16:17:20Z status: in_progress -> in_progress
- 2026-10-18T16:17:20Z auto-follows: linked to predecessor OJ-p8rd

## Links
- Parent: [[OJ-a7l6]]
- Blocks: [[OJ-yf2c]]
- Follows: [[OJ-c1vo]], [[OJ-p8rd]]

## Comments
