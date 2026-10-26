# Public landing page v3 delivery

Date: 2026-10-26

## Scope

Built the separate public conversion surface at `/landing.html`, leaving the production workspace at `/` unchanged.

The page uses:

- the accepted v6b 16:9 keeper as the hero proof;
- one primary action: `Start a dry run`;
- a problem, workflow, feature, proof, rights, FAQ, and final-action structure;
- six purpose-built animated feature cards;
- the approved `landing-page-design` system;
- `design-to-motion` website rules for the feature cards only.

## Motion decisions

The real v6b footage is not decorated or altered. Feature-card stories act out their own jobs:

1. Source: a scan marker reads the take.
2. Reference: the authorized likeness enters its slot.
3. Rights: source, reference, and consent states activate.
4. Render: a pulse travels the MiniMax H3 graph.
5. Audio: waveform bars remain active while the PCM lock stays unchanged.
6. Review: source and final frames stay synchronized under one scan line.

Card entrances play once through `IntersectionObserver`. Stories run only while their cards are visible and stop off screen. `prefers-reduced-motion` renders the final static state.

## Local assets

- Manrope variable font: `app/web/fonts/manrope-latin-400-800.woff2`
- Font license: `app/web/fonts/manrope-OFL.txt`
- Social image: `app/web/images/recastroom-landing-social.jpg`
- Hero video: `app/web/media/recastroom-public-hero-16x9.mp4`
- Favicon: `app/web/favicon.svg`
- Legal page: `/legal.html`

There are no external page requests.

## Verification

```text
node --check app/web/landing.js
PASS

python -m compileall -q app tests
PASS

python -m pytest -q
120 passed, 1 warning
```

Browser verification:

- desktop viewport: 1280px;
- desktop horizontal overflow: 0 px;
- mobile viewport: 390px;
- mobile horizontal overflow after repair: 0 px;
- hero video ready state: 4;
- hero video duration: 23.8 seconds;
- six feature cards found;
- all six card entrances activated;
- zero browser console errors or warnings.

A mobile tagline overflow was found and fixed by preserving spaces between animated words.

## Live tunnel checks

All page-critical assets returned HTTP 200 through Cloudflare:

```text
/landing.html
/landing.css
/landing.js
/legal.html
/favicon.svg
/fonts/manrope-latin-400-800.woff2
/images/recastroom-landing-social.jpg
/media/recastroom-public-hero-16x9.mp4
```

## Evidence

- `desktop.png`
- `mobile.png`
- `browser_smoke.json`
- `SHA256SUMS`

## Boundary

This is the v3 public landing review build. It is not yet the final public deployment domain and does not replace the owner-gated public repository, demo, X post, or Typeform submission steps.
