# SDK asset binding: unpaid engineering, not hosted execution proof

OJ-krar targets official `comfy-sdk>=0.5.0`. It preserves the minimum legacy
constructor contract, the canonical workflow file, all generation parameters,
node 751 audio wiring, and application finalization with the original source.
Only the in-memory submitted graph adds `openjutsu_assets` and changes
`1189.inputs.plan` to the bridge's STRING output link.

## Why a bridge is necessary

Primary sources inspected 2026-10-18:

- [Official SDK docs](https://docs.comfy.org/development/api-development/sdks)
  and [API v2 overview](https://docs.comfy.org/api-reference/v2/overview).
- [Official Python SDK](https://github.com/Comfy-Org/comfy-python-sdk): installed
  0.5.0 `assets.py`, `workflows.py`, `client.py`, `jobs.py`, `outputs.py`.
  Used public APIs: `assets.from_bytes`, `Asset.as_reference`,
  `workflows.from_json`, `submit(idempotency_key=...)`, `jobs.get`, `Job.wait`,
  `Job.get_outputs`, `Output.to_file`.
- [Official TypeScript SDK contract](https://github.com/Comfy-Org/comfy-typescript-sdk)
  explicitly states asset handles resolve to filenames, not decoded media.
- [BFS pinned source](https://github.com/alisson-anjos/ComfyUI-BFSNodes/blob/a93cea17a9f4315110f9c66a29735829e956a9cc/bfs_shot_loop.py):
  `_input_path` calls `folder_paths.get_annotated_filepath`; `BFSShotPlanner`
  takes a JSON STRING `plan`. Its former image inputs are explicitly ignored.
  `_load_plan` prefers `global_refs` when present over legacy ref/ref2 fields.

An asset UUID pasted inside that JSON string is not a filename and does not
materialize bytes. Upload success alone cannot make the existing graph run.

The adapter validates planner structure and nonempty files/supported extensions
before any network operation. It snapshots bytes in memory, binds content-hashed
filenames through real `core/ASSET` objects in separate STRING inputs, and leaves
the serialized plan free of old local filenames. Validation does not decode or
certify media; synthetic protocol fixtures deliberately are not real MP4/images.
Per-shot/cast external refs, mask files, and unsupported multi-ref plans are
rejected rather than silently left pointing to unuploaded files.

## Required deployment inclusion (not performed here)

Include this repository's `custom_nodes/openjutsu_assets/` directory under
`ComfyUI/custom_nodes/openjutsu_assets/` in the build **in addition to** the
pinned BFS/custom nodes/models. Do not deploy an unmodified packaged graph with
asset IDs embedded in `plan`. No remote build or deployment was done by this story.

The v2 backend must replace the bridge's `core/ASSET` inputs with filenames and
materialize their bytes under the ComfyUI input directory. The bridge checks
that each resolved filename exists inside that directory, rejects traversal,
absolute paths, unresolved dictionaries, URLs and symlink escapes, then emits
the exact relative filenames BFS resolves. It does not download URLs, load
credentials, or guess asset-ID filesystem layouts.

Set `COMFY_SDK_ASSET_BRIDGE=openjutsu-v1` only when intentionally targeting a
deployment built with this bridge and a compatible materialization contract.
Without that explicit configuration, the adapter fails before uploads. This
flag is an operator assertion, **not** deployment attestation. Hosted provider
materialization, node registration, build packaging, model availability, paid
render correctness, media/audio quality and latency remain unverified. If a
backend returns filenames that are not materialized in the input root, the
bridge fails closed; do not weaken the path checks to make it pass.

## Submission/recovery

`sdk_outputs/submission.json` durably stores a random stable key, input/graph
fingerprint, endpoint hash, phase and provider ID. Atomic replace plus file and
directory fsync occurs before submission, and immediately after the returned ID,
before polling/downloading. Upload failures retain `prepared` and may retry with
the same key. Once `submitting` is persisted, **any** submit exception is treated
conservatively as unknown (even a definitive rejection); no automatic resubmit.
This intentionally favors duplicate-charge avoidance over availability.

Known IDs resume with GET/wait/download only. Unknown outcomes require manual
provider reconciliation; don't delete state or create a fresh key to retry.
The official v2 duplicate-key contract is 422 reject, not replay, and keys expire;
a stable key alone cannot recover a lost response. Changed inputs or endpoints
cannot reuse an old submission. A corrupt/unreadable state also fails closed.
Local POSIX flock serializes one output directory across processes, with an app
lock as well. This is not a distributed queue guarantee; shared remote/NFS
semantics, hostile filesystem mutation, resource limits and multi-host scheduling
are outside the tested scope. Keep job directories private and durable.

Exactly one MP4 from node 751 is required. Comparison outputs are ignored.
Provider filenames are checked but never used as destination paths; downloads
use a unique local temporary file and atomic replacement of `generated.mp4`.
Provider exception bodies/signed URLs never enter application status messages.
SDK input bytes are currently buffered in RAM; large-file memory limits and
media decoding validation are separate hardening work.

## Evidence boundary

`tests/test_sdk_protocol.py` uses the real installed SDK against an ephemeral
127.0.0.1 HTTP fixture and synthetic bytes only. It exercises multipart uploads,
submit bodies, stable headers, immediate ID persistence, poll/download, response
loss, restart-like known-ID recovery, duplicate serialization, and failure paths.
The fixture's explicit file-materialization simulator is a contract test, not a
real ComfyUI/provider execution. `tests/test_sdk_assets.py` checks the node without
GPU dependencies, planner validation, app input/audio wiring and error redaction.
Existing tests remain untouched. No credentials, provider uploads, inference,
model downloads or remote builds were used. See `docs/evidence/sdk-assets/`.
