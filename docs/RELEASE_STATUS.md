# Release status

RecastRoom Studio `0.3.5` is a local-first production preview for one-person,
continuous-shot dialogue recasting.

## Current capabilities

- FastAPI studio and static web workspace
- Default local preview mode
- Local ComfyUI runner
- Hosted Comfy adapter
- Whisper-compatible word timing
- Permission declaration gate
- Media preflight and review artifacts
- Public overview and local review tools
- Public media kit with hero, showreel, teaser, and proof assets
- Recorded official Comfy API SDK proof beside a visibly distinct no-inference preview
- Pre-spend hosted SDK configuration gate and sanitized recovery state
- Automated application, API, workflow, and browser tests

## Verification

The current local suite reports:

```text
408 passed
1 known Starlette deprecation warning
```

CI runs the same suite on Python 3.11 and 3.12.

## Execution boundary

- Local ComfyUI execution is supported after a compatible renderer is connected.
- Hosted Comfy execution is implemented and fails closed until a compatible
  deployment, credentials, and asset bridge are configured. Missing hosted
  configuration is rejected before a job enters `queued`.
- Preview mode does not load model weights and is not H3 inference.

## Scope

The bundled workflow is tuned for one performer in a continuous dialogue shot.
Multi-person casting, arbitrary multi-shot scenes, and broad VFX lanes remain
roadmap work rather than claimed production features.
