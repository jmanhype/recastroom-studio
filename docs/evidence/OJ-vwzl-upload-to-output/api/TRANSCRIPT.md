# OJ-vwzl API E2E transcript

## Commands

```sh
cd <workspace>
python tools/e2e_smoke.py --output-dir <output-dir> --dry-port 8913 --sdk-port 8914
```

The driver starts isolated Uvicorn processes with `OPENJUTSU_BACKEND=dry_run` and `OPENJUTSU_BACKEND=sdk`, and removes `COMFY_API_KEY`, `OPENJUTSU_COMFY_API_KEY`, and `COMFY_BASE_URL` from each child process environment without printing values.

## Dry-run job

- health backend: `dry_run`
- missing-rights response: `422`
- invalid-rights response: `422`
- prepared job: `186c06e80582`
- terminal state: `complete`
- prompt ID: `dry-run-d3219c17dac0700c`

| artifact | bytes | SHA-256 | HTTP |
|---|---:|---|---:|
| `generated` | 98859 | `6fecc6baff45fa6bc210e3864d15a99e663f7215f97b5a3c8f4fc7d91c51165f` | 200 |
| `final` | 203213 | `9e98ca0fa3852293b59b77b36f684b83ff7e19c8fcc5453672374a670813dd5c` | 200 |
| `side_by_side` | 778832 | `eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9` | 200 |

## SDK fail-closed job

- health backend: `sdk`
- prepared job: `c8ef2f765049`
- terminal state: `error`
- error code: `missing_comfy_api_key`
