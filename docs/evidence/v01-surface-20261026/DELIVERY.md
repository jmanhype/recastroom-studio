# v0.1 public-surface completion

Date: 2026-10-26

## Scope

Completed the low-risk, high-judge-impact additions to `/landing.html`:

1. visible deterministic dry-run badge;
2. runtime and cost disclosure for dry run, local ComfyUI, and official SDK;
3. setup diagnostics;
4. focused comparison table;
5. staged v0.2 through v0.5 roadmap.

The production workspace and generation workflow were not expanded before publication.

## Runtime disclosure

| Mode | Provider charge | Credentials | Inference |
|---|---|---:|---:|
| Dry run | None | None | None |
| Local ComfyUI | No RecastRoom fee | Local endpoint | Operator hardware |
| Official Comfy SDK | Deployment usage | Owner configured | Comfy deployment |

## Browser verification

```text
Desktop width:                 1280px
Desktop horizontal overflow:  0px
Dry-run badge present:        true
Runtime cards:                3
Setup cards:                  4
Comparison rows:              6
Gallery videos:               3
Roadmap cards:                4

Mobile width:                  390px
Mobile horizontal overflow:   0px
Comparison scroll width:       768px inside an owned scroll container
Comparison visible width:      356px
Console errors/warnings:       0
```

The comparison table scrolls inside its own container on mobile; it does not inflate the page layout viewport.

## Roadmap boundary

`docs/ROADMAP.md` now stages:

- v0.1: focused contest release;
- v0.2: production recasting;
- v0.3: studio surface;
- v0.4: developer platform;
- v0.5: hosted try mode.

v0.2 through v0.5 remain behind explicit promotion gates. They are not allowed to displace the v0.1 public repository, demo, social post, Typeform, rights clearance, or clean-checkout gates.

## Evidence

- `desktop.png`
- `mobile.png`
- `browser-check.json`
- `SHA256SUMS`
