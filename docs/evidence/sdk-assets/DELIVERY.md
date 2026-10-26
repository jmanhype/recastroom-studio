# OJ-krar unpaid SDK asset delivery

Base: `98de3ff`. Scope: SDK adapter/application SDK branch, SDK floor, explicit
custom-node bridge, two new test modules and deployment/evidence documentation.
No existing tests, static workflow, legacy guard, CLI or frontend changed.

## Measured evidence

- Full suite: `89 passed, 1 warning in 25.05s` (`pytest.txt`). Warning is existing
  Starlette/httpx deprecation, not a test failure.
- Interpreter: root checkout `.venv/bin/python`, official installed comfy-sdk
  0.5.0; `PYTHONPATH=src` selects this story's source.
- Focused suite command and result are in `focused.txt` (constructor contract,
  new asset/bridge tests and actual-SDK localhost protocol tests).
- `git diff --check` exited 0.
- Canonical workflow SHA256 unchanged against `git show HEAD:<path>`:
  `06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21`.
- Inspected public BFS `bfs_shot_loop.py` at commit
  `a93cea17a9f4315110f9c66a29735829e956a9cc`; downloaded source SHA256
  `663541cd85225f6fc4f14b61fb00f4672a8e9330687ebcb3e170988c8c80824d`.
  Exact source URL is linked in deployment documentation. No account-status
  file or credentials were read. No public source file is vendored by this patch.
- Scoped implementation/evidence hashes are in `SHA256SUMS.txt`.

## Acceptance evidence

1. Local shape/file validation precedes network; optional ref2 supported.
   Explicit core/ASSET filename widgets feed the tested bridge STRING output,
   not UUIDs inside plan text. The bridge requires files inside input root.
2. App manifest inputs and original-source finalization are checked by tests.
   Node 751 is deterministic; other/comparison output does not win. Filenames,
   symlink escapes and provider error redaction are checked. Canonical graph
   remains byte-identical; bound graph only adds bridge and rewires plan.
3. Durable stable key before submit; ID before first poll; restart-like recovery
   makes zero extra POSTs. Lost response blocks further submits. Pre-submit
   upload failure preserves prepared phase/key. Local duplicates submit once.
4. Real SDK multipart/POST/GET/download protocol runs on ephemeral 127.0.0.1
   only. Synthetic source/ref1/ref2 bytes and outputs; no inference. Explicit
   materialization simulator is labelled as such, not hidden mock evidence.
5. Existing constructor tests retained, SDK floor raised to 0.5.0, deployment
   inclusion and unproven hosted stages documented. No production-ready claim.

## Remaining boundaries

Hosted file materialization, registered bridge availability, actual BFS/model
execution and output quality remain unproven. Default fails before uploads
unless `COMFY_SDK_ASSET_BRIDGE=openjutsu-v1` is intentionally configured. That
flag is an operator assertion, not an attestation. Runtime bridge checks still
fail on unresolved/nonexistent/out-of-root inputs. Build inclusion has NOT been
performed; no upload, paid call, GPU/model download, commit, push or remote build.

Graph coverage came from the parent: generation 2026-10-18T04:17:38Z,
openjutsu-studio-OJ-inuo, exact SDK/app paths missing. Exact-checkout source
fallback used; no graph-negative/exhaustive conclusions.
