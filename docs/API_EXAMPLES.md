# API examples

Start from a checkout with the `docs/QUICKSTART.md` commands, then use the
locally running app:

```bash
export RECASTROOM_WORKFLOW="$PWD/workflows/openjutsu_h3_lipsync_local.json"
uvicorn app.main:app --port 8768
```

## Health

```bash
curl --fail http://127.0.0.1:8768/api/health
```

```json
{
  "ok": true,
  "workflow": "openjutsu_h3_lipsync_local.json",
  "workflow_exists": true,
  "backend": "legacy"
}
```

## Home page

```bash
curl --fail http://127.0.0.1:8768/ >/dev/null
```

The response is the HTML UI shown in `docs/images/app-landing.png`.

## Workflow catalog

```bash
curl --fail http://127.0.0.1:8768/api/workflows
```

The response identifies the production Recast Room workflow, the advanced custom
graph path, and concept lanes that are intentionally unavailable in this release.

## Archive.org source discovery

RecastRoom can discover candidate source footage from allowlisted Archive.org
video collections without an API key:

```bash
curl --fail --get http://127.0.0.1:8768/api/archive/sources \
  --data-urlencode "query=driving" \
  --data-urlencode "collection=prelinger" \
  --data-urlencode "limit=12"
```

The endpoint returns titles, Archive identifiers, explicit license URLs where
available, and a rights verdict. Items without an explicit public-domain license
are marked `review_required: true`; discovery never bypasses the preparation
operator attestation.

## Prepare a workflow

Prepare is local and does not contact a model service. Use media that you own or
are licensed to modify:

```bash
curl --fail http://127.0.0.1:8768/api/prepare \
  -F "source=@source.mp4;type=video/mp4" \
  -F "reference_1=@reference-1.png;type=image/png" \
  -F "reference_2=@reference-2.png;type=image/png" \
  -F "words=@words.json;type=application/json" \
  -F "identity=the authorized replacement performer shown in the references" \
  -F "rights_attested=true" \
  -F "seed=49"
```

The response contains the preflight scene report, a job ID, public filenames,
and two download URLs:

```json
{
  "job_id": "example-job-id",
  "scene": {"recommended": true},
  "manifest": {"rights_attested": true, "seed": 49},
  "workflow_url": "/api/jobs/example-job-id/workflow",
  "prompt_url": "/api/jobs/example-job-id/prompt"
}
```

Omitting `rights_attested=true` returns HTTP 422. The API deliberately returns
filenames rather than checkout-local absolute paths.

To replace the bundled Recast Room template for one job, add a C1-compatible
Comfy API graph:

```bash
  -F "workflow=@custom-recast.json;type=application/json"
```

Custom graphs must retain the required planner, conditioning, timed-audio,
exact-audio-lock, and output nodes. Invalid graphs fail preparation with HTTP 422;
rights, source routing, and review behavior remain enforceable.

## Download prepared artifacts

```bash
curl --fail http://127.0.0.1:8768/api/jobs/example-job-id/workflow > workflow.json
curl --fail http://127.0.0.1:8768/api/jobs/example-job-id/prompt > prompt.txt
```

`workflow.json` is ComfyUI API format and can be inspected or queued in a
compatible local runtime.

## Generation endpoints

Generation requires a local ComfyUI runtime; do not call it as part of the
credential-free release smoke test.

```bash
curl --fail -X POST http://127.0.0.1:8768/api/jobs/example-job-id/run
curl --fail http://127.0.0.1:8768/api/jobs/example-job-id/status
curl --fail http://127.0.0.1:8768/api/jobs/example-job-id/artifacts/final > final.mp4
```
