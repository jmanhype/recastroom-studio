# Local reviewer trial deployment

RecastRoom Studio's default reviewer deployment is intentionally **local and
loopback-only**. It is a reviewer trial, not a public hosting path. The local
trial uses the deterministic `dry_run` backend, bundled synthetic fixtures, no
credential, no GPU, and no Comfy cloud request.

## Security boundary

- The supplied workflow binds Uvicorn to `127.0.0.1` only.
- There is **no public URL by default**. Public hosting, social publication,
  repository pushing, and Comfy Developer Platform use remain owner-gated.
- The FastAPI app has no authentication or built-in per-user rate limiter.
  Loopback isolation is therefore the required compensating boundary for this
  trial. Do not bind `0.0.0.0`, expose a port through a router, or forward it
  over an unauthenticated tunnel.
- An owner may share a trial only through a separately authenticated VPN or
  private-network boundary. That owner-controlled boundary must add per-person
  authentication, request and upload limits, logging, and review-period data
  deletion before any reviewer connection. A recommended initial proxy posture
  is at most 60 requests per minute per reviewer and at most 100 MiB per upload;
  the owner remains responsible for the actual proxy policy. No such public or
  VPN configuration is created by this repository.

## Architecture

```text
reviewer browser → http://127.0.0.1:<port>
  → FastAPI static web UI
  → ffprobe source preflight
  → explicit operator-attestation gate
  → job/workflow/prompt storage under RECASTROOM_DATA_DIR
  → deterministic dry_run backend
  → status endpoint and reviewer artifacts
```

The dry-run backend validates prepared upload routing, records queued/uploading/
generating/downloading/complete states, copies the synthetic source as its
deterministic output, and exercises source-audio restoration and side-by-side
review rendering. It does not perform model inference and must not be described
as a MiniMax H3 generation result.

## Operator attestation gate

`POST /api/prepare` rejects missing or invalid `rights_attested` input with
HTTP 422 before a job is created. A valid preparation records
`rights_attested: true` in the manifest. Dry-run, legacy ComfyUI, and official
SDK execution recheck that manifest before generation; there is no unattested
generation path through this application. Attestation is a legal representation
by the uploader, not automated provenance proof. Reviewers must follow
[`RIGHTS.md`](../RIGHTS.md).

## Storage lifetime

- The repeatable script creates a temporary `RECASTROOM_DATA_DIR` beneath its
  evidence directory and deletes that directory when the probes finish.
- The script retains only sanitized machine-readable evidence and a sanitized
  server log under `docs/evidence/OJ-2t3g-local-trial/`; it does not retain the
  uploaded fixture or generated videos.
- A manually started server writes uploads and job artifacts under
  `RECASTROOM_DATA_DIR` (default `work/`). There is no automatic retention TTL:
  the host owner must delete that directory immediately after the review.
- Reviewers should not upload private or third-party media to a shared host.

## Environment variables

| Variable | Local-trial value | Purpose |
|---|---|---|
| `RECASTROOM_BACKEND` | `dry_run` | Required safe backend; set automatically by the script. |
| `RECASTROOM_DATA_DIR` | script-owned temporary directory | Isolates uploads/jobs and permits cleanup. Set automatically. |
| `RECASTROOM_WORKFLOW` | optional | Overrides the bundled workflow path. Defaults to `workflows/openjutsu_h3_lipsync_local.json`. |
| `RECASTROOM_FFMPEG` | optional | Overrides the `ffmpeg` executable for dry-run media packaging. |
| `RECASTROOM_FFPROBE` | optional | Overrides the `ffprobe` executable for preflight. |
| `RECASTROOM_WHISPER` | optional | Overrides the Whisper executable; unused by the bundled fixture probe. |
| `RECASTROOM_COMFY_URL` | leave unset | Irrelevant to dry run; never point the local trial at another machine. |
| `COMFY_API_KEY`, `RECASTROOM_COMFY_API_KEY`, `COMFY_BASE_URL` | forbidden | Removed from the server child environment by the script. If an owner later runs SDK mode, values belong only in that owner's host environment/process secret store, never source, docs, logs, or evidence. |

Unknown backend values fail closed during settings loading. SDK mode additionally
fails closed before network access if its key or deployment URL is missing.

## Repeatable deployment and probes

From a repository checkout with Python 3.10+, `ffmpeg`, and `ffprobe`:

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install ".[dev]"
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/python scripts/local_trial.py --host 127.0.0.1 --port 8890
```

The command refuses non-loopback hosts, starts an isolated Uvicorn process,
waits for readiness, and performs real HTTP probes against
`http://127.0.0.1:8890` for:

1. `/api/health` — HTTP 200, `backend=dry_run`, workflow present;
2. `/` — HTTP 200 HTML containing the operator attestation control;
3. `/api/prepare` without rights — HTTP 422 rejection;
4. `/api/prepare` with attestation — HTTP 200 and a job ID;
5. `/api/jobs/{id}/run` and `/api/jobs/{id}/status` — queued through complete.

It writes `receipt.json`, `server.log`, and `secret-scan.json` under
`docs/evidence/OJ-2t3g-local-trial/`. The scan covers source, documentation,
bundled fixture artifacts, workflow, generated artifacts, and the server log for
credential-shaped values, credential-like filenames, absolute user paths, private network
addresses, and raw credential assignments. A non-empty target directory is
refused so prior evidence cannot be silently replaced.

For a longer manual UI review after running the automated probes, start the same
loopback application explicitly and delete its data directory afterward:

```bash
RECASTROOM_BACKEND=dry_run \
RECASTROOM_DATA_DIR="$PWD/work/local-review" \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8890
```

Stop Uvicorn and delete `work/local-review` only after confirming that the path
is the intended review directory. Prefer moving it to a quarantine name or
deleting it through a trash-capable file manager on a shared host. Public
hosting is not part of this workflow.
