# Archive.org source discovery — 2026-10-23

## Scope

Add key-free, rights-explicit Archive.org discovery to Openjutsu Studio.
Discovery surfaces candidate footage but never bypasses the preparation rights
attestation.

## Implementation

- `openjutsu.archive` searches the allowlisted Archive.org advancedsearch API.
- `GET /api/archive/sources` exposes key-free discovery.
- The source panel can search Prelinger without leaving the studio.
- Results distinguish explicit public-domain license evidence from items that
  still require rights review.
- Supported collections are limited to `prelinger`, `moviesandfilms`,
  `feature_films`, and `animationandcartoons`.

## Live proof

The local app was started with the bundled workflow and dry-run backend:

```text
PYTHONPATH=src \
OPENJUTSU_WORKFLOW="$PWD/workflows/openjutsu_h3_lipsync_local.json" \
OPENJUTSU_BACKEND=dry_run \
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8895
```

Browser action:

```text
open http://127.0.0.1:8895/
open “Find Archive.org footage”
query: going steady
click Search
```

Observed:

```text
6 results · archive.org · no API key
How Much Affection? — explicit public-domain license · HowMuchA1958
[Home movie: 098425 …] — rights review required · 098425
```

Uvicorn recorded:

```text
GET /api/archive/sources?query=going+steady&limit=6 200 OK
```

Screenshot:

```text
docs/images/archive-source-discovery.png
SHA-256 e86d99159852558b09fb803d56906b53d0d5656f14f0cf6f389ec480bd1f1151
```

## First candidate segment

The explicit-public-domain item `GoingSte1951` (*Going Steady?*, Coronet
Instructional Films) was used for a no-GPU import test:

```text
source: https://archive.org/download/GoingSte1951/GoingSte1951_512kb.mp4
segment: 60.000–65.875 seconds
output: work/archive-sources/GoingSte1951/going_steady_60s_5.875s.mp4
SHA-256 562f5c4bf00dc085aeccb5d5974fe42ba9d7b8e5ed95d79abdb626c46e499f35
```

Preflight result:

```text
duration: 5.875011s
resolution: 960×720
fps: 24
audio: present, stereo
risks: []
warnings: H3 grid padding/trimming + manual eyes/mouth/speaker/camera review
recommended: true
```

The segment is open in QuickTime for operator review. It remains a candidate;
no rights attestation or H3 generation has been recorded.

## Verification

```text
python -m compileall -q src/openjutsu/archive.py app/main.py
node --check app/web/studio.js
python -m pytest -q
111 passed, 1 warning
```

The warning is the existing FastAPI/TestClient deprecation notice.

## Boundary

No GPU runtime was started and no compute units were spent. Archive discovery
uses metadata and external item links only; media import and rights recording
remain separate, deliberate actions.
