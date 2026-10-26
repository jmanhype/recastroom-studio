## Implementation Evidence (DELIVERED)

Summary: Uncommitted unpaid SDK asset binding and durable submission recovery delivered for parent integration and independent PM review.

Commit SHA: No implementation commit: explicitly prohibited by assignment. Base HEAD only: 98de3ff703f584755d38c01cb6bb66fc997f0707. This base SHA is NOT evidence that the patch has been committed. Scoped SHA256SUMS.txt identifies the delivered disk artifacts.

### CI/Test Results
- Commands run:
  - PYTHONPATH=src <checkout>/.venv/bin/python -m pytest -q
  - PYTHONPATH=src <checkout>/.venv/bin/python -m pytest tests/test_comfy_sdk_runner.py tests/test_sdk_assets.py tests/test_sdk_protocol.py -q
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
