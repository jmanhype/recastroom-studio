# OJ-vwzl — hosted upload-to-output execution evidence

## Boundary

- Source commit under test: `444e682` on the merged release-candidate tree
- Clean detached worktree: `<workspace>`
- Backend for the complete path: `OPENJUTSU_BACKEND=dry_run`
- Credential use: none. The API driver removes `COMFY_API_KEY`,
  `OPENJUTSU_COMFY_API_KEY`, and `COMFY_BASE_URL` from both child-process
  environments without reading or printing their values. The browser server is
  launched with the same three variables explicitly unset.
- GPU/compute use: none. `dry_run` deliberately does not claim MiniMax H3
  inference; it proves backend routing and artifact plumbing.

## Full test and API E2E

Commands:

```sh
cd <workspace>
python -m pytest -q
python -m pip check
mkdir <output-dir>
python tools/e2e_smoke.py \
  --output-dir <output-dir> \
  --dry-port 8897 --sdk-port 8898
```

Results:

```text
25 passed, 1 warning in 9.57s
No broken requirements found
{"ok": true, "receipt": "<output-dir>/api/receipt.json"}
```

The API driver exercised health, synthetic source/reference/word-timing upload,
ffprobe preflight, rights handling, workflow/prompt preparation, queue routing,
status polling, three artifact downloads, source-audio restoration, and
side-by-side construction.

Observed HTTP/status results:

- missing rights attestation → `422`, `Rights attestation is required.`
- invalid rights value → `422`, FastAPI `bool_parsing`
- health → `200`, backend `dry_run`
- prepared job `186c06e80582` → `200`, scene recommended, rights attested
- run → `200`, state `queued`
- terminal status → `complete`, backend `dry_run`
- generated/final/side-by-side downloads → `200`
- isolated SDK job `c8ef2f765049` → terminal `error`, machine-readable
  `missing_comfy_api_key`

The complete request/response sequence and status observations are in
`api/receipt.json`; the concise command transcript is in `api/TRANSCRIPT.md`.

## Browser E2E

The browser run used the same clean worktree and a separately launched
credential-sanitized Uvicorn process:

```sh
cd <workspace>
env -u COMFY_API_KEY -u OPENJUTSU_COMFY_API_KEY -u COMFY_BASE_URL \
  OPENJUTSU_BACKEND=dry_run PYTHONPATH="$PWD/src:$PWD" \
  python \
  -m uvicorn app.main:app --host 127.0.0.1 --port 8901
```

From another shell in the same clean worktree:

```sh
./tools/browser_smoke.sh http://127.0.0.1:8901 \
  <output-dir>/app-complete.png \
  <output-dir>/browser-transcript.txt
```

The real browser uploaded all three fixture inputs, filled identity and seed,
passed the required rights checkbox, prepared job `d71901bce6a6`, started it,
and polled to `complete`. It found one download link for each of `generated`,
`final`, and `side_by_side`. Browser network observations:

```text
POST /api/prepare                         200
POST /api/jobs/d71901bce6a6/run            200
GET  /api/jobs/d71901bce6a6/status         200
```

The full-page screenshot in `browser/app-complete.png` visually shows the
uploaded inputs, checked rights gate, complete dry-run status, and all three
download links. `browser/browser-transcript.txt` contains the complete
accessibility/network transcript.

## Media receipts

The authoritative SHA-256 and ffprobe records for every evidence artifact are in
`RECEIPTS.json`. Key output records are:

| Stable path | Bytes | SHA-256 | ffprobe summary |
|---|---:|---|---|
| `api/generated.mp4` | 98,859 | `6fecc6baff45fa6bc210e3864d15a99e663f7215f97b5a3c8f4fc7d91c51165f` | 640×240 H264, 24 fps, 2.041667 s, AAC mono |
| `api/final.mp4` | 203,213 | `9e98ca0fa3852293b59b77b36f684b83ff7e19c8fcc5453672374a670813dd5c` | 640×240 H264, 24 fps, 2.048 s, restored AAC 5.1 |
| `api/source_vs_final.mp4` | 778,832 | `eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9` | 1920×384 H264, 24 fps, 2.048 s, AAC 5.1 |
| `browser/app-complete.png` | 141,774 | `77d0095dd779cba960ba79615fb7b4d0a002d18756e513a9f28eb4f2a1210d45` | 1280×1569 PNG |
