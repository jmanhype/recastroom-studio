---
id: OJ-krar
title: "Bind SDK assets and preserve submission identity without paid inference"
status: closed
priority: 0
type: feature
parent: OJ-a7l6
created_at: 2026-10-18T16:04:00Z
created_by: speed
updated_at: 2026-10-18T16:35:30Z
content_hash: "sha256:d370fd9a69b8dc711354ad69f7cb40a76c93b3a07c8a217069b7e847c348f441"
follows: [OJ-c1vo, OJ-p8rd, OJ-inuo, OJ-xtk4, OJ-4rht]
labels: [accepted]
closed_at: 2026-10-18T16:35:30Z
close_reason: "Accepted: annotation rework closes the sole PM type-spec rejection; behavior, tests, hashes, and workflow remain verified."
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
- Transitioned via pvg story deliver on 2026-10-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: Coordinator integrated and independently reran the delivered SDK asset-binding implementation.

Commit SHA: 1afb6fd87f99065fe1f485568f36850e2d05e5d4

Commands run:
- PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_comfy_sdk_runner.py tests/test_sdk_assets.py tests/test_sdk_protocol.py
- PYTHONPATH=src .venv/bin/python -m pytest -q
- git diff --check
- shasum -a 256 -c docs/evidence/sdk-assets/SHA256SUMS.txt

CI/Test Results:
- Focused suite: 30 passed in 6.73s.
- Annotation-rework focused suite: 30 passed in 6.89s.
- Annotation-rework full suite: 89 passed, 1 pre-existing Starlette/httpx warning, in 24.40s.
- git diff --check passed.
- All 15 scoped SHA256 entries verified after annotation rework.
- Canonical workflow SHA256 remains 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.

AC Verification:
- [x] AC1: Local planner/file validation, optional ref2, explicit SDK asset references, bridge route, and fail-closed deployment flag are implemented and tested.
- [x] AC2: App manifest inputs are wired; canonical workflow/audio/legacy behavior preserved; deterministic node 751 output and sanitized errors/filenames are tested.
- [x] AC3: Durable key/phase/provider-ID state, known-ID recovery, no resubmit after ambiguous response loss, and local duplicate serialization are tested.
- [x] AC4: Real installed comfy-sdk 0.5.0 protocol fixture covers required binding, output/audio wiring, failures, recovery, persistence, and traversal cases; focused/full suites pass.
- [x] AC5: Constructor contract and SDK floor are retained; deployment inclusion and unproven hosted stages are documented. No paid inference or production-ready claim.
- [x] PM quality gate: all four newly public SDK asset functions/methods now have complete parameter and return type specifications.

Boundaries:
- Hosted materialization, bridge registration, build packaging, model execution, and output quality remain unproven and require a separately authorized smoke test.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-10-18.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: Coordinator integrated and independently reran the delivered SDK asset-binding implementation.

Commit SHA: 147a748e4bb418eadc242383c3e444d828818c05

Commands run:
- PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_comfy_sdk_runner.py tests/test_sdk_assets.py tests/test_sdk_protocol.py
- PYTHONPATH=src .venv/bin/python -m pytest -q
- git diff --check
- shasum -a 256 -c docs/evidence/sdk-assets/SHA256SUMS.txt

CI/Test Results:
- Focused suite: 30 passed in 6.73s.
- Full suite: 89 passed, 1 pre-existing Starlette/httpx warning, in 25.29s.
- git diff --check passed.
- All 12 scoped SHA256 entries verified.
- Canonical workflow SHA256 remains 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.

AC Verification:
- [x] AC1: Local planner/file validation, optional ref2, explicit SDK asset references, bridge route, and fail-closed deployment flag are implemented and tested.
- [x] AC2: App manifest inputs are wired; canonical workflow/audio/legacy behavior preserved; deterministic node 751 output and sanitized errors/filenames are tested.
- [x] AC3: Durable key/phase/provider-ID state, known-ID recovery, no resubmit after ambiguous response loss, and local duplicate serialization are tested.
- [x] AC4: Real installed comfy-sdk 0.5.0 protocol fixture covers required binding, output/audio wiring, failures, recovery, persistence, and traversal cases; focused/full suites pass.
- [x] AC5: Constructor contract and SDK floor are retained; deployment inclusion and unproven hosted stages are documented. No paid inference or production-ready claim.

Boundaries:
- Hosted materialization, bridge registration, build packaging, model execution, and output quality remain unproven and require a separately authorized smoke test.


## Implementation Evidence

Summary: Coordinator integrated and independently reran the delivered SDK asset-binding implementation.

Commit SHA: 147a748e4bb418eadc242383c3e444d828818c05

### Commands run:
- PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_comfy_sdk_runner.py tests/test_sdk_assets.py tests/test_sdk_protocol.py
- PYTHONPATH=src .venv/bin/python -m pytest -q
- git diff --check
- shasum -a 256 -c docs/evidence/sdk-assets/SHA256SUMS.txt

### CI/Test Results:
- Focused suite: 30 passed in 6.73s.
- Full suite: 89 passed, 1 pre-existing Starlette/httpx warning, in 25.29s.
- git diff --check passed.
- All 12 scoped SHA256 entries verified.
- Canonical workflow SHA256 remains 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.

### AC verification:
- [x] AC1: Local planner/file validation, optional ref2, explicit SDK asset references, bridge route, and fail-closed deployment flag are implemented and tested.
- [x] AC2: App manifest inputs are wired; canonical workflow/audio/legacy behavior preserved; deterministic node 751 output and sanitized errors/filenames are tested.
- [x] AC3: Durable key/phase/provider-ID state, known-ID recovery, no resubmit after ambiguous response loss, and local duplicate serialization are tested.
- [x] AC4: Real installed comfy-sdk 0.5.0 protocol fixture covers required binding, output/audio wiring, failures, recovery, persistence, and traversal cases; focused/full suites pass.
- [x] AC5: Constructor contract and SDK floor are retained; deployment inclusion and unproven hosted stages are documented. No paid inference or production-ready claim.

### Boundaries:
- Hosted materialization, bridge registration, build packaging, model execution, and output quality remain unproven and require a separately authorized smoke test.


## Implementation Evidence (DELIVERED)

Summary: Uncommitted unpaid SDK asset binding and durable submission recovery delivered for parent integration and independent PM review.

Commit SHA: No implementation commit: explicitly prohibited by assignment. Base HEAD only: 98de3ff703f584755d38c01cb6bb66fc997f0707. This base SHA is NOT evidence that the patch has been committed. Scoped SHA256SUMS.txt identifies the delivered disk artifacts.

### CI/Test Results
- Commands run:
  - PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q
  - PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest tests/test_comfy_sdk_runner.py tests/test_sdk_assets.py tests/test_sdk_protocol.py -q
  - git diff --check
  - shasum -a 256 -c docs/evidence/sdk-assets/SHA256SUMS.txt
- Results: full89 passed, 1 warning; focused30 passed; diff check passed; all12 scoped hash entries OK. Local protocol tests, not CI/hosted inference.

## nd_contract
status: delivered

### evidence
- Bounded uncommitted OJ-krar diff at story worktree dev-OJ-krar, base98de3ff. Parent integrates; PM accepts. No commits/pushes by worker.
- Full suite with root .venv/bin/python and PYTHONPATH=src: 89 passed, 1 warning in 25.05s. Focused constructor/assets/protocol suite: 30 passed in 6.92s. git diff --check passed.
- Logs: docs/evidence/sdk-assets/pytest.txt and focused.txt. Implementation/evidence hashes: docs/evidence/sdk-assets/SHA256SUMS.txt. Detail: docs/evidence/sdk-assets/DELIVERY.md.
- Canonical workflow SHA256 unchanged: 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.
- Real installed comfy-sdk0.5.0 exercised against synthetic-only localhost HTTP protocol fixture. No credentials, provider upload, inference, model download or remote build.

### proof
- [x] AC #1: local planner/file validation, optional ref2, explicit core/ASSET filename bridge to BFS plan STRING, runtime input-root/file checks; deployment configuration fails closed by default.
- [x] AC #2: actual manifest inputs passed, canonical workflow unchanged, node751 output chosen, original source finalization retained, filenames/errors sanitized; legacy/dry-run/existing tests unchanged.
- [x] AC #3: stable durable key and immediate durable provider ID, known-ID GET recovery, ambiguous-loss refusal, prepared upload-failure distinction, local duplicate submission serialization tested.
- [x] AC #4: real SDK localhost fixture covers required content/route, missing input, output/audio wiring, upload/terminal failures, response loss, restart-like recovery, traversal paths; full suite passes.
- [x] AC #5: constructor contract retained, SDK floor0.5.0, docs/deployment/SDK_ASSETS.md explains build inclusion and unproven stages.
- [ ] Separate hosted acceptance: materialization, bridge registration, build/model execution and output quality remain unproven. No live-render/production-ready claim. Explicit bridge flag is not attestation; real server must materialize filenames or bridge fails closed.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


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
- 2026-10-18T16:21:40Z status: in_progress -> in_progress
- 2026-10-18T16:21:40Z auto-follows: linked to predecessor OJ-inuo
- 2026-10-18T16:22:29Z status: in_progress -> in_progress
- 2026-10-18T16:22:29Z auto-follows: linked to predecessor OJ-xtk4
- 2026-10-18T16:28:14Z status: in_progress -> open
- 2026-10-18T16:28:14Z released by speed
- 2026-10-18T16:31:53Z status: open -> in_progress
- 2026-10-18T16:31:53Z auto-follows: linked to predecessor OJ-4rht
- 2026-10-18T16:35:30Z status: in_progress -> closed
- 2026-10-18T16:35:30Z dep_removed: no_longer_blocks OJ-yf2c

## Links
- Parent: [[OJ-a7l6]]
- Follows: [[OJ-c1vo]], [[OJ-p8rd]], [[OJ-inuo]], [[OJ-xtk4]], [[OJ-4rht]]

## Comments

### 2026-10-18T16:21:01Z speed
## nd_contract
status: delivered

### evidence
## Implementation Evidence

Summary: Coordinator integrated and independently reran the delivered SDK asset-binding implementation.

Commit SHA: 147a748e4bb418eadc242383c3e444d828818c05

### Commands run:
- PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_comfy_sdk_runner.py tests/test_sdk_assets.py tests/test_sdk_protocol.py
- PYTHONPATH=src .venv/bin/python -m pytest -q
- git diff --check
- shasum -a 256 -c docs/evidence/sdk-assets/SHA256SUMS.txt

### CI/Test Results:
- Focused suite: 30 passed in 6.73s.
- Full suite: 89 passed, 1 pre-existing Starlette/httpx warning, in 25.29s.
- git diff --check passed.
- All 12 scoped SHA256 entries verified.
- Canonical workflow SHA256 remains 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.

### AC Verification:
- [x] AC1: Local planner/file validation, optional ref2, explicit SDK asset references, bridge route, and fail-closed deployment flag are implemented and tested.
- [x] AC2: App manifest inputs are wired; canonical workflow/audio/legacy behavior preserved; deterministic node 751 output and sanitized errors/filenames are tested.
- [x] AC3: Durable key/phase/provider-ID state, known-ID recovery, no resubmit after ambiguous response loss, and local duplicate serialization are tested.
- [x] AC4: Real installed comfy-sdk 0.5.0 protocol fixture covers required binding, output/audio wiring, failures, recovery, persistence, and traversal cases; focused/full suites pass.
- [x] AC5: Constructor contract and SDK floor are retained; deployment inclusion and unproven hosted stages are documented. No paid inference or production-ready claim.

Boundaries:
- Hosted materialization, bridge registration, build packaging, model execution, and output quality remain unproven and require a separately authorized smoke test.


### 2026-10-18T16:28:05Z speed
## PM Review Evidence (2026-10-18)

Reviewed commit 147a748e4bb418eadc242383c3e444d828818c05 against base 98de3ff703f584755d38c01cb6bb66fc997f0707.

- Scoped diff: 15 files, 778 insertions, 20 deletions; confined to assigned app/SDK/bridge/floor/tests/docs/evidence scope; `git diff --check` passed.
- `pvg story verify-delivery OJ-krar`: 7 passed, 2 failed (`nd_contract:eof`, `proof:ac_items`). Judgment: substantive evidence is nevertheless complete—the last delivered contract is identifiable and contains explicit AC1-AC5 proof, while commit SHA/commands/results are present in the coordinator evidence comment; the EOF failure reflects generated History/Links content after the contract and the AC parser does not recognize the `AC1` spelling. These are formatting/parser failures, not absent evidence.
- Focused suite with root checkout `.venv/bin/python`, `PYTHONPATH=src`: 30 passed in 6.64s.
- Full suite with root checkout `.venv/bin/python`, `PYTHONPATH=src`: 89 passed, 1 Starlette/httpx deprecation warning, in 24.21s.
- `shasum -a 256 -c docs/evidence/sdk-assets/SHA256SUMS.txt`: all 12 entries OK.
- Canonical `workflows/openjutsu_h3_lipsync_local.json` SHA256: 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21; workflow also has zero diff across the story range.
- Installed SDK verified as comfy-sdk 0.5.0 from the root checkout virtual environment.

PM gate finding: Tier 1b requires type specifications for public functions in new modules. `src/openjutsu/sdk_assets.py` exposes `validate_inputs` and `bind_graph` without parameter/return annotations, and `custom_nodes/openjutsu_assets/__init__.py` exposes `OpenJutsuAssetPlan.INPUT_TYPES` and `.bind` without return/parameter annotations. This is a rejection independent of the tracker-format false positives above.

### 2026-10-18T16:28:14Z speed
## PM Decision
REJECTED [2026-10-18]:
EXPECTED: PM Tier 1b requires every public function in a new module to have complete parameter and return type specifications.
DELIVERED: At commit 147a748e4bb418eadc242383c3e444d828818c05, `src/openjutsu/sdk_assets.py` exposes `validate_inputs(workflow, source, reference_1, reference_2=None)` and `bind_graph(client, workflow, plan, files)` without annotations, and `custom_nodes/openjutsu_assets/__init__.py` exposes `OpenJutsuAssetPlan.INPUT_TYPES(cls)` and `bind(self, plan, video, global_ref, global_ref2="")` without complete signatures/returns.
GAP: The functional AC evidence and independent tests pass, but the deterministic new-public-function type-spec gate does not.
FIX: Add precise parameter/return annotations (using SDK `Any`/protocol or type aliases where exact SDK types are not exported), then rerun focused and full suites and regenerate/update the scoped SHA256SUMS evidence for changed files.

Structural verify-delivery judgment: its `nd_contract:eof` and `proof:ac_items` failures are formatting/parser issues, not missing substantive evidence. The authoritative delivered contract and AC1-AC5 proof are present, as are commit SHA, commands, counts, hashes, and boundaries. That judgment is documented in the PM review comment, but does not waive the type-spec gate.

## nd_contract
status: rejected

### evidence
- Independent focused suite: 30 passed in 6.64s.
- Independent full suite: 89 passed, 1 existing Starlette/httpx deprecation warning, in 24.21s.
- All 12 scoped SHA256SUMS entries passed; canonical workflow hash is exactly 06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21.
- PM Tier 1b static inspection found missing annotations on the new public functions/methods listed above.

### proof
- [ ] Quality gate: public functions in new SDK asset modules have complete parameter and return type specifications.
- [x] Substantive story evidence was independently present despite `verify-delivery` contract-placement/AC-parser formatting failures.

### 2026-10-18T16:35:30Z speed
## PM Recheck Evidence (2026-10-18)

Rechecked only `147a748e4bb418eadc242383c3e444d828818c05..1afb6fd87f99065fe1f485568f36850e2d05e5d4` at story commit `1afb6fd87f99065fe1f485568f36850e2d05e5d4`.

- Diff scope: 6 files, 74 insertions, 7 deletions, limited to annotations/type aliases and rework evidence/hash updates. `git diff --check`: PASS.
- The four previously untyped public entry points now have complete annotations:
  - `validate_inputs(workflow: WorkflowGraph, source: str | Path, reference_1: str | Path, reference_2: str | Path | None = None) -> tuple[PlannerData, AssetFiles, str]`
  - `bind_graph(client: Comfy, workflow: WorkflowGraph, plan: PlannerData, files: AssetFiles) -> Workflow`
  - `OpenJutsuAssetPlan.INPUT_TYPES(cls: type[OpenJutsuAssetPlan]) -> InputSchema`
  - `OpenJutsuAssetPlan.bind(plan: str, video: str, global_ref: str, global_ref2: str = "") -> tuple[str]`
- Annotation-normalized AST comparison: `src/openjutsu/sdk_assets.py` identical (`53763510fc358043153bc53deab6549deb5e83e3e56b6c269250d808ae78cd59`); `custom_nodes/openjutsu_assets/__init__.py` identical (`a9825670b0781d242b1f410242cbbe309dce66d909c00a2e7586bfb828e35da6`). No executable behavior branch, validation rule, default, network call, graph field, or output selection changed.
- TYPE_CHECKING-only SDK imports resolve against installed comfy-sdk 0.5.0.
- Focused suite with root checkout `.venv/bin/python`, `PYTHONPATH=src`: 30 passed in 6.71s.
- Full suite with root checkout `.venv/bin/python`, `PYTHONPATH=src`: 89 passed, 1 existing Starlette/httpx deprecation warning, in 24.90s.
- `shasum -a 256 -c docs/evidence/sdk-assets/SHA256SUMS.txt`: all 15 entries OK.
- Canonical workflow is untouched by the annotation-rework diff.
- `pvg story verify-delivery OJ-krar` still reports 7 passed / 2 failed from the previously documented contract-placement/AC-parser formatting issues; substantive evidence remains complete.

The sole PM rejection—missing complete public-function type specifications—is closed.
