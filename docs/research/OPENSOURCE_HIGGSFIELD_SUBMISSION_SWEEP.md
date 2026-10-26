# Open Source Higgsfield public submission sweep

Snapshot: 2026-10-23 21:36 UTC
Scope: public, self-declared challenge candidates visible through GitHub topics/code search, contest-tagged posts, ReelStack’s challenge index, and linked repositories. This is not access to the private Typeform ledger. “Candidate” means publicly declared or strongly indicated; it does not mean the official form was submitted.

No publication, social post, form entry, GPU render, or external side effect was made during this research.

## Official bar

The official challenge requires:

```text
one focused creative app built on the Comfy Developer Platform
licensed GitHub repository
local setup instructions
Comfy API-format workflow files
demo video <= 2 minutes
public social post tagged #OpenSourceHiggsfield
optional but encouraged live try link
```

The deadline is October 30, 2026 at 9:00 AM PT. MiniMax H3 must be the core model for the H3 bonus; Open Weights Only excludes partner nodes and closed APIs.

Sources:

- [Official challenge page](https://comfy.org/open-source-higgsfield)
- [Official announcement](https://blog.comfy.org/p/higgsfield-promised-to-open-source)

## Candidate snapshot

All repositories were cloned shallow at the listed heads and inspected locally. Stars and repository state are point-in-time observations.

| Candidate | Head at inspection | License | Public surface | Local verification | Threat read |
|---|---|---|---|---|---|
| [bgstratt/seriesmith](https://github.com/bgstratt/seriesmith) | `7181488c6490082e9f41265949fa2bbb06c05ed7` | MIT | Repository, ComfyUI custom-node/editor installation, docs; no public live demo or social receipt found in this sweep | `1616 passed, 25 skipped, 891 subtests passed` | **Highest engineering threat** |
| [IBFolding/haggs](https://github.com/IBFolding/haggs) | `8e15b54f50b223d38405efc6c6134d595e196dbd` | MIT | [Public Vercel demo](https://haggs.vercel.app), docs, workflow catalog | Typecheck passed; `421` tests passed | **Strong Best Overall / Viral threat** |
| [thePloggy/CreatorOS-Studio](https://github.com/thePloggy/CreatorOS-Studio) | `f4b78fa56385cc08d7f8091e5b4f864d9839a18d` | Apache-2.0 | [1:59 YouTube demo](https://youtu.be/axHdAXHv3Kk), [live GPU demo](https://forge.taila06702.ts.net:8443), screenshots | `npm ci`, lint, and production build passed; no test suite found | **Strong public-demo/open-weights threat** |
| [Orazen/conjure](https://github.com/Orazen/conjure) | `3dbbfaf5797e785565d8bb019f2117c52f7e57d6` | MIT | [Static live showcase](https://orazen.github.io/conjure/), 22 effects, mock mode, workflows | Typecheck, `28` tests, production build, and `178/178` workflow validations passed | **Strong Viral / Open Weights / LTX / FLUX threat** |
| [Bambushu/h3-recast](https://github.com/Bambushu/h3-recast) | `19304d8023bc4a78a4c412d1be5e156f72540852` | MIT | Repository, ComfyUI App-mode workflow, 33-second demo asset, CivArchive post explicitly declaring challenge entry | JSON/workflow inspected; no automated tests or standalone web app | **Direct H3/Openjutsu competitor** |
| [Tekholms-LW/ReAngle](https://github.com/Tekholms-LW/ReAngle) | `d13a284274d13f8d915b147c41e9c07196da2bb5` | Apache-2.0 | [public showcase](https://tekholms-lw.github.io/ReAngle/), repository, social posts | Backend: `49 passed, 2 failed` due local ffmpeg lacking `drawtext`; node pack: `41 passed, 1 skipped` | **Strong Innovative / LTX threat** |
| [rk0neki/OpenKatana](https://github.com/rk0neki/OpenKatana) | `cfc9a69c9342c204501acf9128504fb2b8c53bb6` | Apache-2.0 | Repository, Studio, ComfyUI Apps, CLI/MCP, docs, public Reddit post | Minimal install collected 272 errors because Comfy nodes import `torch`; this was not a full documented Comfy-runtime install | **Agent/editor innovation threat** |
| [synthetic-ape/comfield](https://github.com/synthetic-ape/comfield) | `3dbae26715869bc0c35507eedf840682f50e7c09` | MIT | Repository, screenshots, docs; no live demo or social receipt found in this sweep | Typecheck passed, `51` tests passed after schema cache warmed, production build passed | **Broad Higgsfield-studio threat** |
| [pyoonpyoon/open-higgsfield](https://github.com/pyoonpyoon/open-higgsfield) | `ccaf07ba4efc6f57ebf5bd54fd0788f869b6ecd7` | MIT | [public dry-run demo](https://open-higgsfield-reshoot.vercel.app), repository, CC0 example | `14` tests passed, but `npm ci` reports lock/package mismatch and typecheck fails on four route/layout types | **Polished focused demo threat** |
| [EmmanuelRiveros/TimeFlight](https://github.com/EmmanuelRiveros/TimeFlight) | `230a519315c41e552d3c794226f35bb0d5828dff` | Apache-2.0 plus GPL-3.0 Blender folder | Repository, docs, tests, explicit challenge declaration | `67 passed, 2 skipped` | **Distinct Innovative / LTX candidate** |
| [SydFloyd/openjutsu](https://github.com/SydFloyd/openjutsu) | `f783a001ff3ceae4711a592623587224bf87f46c` | Apache-2.0 | Repository/docs; direct same-name competitor | `16 passed, 1 failed` on upload-normalization frame count | Direct competitor, currently less verified |
| [audriu/fxjutsu](https://github.com/audriu/fxjutsu) | `cd333a4d15edc928060d27c2d0c14478ff7ac11e` | **No license file found** | Repository/workflows | Not run | **Fails a hard contest requirement unless fixed** |

## What the strongest entrants do better

### 1. Seriesmith — engineering depth and production semantics

Seriesmith is the strongest engineering submission found. It turns series configuration and screenplay-style episode scripts into per-shot Comfy jobs, with:

- H3 Ref2VA as the default video target;
- FastH3, LTX-2, Wan, Router, Cloud, and deployment backends;
- per-shot rerenders;
- reference/keyframe generation;
- queue and editor;
- take provenance;
- proxy/final passes;
- upscale/post/master;
- a ComfyUI Manager installation path.

Its editor was launched locally without a GPU. The first screen correctly reported:

```text
local ComfyUI not answering
3 shots
3 missing references
Build required
```

Clicking **Build** completed offline and produced final and proxy shotlists for a three-shot, 11.25-second starter. This is strong state transparency.

### 2. HAGGS — broadest product surface and public demo

HAGGS’ public Vercel app presents a complete studio narrative:

- script-to-screen workflow;
- 26 ready-made apps;
- photos, video, series, comic, editor, workflow gallery, and academy;
- model roles and prices;
- a real recreate-an-edit case study;
- open-weights routing to a local GPU;
- Claude/MCP integration;
- clear landing-page storytelling.

It has the best public marketing surface found in this sweep. The landing page explains the product in plain language and shows model choices, expected prices, and an example cost ledger.

### 3. CreatorOS Studio — strongest public GPU try path

CreatorOS is less test-covered but has the strongest operator-facing try evidence:

- a public 1:59 demo;
- public GPU-backed instance;
- rate limits and owner-key controls;
- setup wizard;
- mobile screenshots;
- broad open-weights workflow set;
- explicit character/likeness policy.

Its repository production build passed locally. The public page’s DOM loaded the full app, although the hidden-browser accessibility/screenshot capture did not expose its visual surface cleanly.

### 4. Conjure — best focused viral/open-weights UX

Conjure is the strongest focused “one tap” product:

- 22 VFX recipes;
- public static showcase;
- before/after comparison;
- effect builder;
- shareable recipe links;
- mock mode with no GPU;
- FLUX 3 end-frame + LTX-2.5 video/audio route;
- Comfy SDK and custom-node paths.

It has excellent demo psychology: a user can understand the product before installing anything.

### 5. H3 Recast — direct multi-person H3 challenge

H3 Recast directly attacks the Openjutsu use case:

- up to three people in one pass;
- original motion, set, and audio retained;
- optional FaceRefine lip repair;
- ComfyUI App-mode workflow;
- MIT license;
- AI-generated example cast;
- explicit challenge declaration.

Its graph contains 21 nodes, 32 links, and five groups. The packaged demo MP4 hashes as:

```text
ab3995a56526bf64ab66a84b61ce68cca319130442cecec28617446362d853a5
```

Weaknesses: it is a workflow rather than a full standalone app, has no automated test suite, requires roughly 95 GB of models, needs 16 GB+ VRAM and 64 GB RAM, and has heavier UX friction than Openjutsu’s web form.

### Commercial benchmark — ElevenLabs / ElevenCreative Recast

ElevenLabs also launched a hosted Recast feature in ElevenCreative. Its current documentation calls the model **MiniMax H3 Max Recast** and describes:

```text
source video up to 30 seconds
1–4 reference photos
output length follows source
source audio kept
resolution up to 1080p
aspect ratio follows source
```

The public launch framing says the swap preserves lighting, composition, motion, camera movement, cuts, and original audio. The product is a useful benchmark for expected user experience and multi-person scope, but it is not an Open Source Higgsfield submission: it is a closed hosted ElevenCreative feature rather than an open Comfy app/repository.

Competitive implication: Openjutsu should not try to imitate the hosted service’s breadth before the contest deadline. The differentiated claim remains the open, rights-gated, receipted pipeline—especially exact decoded-audio restoration, pinned model/node provenance, source blur to reduce identity leakage, and local reproducibility.

## Category implications

### Best Overall

Likely leaders:

1. Seriesmith — engineering depth, H3 core, broad model routing, editor, tests.
2. HAGGS — product breadth, public demo, pricing transparency, 421 tests.
3. CreatorOS — public try path, open weights, strong demo.
4. Comfield — broad Higgsfield-style studio, clean tests/build.

Openjutsu cannot win a breadth contest against these. Its viable lane is depth and trust: **one continuous dialogue shot, exact performance/audio preservation, rights gating, reproducibility, and reviewable evidence**.

### Most Viral

Likely leaders:

1. Conjure — one-tap VFX, gallery, sound, shareable recipes.
2. HAGGS — polished landing experience and many starting points.
3. CreatorOS — public GPU demo and 1:59 video.
4. H3 Recast — instantly understandable multi-person recasting.

Openjutsu’s current public story is not viral enough. A synthetic before/after comparison page with visible mouth motion, waveform/PCM equality, and one-click workflow download would be the minimum competitive surface.

### Most Innovative

Likely leaders:

1. ReAngle — draw a 3D camera path and re-render the clip.
2. TimeFlight — open geodata and historical reconstruction.
3. OpenKatana — agent-driven editable video projects through CLI/MCP/Studio.
4. Seriesmith — model-independent script-to-shot compiler and per-shot production state.

Openjutsu has a real innovation story in Exact Audio Lock, source blur, SAM 3.1, and receipted C1 v4, but it must be demonstrated publicly.

### Open Weights Only

Likely leaders:

1. Conjure.
2. ReAngle.
3. CreatorOS.
4. SydFloyd/openjutsu, if its setup is repaired.

Openjutsu qualifies technically, but the public default workflow is still stale relative to C1 v4.

### MiniMax H3 bonus

Likely leaders:

1. H3 Recast — direct, multi-person, contest-declared.
2. Seriesmith — H3 Ref2VA default and mature production editor.
3. HAGGS — H3 used prominently across a broad studio.
4. Comfield — H3/FastH3 as local open-weight options.
5. Openjutsu — strongest exact-audio/performance provenance, if packaged.

H3 Recast is the biggest direct threat to Openjutsu’s category story because it solves multi-person casting. Openjutsu should not copy that immediately; it should win on verifiable fidelity and governance, then add multi-person as a separately gated engine.

## Openjutsu’s current position

Verified locally at `d9c8e80`:

```text
105 passed
```

Existing strengths:

- working local web UI;
- rights/consent gate;
- CLI and API surface;
- workflow timing/media tests;
- backend readiness guards;
- review artifacts;
- synthetic demo evidence;
- private C1 v4 exact-audio success;
- model/node hash receipts;
- Colab cost and session evidence.

Critical public gaps:

1. public repository;
2. public approved demo;
3. public social post;
4. Typeform receipt;
5. live Comfy Developer Platform SDK proof;
6. public default workflow still describes v1.0 + Head Swap + `source_blur=off`;
7. UI/product presentation is behind HAGGS, Conjure, and Open Higgsfield.

The private C1 v4 result is better than the current public workflow. That mismatch is the biggest immediate risk.

## Strategic response

### P0 — Ship the golden path, not more breadth

1. Make Character Swap v1.1 + source blur + SAM 3.1 + Exact Audio Lock the public default profile.
2. Keep v1.0/Head Swap only as a named legacy comparison.
3. Add regression tests that fail if the graph regresses to `source_blur=off`, Head Swap, v1.0, or unlocked audio.
4. Update README/contest narrative around exact source performance and rights.
5. Repackage with the C1 v4 model/node provenance.

### P1 — Match the public-demo pattern

Competitors already provide static or dry-run demos. Openjutsu needs:

- public synthetic source/final example;
- before/after player;
- waveform/PCM equality card;
- workflow JSON download;
- setup path;
- “dry run / no GPU attached” state;
- model/readiness table;
- cost and execution boundary.

### P2 — UI parity where it changes judgment

Borrow, do not rebuild:

- HAGGS: model-role cards and visible price before run.
- Seriesmith: readiness/missing-model/missing-reference state.
- Conjure: gallery-first public showcase and mock mode.
- Open Higgsfield: focused setting cards and explicit dry-run badge.
- ReAngle: precomputed public try examples.

### P3 — Optional multi-person engine

Audit and optionally expose H3 Recast as a separately named multi-person engine. Do not silently merge it into C1 v4:

- scene-reference generation;
- one sentence per person;
- FaceRefine cache;
- separate rights/QC gates;
- separate model obligations;
- separate failure modes.

### P4 — Finish the actual submission

The public package must close:

```text
live Comfy SDK execution proof
public repo
approved public demo
X post with verified links
Typeform receipt
```

No local feature should displace these owner-gated blockers before October 30.

## Bottom line

The field is stronger than it was at launch. Openjutsu is not the only polished app, and it is no longer the only H3 recasting candidate.

The winning lane is not:

```text
more apps
more model routers
more broad studio features
```

It is:

```text
attestation-gated, receipted, exact-performance recasting
```

If Openjutsu ships C1 v4 publicly with a clean demo and SDK proof, it has a differentiated, credible H3 entry. If it remains private or publishes the stale v1.0/Head Swap workflow, H3 Recast, Seriesmith, HAGGS, Conjure, CreatorOS, and ReAngle are all likely to present more complete submissions.
