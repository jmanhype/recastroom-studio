---
id: OJ-8zaw
title: "Redact prepared-job history config to a safe allowlist"
status: in_progress
priority: 0
type: bug
labels: [studio, foundation, local, no-spend, security, delivered]
parent: OJ-mnrv
created_at: 2026-10-27T05:32:07Z
created_by: speed
updated_at: 2026-10-27T05:41:50Z
content_hash: "sha256:971e2b402b1f5ea5d66285ce240d06bb2242b585f3fe57389946c5c4b7afd983"
blocks: [OJ-5uq4, OJ-wfpy]
assignee: dev-OJ-8zaw
follows: [OJ-6xh3]
---

## Description
Accepted OJ-6xh3 persists prepared-job history, but its public configuration projection is unsafe. A real integration review at epic merge a3bc898d11387828ead58e7ad5dff02523d4fead found that the full uploaded/custom workflow graph is stored as `PreparedConfigRecord.config` and therefore as future project history. Fix this before OJ-5uq4 exposes that history through the connected API/UI.

## Root Cause
At integration a3bc898:
- `src/openjutsu/workspace_store.py:497-513` validates only that `workflow.json` is an object, then returns `config: payloads["workflow.json"]` verbatim.
- `src/openjutsu/workspace_store.py:318-343` serializes that value into `prepared_configs.config_json` and returns it as `PreparedConfigRecord.config`.
- `src/openjutsu/workspace_store.py:561-568` decodes the same persisted value on reopen/list.
- `app/main.py:81-128` accepts an uploaded custom `workflow`, and `src/openjutsu/pipeline.py:31-86` copies and emits that graph as `jobs/<job_id>/workflow.json`.

Credential-stripped synthetic temp probe (no real key, private media, network, provider, or GPU): a custom workflow containing nested sentinel `SYNTHETIC_API_KEY_NOT_A_REAL_CREDENTIAL`, `/private/tmp/synthetic/private-input.mov`, an arbitrary nested map, and list was prepared through the real API. `record_prepared_job(...).config` equaled the complete workflow; the key and path were present before and after SQLite reopen. Probe result: `{"recorded_config_equals_full_workflow":true,"reopened_config_exposed":true,"sentinel_key_exposed":true,"sentinel_path_exposed":true}`.

## USER INTENT
Saved project history must remain useful across restart without turning an uploaded ComfyUI graph into a durable secret/personal-path disclosure surface. The connected UI can show safe job metadata while the complete workflow remains a server-side job artifact identified by its existing SHA-256.

## Safe Config Contract
`PreparedConfigRecord.config` must be an exact, six-key allowlist, not a recursively redacted copy of the graph and not an open-ended projection:

```python
{
    "audio_mode": "auto",
    "reference_names": ["<basename-only>", "...optional second basename-only..."],
    "scheduler_steps": 8,
    "seed": <the same non-bool int as PreparedConfigRecord.seed>,
    "video_name": "<basename-only>",
    "with_audio": True,
}
```

Requirements:
- The key set is exactly the six keys above; no additional key, node ID, class type, prompt text, model name, graph JSON, serialized plan, credential, absolute path, or arbitrary nested value may appear.
- `video_name` and each entry in `reference_names` must be nonempty basename-only strings (`Path(value).name == value`); `reference_names` has one or two entries and must not contain an empty placeholder when `reference_2` is absent.
- `scheduler_steps` and `seed` are non-bool integers; `with_audio` is boolean; `audio_mode` is the literal `"auto"`.
- Unsupported extra fields in a valid custom graph are ignored by this projection. Recording must continue to support custom graphs; do not repair this by disabling uploaded/custom workflows.
- If a selected/known field is missing or has an unsupported type, fail closed with an existing `WorkspaceStoreError` subtype. Never fall back to the raw workflow.
- Apply the projection before SQL persistence and to reads; existing historical rows that contain a full graph must not be returned through the public record as-is. Reads must expose only the allowlist (reject a malformed/unprojectable historical row explicitly rather than leak it). No migration is authorized in this two-file budget.

## Affected Components / DIFF BUDGET
- `src/openjutsu/workspace_store.py` — safe prepared-config projection and persistence/read behavior.
- `tests/test_workspace_store.py` — real SQLite/custom-workflow regression and reopen tests.

Exactly 2 files. No app/API/UI, pipeline, workflow, schema-migration, verifier, evidence, graph, or fixture edits. A gross overrun is mandatory PM investigation, not automatic rejection.

## Boundary Map
PRODUCES:
- `src/openjutsu/workspace_store.py` -> `record_prepared_job(project_id: str, job_id: str, job_dir: Path, character_version: tuple[str, int] | None = None) -> PreparedConfigRecord` with the exact safe `config` contract above and unchanged public signature.
- `src/openjutsu/workspace_store.py` -> `list_prepared_jobs(project_id: str) -> list[PreparedConfigRecord]` with persisted history projected through the same exact safe config contract.
- `tests/test_workspace_store.py` -> real custom-workflow/SQLite/reopen/artifact-invariance regression tests using only synthetic sentinel values.

CONSUMES:
- OJ-6xh3: `src/openjutsu/workspace_store.py` -> `PreparedConfigRecord(project_id: str, job_id: str, character_id: str | None, character_version: int | None, seed: int, workflow_sha256: str, prompt_sha256: str, source_sha256: str | None, reference_sha256s: list[str], config: dict[str, Any], created_at: str)`.
  spec: retain the typed record and the two public prepared-history method signatures above; only the semantics of `config` change from full graph to exact allowlist.
- (existing): `src/openjutsu/pipeline.py` -> `prepare_workflow(settings: Settings, *, job_id: str, source: str | Path, reference_1: str | Path, reference_2: str | Path | None, words_path: str | Path | None, rights_attested: bool, identity_description: str | None = None, seed: int = 49, workflow_template: str | Path | None = None) -> tuple[PreparedJob, dict[str, Any]]`.
  spec: consume the real produced `job.json`, `workflow.json`, and `prompt.txt` unchanged; do not alter generation, validation, attestation, custom-template support, or artifact bytes.

## Acceptance Criteria
1. Recording a prepared job derived from a custom workflow returns exactly the six-key safe config contract above; it does not equal or contain the full `workflow.json`, graph nodes, prompt text, serialized planner plan, unsupported nested maps/lists, credentials, or absolute paths.
2. A real temp-SQLite regression uses `prepare_workflow(..., workflow_template=...)` with synthetic adversarial values nested in a valid custom graph (including `SYNTHETIC_API_KEY_NOT_A_REAL_CREDENTIAL`, `/private/tmp/synthetic/private-input.mov`, a nested map, and a list). `prepared_configs.config_json` and the returned record contain none of those sentinel values, while valid custom-graph preparation still succeeds. Use no real key or private media.
3. A fresh `WorkspaceStore(root)` reopened on the same real temp SQLite database returns the identical exact safe config from `list_prepared_jobs(project_id)`; the public read path cannot return an unprojected full-graph row.
4. Full workflow/prompt/source/reference provenance remains unchanged: before/after recording, `jobs/<job_id>/workflow.json` and `prompt.txt` bytes are byte-identical, their SHA-256 values still match `workflow_sha256`/`prompt_sha256`, source/reference hashes remain unchanged, and all job artifacts remain present. The safe config does not replace or rewrite those artifacts.
5. Focused regression, the full existing suite, compileall, and touched gates pass from the integration worktree with no skipped test, warning filter, marker suppression, or weakened assertion. The existing disclosed warning remains disclosed.
6. The source diff touches exactly `src/openjutsu/workspace_store.py` and `tests/test_workspace_store.py`; OJ-6xh3 remains historically accepted and unchanged as a story record.

## Testing Requirements
- Unit/real integration only in this bug; no mock replaces WorkspaceStore, SQLite, filesystem artifacts, or `prepare_workflow`.
- Mandatory focused command: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q tests/test_workspace_store.py`.
- Mandatory full command: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q`.
- Mandatory compile command: `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m compileall -q src/openjutsu/workspace_store.py tests/test_workspace_store.py`.
- Mandatory gate command: `pvg gates src/openjutsu/workspace_store.py tests/test_workspace_store.py --format text`.
- Record exact commands, exit status, pass/fail counts, warning inventory, file hashes, and artifact-byte/hash invariance. Include exact `LEARNINGS:` and `OBSERVATIONS:` sections.

## Discovered During
Integration review of accepted story OJ-6xh3 after local merge a3bc898. OJ-6xh3 remains accepted as a historical record; this child tracks the newly discovered regression without reopening or rewriting that acceptance.

## OUT OF SCOPE
- No API/UI work: OJ-5uq4 owns connected exposure and remains blocked by this bug.
- No pipeline/workflow changes: custom graph preparation and artifact generation remain unchanged.
- No schema migration or historical data rewrite: only the public projection/read behavior is in this two-file budget.
- No provider, GPU, network, credential, publication, or push action.

## MANDATORY SKILLS
- developer — owns the bounded implementation and delivery evidence.
- codebase-memory — verifies current brownfield paths, APIs, and call relationships before edits.
- pm_acceptor — performs independent evidence-based acceptance; implementation cannot self-accept.

## nd_contract
status: new

### evidence
- Created: 2026-10-27 by SrPM bug triage from integration finding at a3bc898.
- Source and synthetic temp probe confirmed full-workflow exposure and persistence across reopen.

### proof
- [ ] Pending implementation and independent PM verification of AC #1-#6.

## Design

## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
PROOF:
### CI/Test Results
Commands run:
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q tests/test_workspace_store.py
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m pytest -q
- env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHONPATH=src /Users/speed/Documents/Codex/2026-10-11/how-to-do-it-how-to/work/openjutsu-studio/.venv/bin/python -m compileall -q src/openjutsu/workspace_store.py tests/test_workspace_store.py
- pvg verify src/openjutsu/workspace_store.py tests/test_workspace_store.py --format=text
- pvg gates src/openjutsu/workspace_store.py tests/test_workspace_store.py --format text
- git diff --check
- shasum -a 256 src/openjutsu/workspace_store.py tests/test_workspace_store.py
Summary: all commands exit 0. Focused 52 passed in 0.35s; full 178 passed in 24.05s, zero failures/skips, 1 disclosed existing StarletteDeprecationWarning. Compileall pass. VERIFY PASSED: 2 files, 0 issues. Touched GATES PASS: 1 warn, 0 skipped. Coverage percentage not measured; real filesystem/SQLite/custom preparation/reopen behavior directly asserted.
Commit SHA: cdd6adc0aa1cbbe364764f29ef06c5cf59f4fe56
Branch: story/OJ-8zaw
File hashes:
- src/openjutsu/workspace_store.py SHA256 d92e805cafc1811d3c9034d2f7828035af1248f83573abdb761a82c5155f87c1
- tests/test_workspace_store.py SHA256 713cd59c9b612fcdddcb771fbd9efc799afb695b077606a023e5e7b8d43521bb
### AC checklist
- [x] AC #1: _workflow_config selects six fields; _safe_config validates exact output, nonbool ints, seed consistency, bool audio and basename-only filenames. Existing raw-graph equality assertion replaced by stronger exact config assertion.
- [x] AC #2: test_custom_graph_history_is_safe_and_artifacts_are_unchanged prepares real custom graphs with all requested synthetic sentinels nested in graph and planner; direct SQLite SELECT and returned config equal exact safe object, contain no sentinels.
- [x] AC #3: reopen equals original record; legacy full graphs explicitly raise ValidationError with no migration; missing keys, invalid types/shapes/JSON and extras covered on reads.
- [x] AC #4: custom graph test snapshots every job artifact plus source, both refs and template; bytes and artifact inventory unchanged; workflow/prompt/source/reference SHA256 comparisons pass with one and two references.
- [x] AC #5: focused/full/compileall/verify/touched gates pass; no mocks, skips, filters or weakened assertions. Existing warning disclosed below.
- [x] AC #6: git commit changes exactly assigned two files. OJ-6xh3 history not modified; no pipeline, API, fixtures, graph, migration, provider, network or media edits.
LEARNINGS:
- Configure workflow stores selected settings across planner JSON and three nodes; projection must validate types rather than recursively redact.
- Rejecting historical graph rows closes the public read leak without rewriting historical data.
- Graph tool inventory had zero indexed projects; bounded direct reads verified store -> pipeline -> configure_workflow relationships.
OBSERVATIONS:
- Existing StarletteDeprecationWarning at fastapi/testclient.py:1: Using httpx with starlette.testclient is deprecated; install httpx2 instead. No dependencies changed or warnings suppressed.
- Existing file_loc gate category remains: workspace_store.py now 565 nonblank lines > 400. Initial new complexity warning removed through bounded validation helper extraction; final touched gates only have file_loc warning.
- pvg notes search unavailable because configured Claude vault missing; not a code/test failure. No raw vault edits.
- No push, acceptance, close or merge performed.
DISCOVERED_BUG:
  title: Existing Starlette TestClient httpx deprecation
  context: Full suite passes 178 tests with the known single warning at fastapi/testclient.py:1; dependency remediation outside exact two-file security scope.
  affected_files: installed fastapi/testclient.py and dependency configuration
  discovered_during: OJ-8zaw
## nd_contract
status: delivered
### evidence
- cdd6adc0aa1cbbe364764f29ef06c5cf59f4fe56: focused 52 passed; full 178 passed, 1 disclosed warning; compileall/verify/gates exit 0.
### proof
- [x] AC #1: exact validated six-key config.
- [x] AC #2: custom workflow sentinel exclusion in real SQLite.
- [x] AC #3: reopen safe, historical graph rejected.
- [x] AC #4: artifact bytes and provenance hashes unchanged.
- [x] AC #5: full verification passed, warnings disclosed.
- [x] AC #6: exactly two source files changed.


## History
- 2026-10-27T05:33:08Z dep_added: blocks OJ-5uq4
- 2026-10-27T05:33:55Z dep_added: blocks OJ-wfpy
- 2026-10-27T05:37:47Z status: open -> in_progress
- 2026-10-27T05:37:47Z auto-follows: linked to predecessor OJ-6xh3
- 2026-10-27T05:37:47Z claimed by dev-OJ-8zaw
- 2026-10-27T05:41:50Z status: in_progress -> in_progress

## Links
- Parent: [[OJ-mnrv]]
- Blocks: [[OJ-5uq4]], [[OJ-wfpy]]
- Follows: [[OJ-6xh3]]

## Comments
