# OJ-krar bounded annotation rework

Base commit: `147a748`. Changes intentionally left uncommitted for parent review.

Added complete parameter and return annotations to `validate_inputs`,
`bind_graph`, `OpenJutsuAssetPlan.INPUT_TYPES`, and `OpenJutsuAssetPlan.bind`.
Graph, plan, byte snapshots and ComfyUI widget schema have explicit aliases.
The installed official SDK exports `Comfy` and `Workflow`; these are imported
only under TYPE_CHECKING, preserving lazy runtime SDK availability. The binding
input dictionary annotation permits both serialized plan text and asset objects.
No execution branch, file validation, network call, default or graph field changed.

Verification (root checkout .venv Python, this worktree PYTHONPATH=src):

- `python -m pytest tests/test_comfy_sdk_runner.py tests/test_sdk_assets.py tests/test_sdk_protocol.py -q`:
  **30 passed in 6.80s**, `review-fix-focused.txt`.
- `python -m pytest -q`: **89 passed, 1 warning in 24.07s**,
  `review-fix-full.txt`. Existing Starlette/httpx deprecation warning only.
- `git diff --check`: passed.
- Updated changed-source hashes and added these rework artifacts to SHA256SUMS.txt.

No commit, push, merge, remote upload, paid call or model execution performed.
Original hosted-materialization limitations remain unchanged.
