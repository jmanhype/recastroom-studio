# Clean package install and launch — 2026-10-25

## Input package

```text
source commit:          8a5f376efa1e7a9699582a7e4c97da69754eb192
filtered content SHA:   b65b7d23366ddf75c20697feaff331867ca71f43c8c91f8d8cf9a70e6bd5105f
public-package.zip:     926bc1bbac2fd2186f03f9f70a7ed81ed6aa9075e0fd9209034d3060559a3a4a
```

The archive was unpacked into a new directory and installed into a new Python
3.11 virtual environment. No existing repository virtual environment was used.

## Install and tests

```text
recastroom --version:  0.1.1
pip check:             no broken requirements
pytest:                113 passed, 1 warning
```

The warning is the known FastAPI/TestClient deprecation warning from the
installed test-client dependency; it is not a RecastRoom runtime failure.

## Fresh package launch

The clean installed package launched with:

```text
RECASTROOM_BACKEND=dry_run
uvicorn app.main:app --host 127.0.0.1 --port 8901
```

Observed:

```text
health:               ok=true
bundled workflow:     present
backend:              dry_run
renderer_ready:       true
home title:           RecastRoom Studio
```

The server was stopped after the probes. No credential, GPU, cloud job, or
model inference was used.

## Boundary

This proves the audited 8a5f376 package installs and launches from a fresh
Python environment. It does not replace the owner’s final clean-install run on
the exact public commit after publication, and it does not clear live Comfy
Developer Platform execution, public repository/demo, social, Typeform, or
rights/model-license blockers.
