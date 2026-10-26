# Tone.js sound-design lab delivery

Date: 2026-10-26

## Scope

Added a separate local `/sound-lab.html` workspace surface for the longer contest demo. It auditions four deterministic cue families:

1. brand pulse;
2. soft UI tick family;
3. source-to-recast signature reveal;
4. CTA bed that opens, holds, and resolves.

The lab intentionally does not generate or replace narration. Drama 3 Voice A remains the demo narrator.

## Implementation

- Route: `/sound-lab.html`
- UI: `app/web/sound-lab.html`
- Styling: `app/web/sound-lab.css`
- Audio engine: `app/web/sound-lab.js`
- Runtime: pinned local `Tone.js 15.1.22` MIT bundle
- Tests: `tests/test_sound_lab.py`
- Demo documentation: `docs/DEMO_PLAN.md`

The audio graph uses a `Tone.Limiter(-1)` output ceiling, a master volume control, and deterministic scheduled cues. There is no network audio fetch, no random variation, and no persistent local storage.

## Verification

```text
node --check app/web/sound-lab.js
PASS

python -m compileall -q app tests
PASS

python -m pytest -q
117 passed, 1 warning
```

The warning is the existing FastAPI/TestClient Starlette deprecation notice.

Live browser verification in the ChatGPT in-app browser:

- full 12.8-second sketch started and reached `Sketch finished · local Tone.js 15.1.22`;
- individual `Brand pulse` audition reported `Auditioning pulse cue`;
- play and preset controls remained enabled after the individual audition;
- no browser console errors or warnings;
- desktop viewport: 1440×1100;
- mobile viewport: 390×844;
- mobile horizontal overflow: 0 px.

## Evidence

- `desktop.png`
- `mobile.png`
- `hosted-with-video.png`
- `browser_smoke.json`
- `SHA256SUMS`

This browser pass proves interface/runtime behavior. It is not an EBU R128 measurement of the generated signal and does not replace the operator's listen test.
