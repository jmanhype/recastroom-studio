# Elaya AI Design Skills assessment

Date: 2026-10-25

## Source

- Post: https://x.com/elayadesigns/status/2114049200749175174
- Author: Elaya, `@elayadesigns`
- Posted: 2026-10-24, 12:39 PM
- Embedded video metadata: 14.667 seconds, 1168×720.
- Repository: https://github.com/elayadesign/ai-design-skills
- Inspected commit: `a2735a3eaf092eaaffb6dc17df25de33ef3bd048`
- Repository license: MIT.
- GitHub metadata at inspection: 5,993 stars, 430 forks, default branch `main`.

Observed post metrics at inspection:

```text
Views:      487.1K
Replies:    183
Reposts:    536
Likes:      8,889
Bookmarks:  14,234
```

Bookmark-to-like ratio:

```text
14,234 / 8,889 = 1.60×
```

This is a stronger save signal than the e1genqq motion-stack post’s 1.19× ratio.

## Post formula

The post works because it is not a single demo:

```text
body of work
→ short montage across distinct visual worlds
→ named production tools
→ reusable open-source skill
→ immediate GitHub link
```

The montage demonstrates range: travel, finance, AI product, agent orchestration, content analytics, and illustrated marketing pages. Each frame looks intentionally art-directed rather than like a generic SaaS template.

## Repository contents

The repository currently contains two MIT-licensed skills.

### 1. `landing-page-design`

A strict landing-page production system with:

- intake questions;
- one-offer / one-audience / one-action structure;
- hero, benefits, how-it-works, proof, FAQ, risk reversal, and final CTA;
- copy rules;
- typography and spacing scales;
- visual-system constraints;
- motion and accessibility rules;
- content-realism checks;
- shipping requirements.

Its most important rule is:

> A landing page is not a homepage. A landing page wins one intent: one offer → one audience → one primary action.

### 2. `design-to-motion`

A high-fidelity static-design-to-animation system:

```text
exact frame
→ empty state
→ smooth load
→ every visual acts out its story
→ seamless repeat
```

It includes:

- Figma/source fidelity checks;
- layer export rules;
- sacred-background preservation;
- app-frame versus separate-card layouts;
- deterministic frame capture;
- overflow, seam, reset, and rest checks;
- MP4 plus website-GIF and 800×500-GIF exports.

The strongest principle is that loading alone is not motion. Charts should be read, lists should receive items, prompts should be typed, calendars should find slots, and pipelines should carry pulses.

## Provenance note

Leon Lin (`@LexnLin`) publicly noted that the landing skill overlapped his MIT-licensed `taste-skill`. Elaya acknowledged the source had not been traced, credited it, and rewrote overlapping sections in commit `a2735a3`.

That thread is a useful reminder for our contest package:

> Every borrowed method, repo, workflow, asset, model license, and likeness needs a recorded source.

Our current research records already track repository commits and licenses. We should preserve that habit through the public release.

## Fit with RecastRoom

### What this repo solves for us

The current `/app/web` interface is a **workspace**, not a public landing page. It is functional and attestation-gated, but:

- it is workflow-first rather than conversion-first;
- it exposes production internals too early;
- it uses Helvetica and arbitrary sizing/spacing values;
- it has dense live-status panels before the product outcome is emotionally clear;
- it has no public demo video in the hero;
- it lacks social proof, objection handling, FAQ, risk reversal, and a final CTA.

That is acceptable for the studio workspace, but not enough for the public contest/demo surface.

### What to borrow

1. **One public intent:** keep a performance, change the lead.
2. **Hero proof:** show v6b immediately.
3. **Three-step story:** source → authorized reference/consent → review recast.
4. **Rights as risk reversal:** no consent, no render.
5. **Technical proof:** exact audio restoration, frame comparison, workflow hashes.
6. **Motion stories:** each feature card should act out its own job.
7. **Source credits:** open workflow, open components, recorded provenance.

## RecastRoom landing v3 direction

### Hero

```text
Keep the performance.
Change the lead.
```

Subhead:

```text
RecastRoom is an attestation-gated Comfy workspace for MiniMax H3.
The source take stays intact while an authorized reference becomes the new lead.
```

Primary CTA:

```text
Start a dry run
```

Secondary CTA:

```text
Watch the 24-second proof
```

Hero media:

```text
work/recastroom-hook/v5/hyperframes/recastroom-locked-performance-v6b-16x9.mp4
```

### Mid-page argument

1. **The problem:** generative recasting usually loses the take, the camera, or the voice.
2. **The shift:** RecastRoom separates identity from performance, scene, and audio.
3. **How it works:**
   - select owned source;
   - attach an authorized reference;
   - record consent;
   - review frame by frame.
4. **Proof:**
   - source/final comparison;
   - decoded PCM match;
   - deterministic render;
   - workflow manifest.
5. **Rights:** permission is a production state, not a disclaimer.

### Animated feature cards

Use `design-to-motion` discipline:

| Card | Story |
|---|---|
| Source | A clip marker scans the original take |
| Reference | An authorized portrait enters the reference slot |
| Rights | Source, reference, and consent badges turn ready in sequence |
| Render | Mask and identity references travel into the H3 graph |
| Audio | The original waveform remains unchanged while the face changes |
| Review | Source and final frames stay synchronized under one scan line |

### Objection handling / FAQ

1. Does this recreate the voice?
2. Can I use any footage?
3. What counts as an authorized reference?
4. What happens if consent is missing?
5. Does the output preserve exact audio?
6. Can I bring my own Comfy graph?
7. Where is the workflow provenance recorded?
8. What visual checks should I run before publishing?

### Final CTA

Repeat the primary action:

```text
Start an attested dry run
```

## Decision

Use the repo as a **public-surface design system**, not as a replacement for the studio workspace.

- Keep the current app workspace focused on production state and readiness.
- Build a separate public landing page around v6b and conversion.
- Use `design-to-motion` only on feature/bento cards, not on the real recast footage.
- Preserve and publish provenance for every borrowed idea and asset.
