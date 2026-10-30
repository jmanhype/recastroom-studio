# Required setup wizard evidence — 2026-10-30

`wizard.png` captures the fresh-browser required setup overlay before any studio
control is usable. The overlay has four steps:

1. intended execution connection,
2. guided versus advanced studio,
3. solo versus local review handoff,
4. ready state.

Escape and backdrop clicks do not dismiss the first-run overlay. The only exit is
the final **Open the studio** action, which records local setup preferences.
Review handoff is intentionally local-first: no remote session, viewer, account,
or media upload is created. A named reviewer is attributed in take-review notes.

Focused UI/browser checks passed **49 tests** with the known Starlette/httpx
warning (`focused.log`).
