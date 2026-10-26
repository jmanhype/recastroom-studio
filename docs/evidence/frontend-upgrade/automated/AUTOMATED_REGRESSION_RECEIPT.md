# OJ-yf2c automated deterministic regression receipt

Date: 2026-10-18

Scope: `tests/test_frontend_regression.py` only. This receipt does not claim
browser E2E completion, screenshots, keyboard operation, reduced-motion behavior,
or public deployment safety. The parent capstone owns browser evidence and final
delivery.

## Environment and identity

- Branch: `story/OJ-yf2c`
- Starting base: `2b22504`
- Interpreter: repository `.venv`, Python 3.11.11
- pytest: 9.1.1, pluggy 1.7.0
- Import path: `PYTHONPATH=src`
- Backend under test: real FastAPI application configured to `dry_run`
- New test file: `tests/test_frontend_regression.py`
- New test-file SHA-256: `92aad918dd7ee1b980df5b8238332dcd7050932b5a9eae73094c2ceeac2cf502`
- New test-file LOC: 317

Synthetic fixture hashes:

- `tests/fixtures/synthetic_source.mp4`: `6fecc6baff45fa6bc210e3864d15a99e663f7215f97b5a3c8f4fc7d91c51165f`
- `tests/fixtures/synthetic_reference.png`: `0f5f0bc67819583b824c3e2d9900225e89cf9b0223108a1b472e444da8b9e79a`
- `tests/fixtures/word_timings.json`: `7943902959ac0aba6b775857a964bbdef11bc89e354847ccf5ab02bfe9439d5f`

## Official focused run 1

Executed command (private repository prefix replaced by `<repo>`):

```sh
PYTHONPATH=src <repo>/.venv/bin/python -m pytest tests/test_frontend_regression.py
```

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.11, pytest-9.1.1, pluggy-1.7.0
rootdir: <repo>
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 4 items

tests/test_frontend_regression.py ....                                   [100%]

=============================== warnings summary ===============================
<repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1
  <repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/captured_warnings.html
========================= 4 passed, 1 warning in 1.87s =========================
```

## Official full run 1

Executed command (private repository prefix replaced by `<repo>`):

```sh
PYTHONPATH=src <repo>/.venv/bin/python -m pytest
```

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.11, pytest-9.1.1, pluggy-1.7.0
rootdir: <repo>
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
collected 45 items

tests/test_app.py ...                                                    [  6%]
tests/test_app_e2e.py ...                                                [ 13%]
tests/test_comfy_sdk_runner.py ....                                      [ 22%]
tests/test_config.py ....                                                [ 31%]
tests/test_evidence.py ....                                              [ 40%]
tests/test_final_submission_gate.py ....                                 [ 48%]
tests/test_frontend_regression.py ....                                   [ 57%]
tests/test_local_trial.py ..                                             [ 62%]
tests/test_media.py .......                                              [ 77%]
tests/test_media_audio.py ...                                            [ 84%]
tests/test_profiles.py .                                                 [ 86%]
tests/test_release_tools.py ..                                           [ 91%]
tests/test_timing.py ..                                                  [ 95%]
tests/test_workflow.py ..                                                [100%]

=============================== warnings summary ===============================
<repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1
  <repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/captured_warnings.html
======================== 45 passed, 1 warning in 16.06s ========================
```

## Official focused run 2

Executed command (private repository prefix replaced by `<repo>`):

```sh
PYTHONPATH=src <repo>/.venv/bin/python -m pytest tests/test_frontend_regression.py
```

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.11, pytest-9.1.1, pluggy-1.7.0
rootdir: <repo>
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 4 items

tests/test_frontend_regression.py ....                                   [100%]

=============================== warnings summary ===============================
<repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1
  <repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/captured_warnings.html
========================= 4 passed, 1 warning in 2.21s =========================
```

## Official full run 2

Executed command (private repository prefix replaced by `<repo>`):

```sh
PYTHONPATH=src <repo>/.venv/bin/python -m pytest
```

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.11, pytest-9.1.1, pluggy-1.7.0
rootdir: <repo>
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
collected 45 items

tests/test_app.py ...                                                    [  6%]
tests/test_app_e2e.py ...                                                [ 13%]
tests/test_comfy_sdk_runner.py ....                                      [ 22%]
tests/test_config.py ....                                                [ 31%]
tests/test_evidence.py ....                                              [ 40%]
tests/test_final_submission_gate.py ....                                 [ 48%]
tests/test_frontend_regression.py ....                                   [ 57%]
tests/test_local_trial.py ..                                             [ 62%]
tests/test_media.py .......                                              [ 77%]
tests/test_media_audio.py ...                                            [ 84%]
tests/test_profiles.py .                                                 [ 86%]
tests/test_release_tools.py ..                                           [ 91%]
tests/test_timing.py ..                                                  [ 95%]
tests/test_workflow.py ..                                                [100%]

=============================== warnings summary ===============================
<repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1
  <repo>/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/captured_warnings.html
======================== 45 passed, 1 warning in 26.13s ========================
```

## Deterministic coverage boundary

1. Served HTML/JS/CSS checks cover required consent, media-change re-attestation,
   health-gated prepare/run controls, no-AI dry-run disclosure, complete-only
   artifact links, terminal-error and status-unavailable recovery copy, epoch/current
   stale-response guards, visible focus, and reduced-motion CSS suppression.
2. Real `TestClient` calls cover missing/invalid consent, persisted upload of all
   three fixtures, prepare URLs, run/status, and all completed artifact downloads.
   No fetch or backend method is mocked.
3. A labeled isolated fault removes a prepared job's source and verifies terminal
   error, retry, no fabricated artifacts, and fresh-job recovery. It is not evidence
   of real provider behavior.
4. A labeled isolated active-status fixture verifies the duplicate-run 409 guard;
   unknown/malformed job IDs remain 404.

The frozen UI assertion seam is limited to `StudioUI.errorText` and
`StudioUI.getState`; historical mutable methods are asserted absent.

## Caveats and open finding

- The pre-edit full baseline was 41 passed. Both final full runs collected 45 and
  passed, preserving the 41 prior tests plus these four regressions.
- Static source assertions do not establish browser execution truth. Parent CUA
  evidence is required for real DOM interaction, keyboard/reduced-motion behavior,
  screenshots, and recovery under the browser-observed failure.
- Parent CUA reported a real transient status-file read/write race: `GET status`
  returned HTTP 500 with `JSONDecodeError` while `_set_status` was writing
  `status.json`; the UI's Check-status control subsequently recovered. This
  deterministic suite did not reproduce that race and does not claim it fixed.
  Production changes are intentionally out of scope for OJ-yf2c.
- No browser driver, mock backend/fetch, mandatory new dependency, GPU/API/cloud
  inference, or push operation was introduced.
