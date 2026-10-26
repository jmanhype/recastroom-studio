# Motion-video repo sweep

Date: 2026-10-25

## Inputs

| Repository | Commit | License | Use |
|---|---|---|---|
| `echris6/motion-video-kit` | `e4b1c0004080fe6a0deb883631bad5eba1e5f339` | MIT | Measured Gauntlet, motion grammar, loudness and frozen-time checks |
| `zhuyansen/awesome-claude-video-skills` | `c7bcf25b3a34e1e1d95d929336d7dadf9ba0f159` | See repository license | Machine-readable catalog of 347 agent video repos and a 16-repo end-to-end test |
| `Tejashmakwana/motionmaxxing` | `8c8ec0f2a6f6c9a0da15cd24f7b1298ab298368c` | Apache-2.0 | Render gates G0–G5, anti-page-chrome lint, motion law review |
| `AbubakrChan/product-launch-motion` | `edbfb105382f21507bad895d8b5f6e0faa67487c` | MIT | Candidate for a future one-shape/music-first launch film |
| `iart-ai/motion-skills` | `238dfc55aac123d4649be39adfe58c43193ca349` | MIT | Candidate pack for reusable motion/design sub-skills |
| `lemomo-ai/lemo-opuscar` | `413a6bd6d78ebd3bdd5abaec9538a26867f890df` | MIT code/docs; demo media CC BY 4.0 with exclusions | Style library for future lanes and contest-demo styling |

## What was adopted now

The useful split was:

- **HyperFrames** remains the deterministic renderer.
- **Motion Video Kit** supplies the production Gauntlet and measurable checks.
- **MotionMaxxing** supplies stricter anti-slop gates and the strongest page-chrome critique.

Applied to RecastRoom v6b:

1. Removed persistent footer/HUD chrome.
2. Removed the kicker above the recast headline.
3. Centered headlines to avoid left-anchored deck layouts.
4. Removed the frozen 1.225s source tail and let the real source end at 5.875s.
5. Added a persistent comparison scan line.
6. Added motion to rights cards and the CTA copy.
7. Reduced the resolved end hold to 1.20s.

## v6b measured result

```text
HyperFrames:       ok; 0 lint/runtime/layout/contrast errors; 0 craft warnings
MotionMaxxing G0:  PASS
MotionMaxxing G2:  PASS
MotionMaxxing G3:  PASS, end hold 1.20s
MotionMaxxing G5:  PASS
Motion Video Kit:  1.7s near-frozen total, mostly final CTA
Audio:             -13.8 LUFS, 3.9 LU range, -1.5 dBTP
Duration:          23.800s, 1920x1080, 714 frames
SHA-256:           83b810dd404113d045ac01e76e3a802353eaa9d481a5bc032c5000ddeb0350b3
```

Local artifact:

```text
work/recastroom-hook/v5/hyperframes/recastroom-locked-performance-v6b-16x9.mp4
```

## Why the other strong repos were not swapped in now

- **Product Launch Motion** is excellent for a music-first, one-shape UI morph film. RecastRoom's strongest asset is a real source-to-recast performance, so replacing the whole architecture now would discard the verified C1 proof.
- **iart Motion Skills** is a broad 56-skill library. It is more useful for future reusable lanes (kinetic type, charts, vertical social) than for changing this already-locked launch cut.
- The Awesome list's own end-to-end test warns that HyperFrames is slow, but speed was acceptable here and determinism/QC mattered more.

## Lemo-Opuscar assessment

The repository was cloned and its style catalog was regenerated successfully:

```text
styles:       59
categories:   11
catalog:      styleboard/catalog.json
total video:  56 minutes listed
```

The local clone remains clean. The style-board build was run only as validation and its generated HTML was restored after the shallow clone correctly omitted release-hosted demo MP4s.

Candidate frame sheet:

```text
work/recastroom-hook/v5/gauntlet/lemo-opuscar/candidate-styles.jpg
SHA-256: 70dc80808fdb5c4c4f90804de5567cf93c7669e0993cb8e7e355d6d6322f2506
```

### Best fits for RecastRoom

| Style | Why it fits | Use now? |
|---|---|---|
| **Dark Tech Keynote** | Near-black stage, hairline grid, one accent, product UI as protagonist, light reveals, snap-grid precision | Best guide for the longer two-minute contest demo; v6b already shares much of this grammar |
| **Visual Investigation** | Multiple evidence sources on one timeline, annotation discipline, measured claims | Strong model for a vertical evidence-cut derivative and technical credibility scenes |
| **Sports Telestrator** | Freeze, draw, split, and track motion through a moment | Useful for a source-versus-recast motion breakdown, but risks making the promo feel like sports analysis |
| **Exploded Teardown** | Layers separate, labels land on real parts, then reassemble | Good future metaphor for the pipeline—source, mask, reference, render, review—but too much machinery for the 24-second hook |
| **Archive Light Table** | Sources under examination, loupe/detail framing | Good for a “provenance mode” product tour, not the fast social hook |

Styles considered and rejected for this lane:

- **Glass Product Render**: excellent for a physical hero object, but RecastRoom’s hero is real footage plus a workflow, not a glass object.
- **Sci-fi Hologram HUD**: visually strong but risks generic sci-fi chrome and works against the honest, attestation-gated positioning.
- **Swiss Motion Graphics**: great for a pure graphic identity film, but it would fight the cinematic source footage.

### Decision

Do not replace RecastRoom v6b. It finally has the right balance of real footage, clear proof, motion, and platform-ready pacing.

Use Lemo-Opuscar next in two bounded places:

1. **Two-minute contest demo:** borrow Dark Tech Keynote’s light reveal, one-accent logic, and snap-grid precision for product/UI scenes.
2. **Vertical social derivative:** borrow Visual Investigation’s evidence-timeline grammar to stack source/recast/proof in 9:16 without blind cropping.

## Local compatibility note

This machine's Homebrew FFmpeg lacks the `drawtext` filter. The local MotionMaxxing `look.py` clone was patched only to omit timestamp overlays when `drawtext` is unavailable; video analysis itself is unchanged.
