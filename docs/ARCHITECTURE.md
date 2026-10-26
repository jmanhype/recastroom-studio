# Architecture

```text
FastAPI web UI
  ↓
source preflight
  ↓
recorded operator attestation gate
  ↓
Whisper timing parser
  ↓
profile/prompt builder
  ↓
Comfy API workflow mutation
  ↓
local ComfyUI runner, official Comfy SDK runner, or deterministic dry-run runner
  ↓
output download
  ↓
audio restoration
  ↓
review artifact builder
```

## Modules

- `openjutsu.config` — environment and paths
- `openjutsu.scene` — ffprobe preflight and shot risk report
- `openjutsu.timing` — Whisper word-interval parser and frame scheduler
- `openjutsu.profiles` — identity and prompt contract for authorized replacement references
- `openjutsu.workflow` — Comfy API graph mutation
- `openjutsu.studio_catalog` — production, advanced, and concept workflow cards
- `openjutsu.archive` — key-free Archive.org source discovery with license metadata; metadata is not legal clearance
- `openjutsu.comfy_legacy` — self-hosted ComfyUI API runner
- `openjutsu.comfy_sdk_runner` — official Comfy Python SDK adapter
- `app.main` deterministic `dry_run` backend — credential-free routing and artifact test path
- `openjutsu.pipeline` — prepare jobs and manifests
- `openjutsu.media` — ffmpeg normalize/audio/review helpers

## App

The FastAPI app serves:

- `/` — web UI,
- `/api/health`,
- `/api/workflows`,
- `/api/archive/sources`,
- `/api/prepare`,
- `/api/jobs/{id}/workflow`,
- `/api/jobs/{id}/prompt`.

Set `OPENJUTSU_BACKEND=sdk` and `COMFY_BASE_URL` to execute through the official
Comfy SDK adapter. That adapter also requires `COMFY_API_KEY`; missing key or
deployment configuration raises `ComfySdkConfigurationError` before importing or
constructing the SDK client. The default `legacy` backend targets a self-hosted
ComfyUI HTTP API. `OPENJUTSU_BACKEND=dry_run` uses a committed synthetic fixture
to exercise backend selection, prepared-workflow routing, status transitions,
downloads, source-audio restoration, and side-by-side review generation without
credentials or GPU compute. Unknown backend values fail closed at configuration
load rather than falling back to another runner.
