# Release status

RecastRoom Studio `0.1.1` is a local-first production preview for one-person,
continuous-shot dialogue recasting.

## Current capabilities

- FastAPI studio and static web workspace
- Local ComfyUI API runner
- Official Comfy SDK adapter
- Whisper-compatible word timing
- Rights attestation gate
- Media preflight and review artifacts
- Public overview and local review tools
- Public media kit with hero, showreel, teaser, and proof assets
- Automated application, API, workflow, and browser tests

## Verification

The current local suite reports:

```text
393 passed
1 known Starlette deprecation warning
```

CI runs the same suite on Python 3.11 and 3.12.

## Execution boundary

- Local ComfyUI execution is supported.
- Official Comfy SDK execution is implemented and fails closed until
  `COMFY_API_KEY` and `COMFY_BASE_URL` are configured.
- CPU dry runs do not load model weights and are not H3 inference.

## Scope

The bundled graph is tuned for one performer in a continuous dialogue shot.
Multi-person casting, arbitrary multi-shot scenes, and broad VFX lanes remain
roadmap work rather than claimed production features.
