# Readiness strip — 2026-10-24

## Scope

Add a Seriesmith-inspired live dependency strip to Openjutsu Studio without
changing execution behavior or claiming provider quality.

## UI

The home page now exposes six dependency states:

```text
Source
Primary reference
Rights
Workflow
Renderer
Execution
```

The strip distinguishes:

```text
ok / pending / checking / warning / blocked / unknown
```

Important truthful states include:

```text
Source: Selected · preflight pending
Source: Preflight passed
Source: Preflight warning
Rights: Permission recorded
Workflow: Custom graph pending validation
Renderer: Renderer disconnected
Renderer: SDK configured · reachability unchecked
Execution: Dry run · no AI inference
```

No percent, ETA, QC, or quality-score claim is introduced.

## Live dogfood

The dry-run app was started locally on port 8895. Initial state was captured in:

```text
docs/images/readiness-visual.png
```

Observed initial chips:

```text
Source: Not selected
Primary reference: Missing
Rights: Permission required
Workflow: Bundled graph ready
Renderer: Dry-run runner ready
Execution: Dry run · no AI inference
```

After selecting the synthetic source and primary reference and checking consent,
the exposed `window.StudioUI.getReadiness()` returned:

```text
Source: pending / Selected · preflight pending
Primary reference: pending / Selected
Rights: ok / Permission recorded
Workflow: ok / Bundled graph ready
Renderer: ok / Dry-run runner ready
Execution: ok / Dry run · no AI inference
```

Updated viewport:

```text
docs/images/readiness-ready.png
```

## Verification

```text
node --check app/web/studio.js
python -m pytest -q
112 passed
```

The warning is the existing FastAPI/TestClient deprecation notice.
