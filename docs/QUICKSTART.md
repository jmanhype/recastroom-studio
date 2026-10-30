# Quickstart

This is the reviewer-facing path from a clean source checkout or unpacked release
archive. The default path is local preview mode: no credentials, no GPU, and no
AI inference. Generation is a separate step requiring ComfyUI or hosted Comfy.

## 0. Prerequisites

- Python 3.10 or newer
- Git for a source checkout
- `ffmpeg` and `ffprobe`
- optional local `whisper` for word timings

## 1. Install

The fastest path from a source checkout is:

```bash
./setup.sh
```

For the equivalent manual installation:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[dev]"
python -m pip check
python -m pytest -q
recastroom --version
```

The expected application version is `0.3.4`.

## 2. Confirm the bundled workflow

```bash
test -f workflows/recastroom_h3_workflow.json
python -m json.tool workflows/recastroom_h3_workflow.json >/dev/null
```

## 3. Start the app in preview mode

```bash
./run.sh
```

Open `http://127.0.0.1:8768`.

`run.sh` defaults to `RECASTROOM_BACKEND=dry_run`. It probes and prepares source
media, copies the prepared source, restores source audio for review, and builds
a paired comparison. It does not perform H3 inference or claim a recast.

If you start Uvicorn directly, set the same mode:

```bash
export RECASTROOM_BACKEND=dry_run
export RECASTROOM_WORKFLOW="$PWD/workflows/recastroom_h3_workflow.json"
uvicorn app.main:app --reload --port 8768
```

From another shell, confirm the local service:

```bash
curl --fail http://127.0.0.1:8768/api/health
curl --fail http://127.0.0.1:8768/ >/dev/null
```

The health response must include `"workflow_exists":true` and `"backend":"dry_run"`.

## 4. Inspect a clip

```bash
recastroom inspect source.mp4
```

Recommended input:

- one target speaker,
- 5–8 seconds,
- 24 fps or easy to normalize,
- visible eyes and mouth,
- stable camera,
- no hats or sunglasses,
- no overlapping speakers.

## 5. Word timings

```bash
recastroom words source.mp4 --json work/source.words.json
```

## 6. Prepare an H3 workflow

```bash
recastroom prepare \
  --attest-rights \
  --source source.mp4 \
  --reference-1 reference-1.png \
  --reference-2 reference-2.png \
  --words work/source.words.json \
  --output work/workflow.json
```

The generated `workflow.json` is in ComfyUI API format.

## 7. Queue to local ComfyUI

Start a ComfyUI runtime containing the models and custom nodes listed in
[`PIPELINE.md`](PIPELINE.md). Then restart the studio with:

```bash
RECASTROOM_BACKEND=legacy ./run.sh
```

Or queue a prepared workflow directly:

```bash
export RECASTROOM_COMFY_URL="http://127.0.0.1:8188"
recastroom run --attest-rights work/workflow.json
```

## 8. Hosted Comfy mode

Install and configure:

```bash
pip install comfy-sdk
export COMFY_API_KEY="comfyui-..."
export COMFY_BASE_URL="https://<your-deployment>"
```

The deployment must include the required RecastRoom bridge, custom nodes, and
models. The hosted adapter is in `src/openjutsu/comfy_sdk_runner.py`.

RecastRoom also requires the explicit asset-bridge opt-in:

```bash
export COMFY_SDK_ASSET_BRIDGE=openjutsu-v1
```

```bash
RECASTROOM_BACKEND=sdk ./run.sh
```

Both values are mandatory for this Developer Platform deployment mode. If either
is missing, job startup fails closed before network access with a JSON-serializable
`ComfySdkConfigurationError` (`missing_comfy_api_key` or `missing_comfy_base_url`).
