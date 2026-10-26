# C1 v4 next-step research

Date: 2026-10-23
Scope: highest-leverage quality, speed/cost, and repeatability improvements after the successful C1 v4 render. This is research only; no render, paid API call, publication, or model change was made while producing this report.

## Baseline from local evidence

The successful C1 v4 execution is not a vague recipe. It is a pinned, hash-verified package:

- Record: `work/recast-engines/tears-of-steel-jay-c1-v4-20261023/LIVE_V4_SUCCESS.md`
- Final status: `work/recast-engines/tears-of-steel-jay-c1-v4-20261023/live-cli-tos-c1-v4-live-e/status.json`
- Workflow: `work/recast-engines/tears-of-steel-jay-c1-v4-20261023/c1_workflow.json`
- Setup receipt: `review.zip::metadata/setup_receipt.json`

Measured result:

| Item | Value |
|---|---:|
| Output | 960×384, 24 fps, 192 frames, 8.000 s |
| Queue-to-download | 118.213 s |
| Comfy prompt execution | 116.47 s |
| Successful-session cost | 1.04 CU |
| Full v4 authorization sequence | 2.41 CU of a 3.00 CU cap |
| Source/final decoded PCM | identical SHA-256, 706,560 samples, max delta 0 |
| Final SHA-256 | `561f3208e3dbcdda9aab95cf99ecc913f9cfadf642d3a668dc80edf11076b4ed` |
| Bundle SHA-256 | `7c5455e315cae26a03bc69e8b2397f2f00bb41046c2b50fb3be036face36544a` |

The live workflow uses:

```text
MiniMax H3 Ref2VA int8 ConvRot
Alissonerdx Character Swap v1.1 at strength 1.0
DMD 8-step Turbo at strength 1.0
BFS Shot Planner / Conditioning
source_blur = head + hands (keep mouth)
source_blur_segmenter = SAM 3.1
with_audio = true
MiniMaxH3TimedAudio
MiniMaxH3ExactAudioLock
seed 49
0.384 MP output, H3 17n+5 grid
```

The complete setup receipt records exact git SHAs for ComfyUI and six custom-node repositories, SHA-256 hashes for seven models, and a `comfy-kitchen 0.2.40` runtime. That pinning is the reason the run can be repeated.

The largest measured wall-time component was not sampling:

| Setup phase | Seconds |
|---|---:|
| clone and requirements | 20.113 |
| custom nodes | 23.991 |
| model downloads | 452.873 |
| Comfy startup | 20.022 |
| **setup subtotal** | **516.999** |

The cold prompt then took 116.47 seconds. Therefore, future cost work should first attack cold-session waste, not blindly reduce sampling steps.

## Finding 1 — freeze C1 v4 as the golden path before adding anything

The current public repository still describes the older route in `README.md` and `workflows/openjutsu_h3_lipsync_local.json`:

```text
Character Swap v1.0
Head Swap at 0.35
source_blur = off
no Exact Audio Lock
```

That is materially different from the successful C1 v4 graph. The local workflow confirms v1.0, Head Swap 0.35, and `source_blur=off`. C1 v4 replaced those with v1.1, no Head Swap, `head + hands (keep mouth)` source blur, SAM 3.1 segmentation, and exact source-audio latent locking.

The current [Alissonerdx v1.1 guide](https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/blob/main/docs/character-swap.md) and [ComfyUI Wiki v1.1 coverage](https://comfyui-wiki.com/en/news/2026-10-18-h3-character-swap-v1-1) identify v1.1 as the recommended release. It is an 80 MB dynamic-rank extraction that scores better on likeness than the older 620 MB rank-64 checkpoint. The guide expects the aligned guide lattice, `body_swap:` trigger, strength `1.0`, and a head-to-toe `{details}` description.

**Implication:** the first engineering task is to promote the C1 v4 profile into the public, synthetic app path—not to try another model first.

### P0 acceptance criteria

1. A public/default C1-v4 profile uses Character Swap v1.1 at 1.0, no Head Swap, `source_blur=head + hands (keep mouth)`, SAM 3.1, and exact source-audio locking.
2. The old profile remains available only as an explicitly named legacy comparison.
3. The public package records model hashes, custom-node SHAs, runtime versions, and source/rights provenance.
4. All examples use owned, licensed, or synthetic footage.
5. Tests assert the workflow mutation cannot silently regress to v1.0, Head Swap, `source_blur=off`, or unlocked audio.

## Finding 2 — highest-quality next test: guided H3 finishing, not another base swap

The strongest low-risk quality upgrade is [ComfyUI-H3-Video-Upsampler](https://github.com/dntpi/ComfyUI-H3-Video-Upsampler). It upscales a finished H3 clip with an H3 latent upscaler and a light guided re-draw. Its [Hugging Face README](https://github.com/dntpi/ComfyUI-H3-Video-Upsampler/blob/main/README_HF.md) states that the guide comes from the clip itself, while “mouths, motion and the soundtrack come from your clip.”

Relevant controls:

| Control | Recommended starting value |
|---|---:|
| `megapixels` | 2 |
| `denoise` | 0.1 |
| LoRA | `h3upscale_v2_x2.safetensors` |
| `tile_tokens` | default 70,000 on G4; 40,000–25,000 for smaller cards |

The maintainer reports that guided denoise `0.1` produced a 2 MP result that beat the native render in a blind comparison. The node explicitly warns that it should refine an existing clip, not generate from noise, because generation from noise can flicker every 17 frames.

### Why this is first

- It preserves the accepted C1 v4 performance rather than re-rolling identity, occlusion, timing, and background.
- It can be evaluated against the current final without changing the base generation.
- The output should be immediately checked for texture boiling, edge drift around the occluding arm, and Jay's dreadlock silhouette.

### P1 proposed bounded test

```text
input: accepted C1 v4 final
output: 2 MP, same 8-second duration
denoise: 0.1
audio: exact source PCM retained
compare: source / v4 / upscaled
QC: local frame diff + Qwen video review + human playback
```

No compute should be spent without a fresh operator authorization and explicit CU cap.

## Finding 3 — FaceRefine is a repair pass, not a default stage

[ComfyUI-H3-FaceRefine](https://github.com/Carasibana/ComfyUI-H3-FaceRefine) tracks and crops small faces so H3 can re-render them at useful scale, then composites them back. Its README is explicit that H3 renders distant faces poorly because of head-size-in-frame, not output resolution, and that this persists at 720p and above.

Its useful controls are nuanced:

- `auto_capped_768` is the sane default canvas and VRAM ceiling.
- Cost scales with `canvas² × frames`.
- `denoise_multiplier_small_face` defaults to 1.0.
- `denoise_multiplier_large_face` defaults to 0.35.
- `smooth_frames` defaults to 9 to prevent texture pops.
- The box must track stably or the refined face “boils.”
- H3 denoise values do not transfer from SDXL-family models; an ordinary 0.25 can rewrite the face at effective sigma 0.800.

### When to use it

Use FaceRefine only when:

1. face height is genuinely small relative to the frame;
2. mouth readability remains the dominant defect after upscale;
3. the tracked face box is stable;
4. identity is accepted but local texture is not.

Do not add it to C1 v4 by default. The current foreground performer is not a distant face, and a bad crop can introduce a new seam or boil the dreadlocks.

## Finding 4 — reduce cost by batching and reuse, not by destabilizing the golden recipe

### Batch under one guarded G4 session

C1 v4 spent most wall time downloading and installing 44+ GB of models. Once those models are present and Comfy is warm, a second prompt should avoid that fixed cost. This matches earlier local Alissonerdx observations where the first run took 60.6 s and cached runs B/C took 40.2 s and 39.9 s.

A reasonable production pattern is:

```text
cold setup once
preflight all jobs
run base swap(s)
run guided finishing only after accepted base
stop runtime immediately
```

For exploration, batch closely related variants rather than creating a fresh G4 per idea. The queue must retain:

- one submission marker per prompt;
- no automatic retry;
- a total CU cap;
- hard session deadline;
- stop after queue drains;
- receipts for every prompt, including failures.

### Treat step distillation as draft mode

Community speed notes and [WhichH3's LoRA library](https://www.whichh3.com/en/lora/) show meaningful speedups:

| Option | Steps | Reported speedup | Quality signal |
|---|---:|---:|---|
| Turbo v4 8-step | 8 | 2.09× | low quality cost, high arena rank |
| LightX2V Turbo 4-step | 4 | 3.44× | medium; slight detail loss |
| FastH3 4-step DMD2 | 4 | 4.1× | medium; identity/lip-sync preserved in testing |

The official Comfy H3 tutorial lists 20 steps without turbo and 8 turbo steps for standard T2V/I2V/continuation; it also lists a four-step FL2VA file for applicable paths. The character-swap v1.1 workflows, however, are validated with the 8-step DMD Ref2VA path.

Therefore:

- use 8-step C1 v4 for keepers;
- test 4-step only as a draft/batch mode;
- require same-seed, same-input A/B against v4;
- reject it if identity, occlusion handling, gaze, mouth shape, or dreadlocks regress.

### Be conservative with attention and VAE changes

The official Comfy H3 docs say Sage Attention can roughly double speed, but also warn that Comfy Kitchen does not support the int8-ConvRot checkpoints in the current templates and can crash with an alignment error. That makes the successful pinned C1 v4 stack valuable and unpinned upgrades risky.

The [Comfy H3 VAE post](https://blog.comfy.org/p/making-the-minimax-h3-video-vae-2x) describes an int8 VAE and `--fast fp16_accumulation` path with roughly 1.4× decoder speedup and very small measured quality loss. This is a plausible later experiment, but not before the public workflow matches v4.

**Rule:** never swap attention or VAE paths in the golden recipe until a separate benchmark proves output quality and exact-audio behavior on the same clip.

## Finding 5 — adopt Relay's operational model for longer studio work

[H3 Relay](https://github.com/akatz-ai/h3-relay) provides the best public model for studio repeatability:

- source preparation;
- window planning;
- SAM mask conversion;
- bounded-memory generation;
- durable review;
- accepted raw checkpoints;
- optional finishing only after approval;
- per-window reroll without rebuilding accepted windows.

Its README explicitly tells creators to run and review each raw H3 shot before paying for LTX/interpolation or finishing. Its windowed character/reference editing route preserves character image and original-video conditioning in every window.

### What Openjutsu should borrow

Do not replace the successful C1 v4 engine immediately. Instead, add its production semantics:

1. continuous-shot preflight;
2. shot/window manifest;
3. accepted-window cache;
4. reroll only failed windows;
5. finishing pass only after operator approval;
6. exact model/runtime provenance per window;
7. durable side-by-side review.

This directly addresses the prior Get Out and 30-second seam failures: generate per continuous shot, approve, then stitch.

## Finding 6 — multi-person support is now a competitive requirement

The public [Bambushu/h3-recast](https://github.com/Bambushu/h3-recast) workflow swaps up to three people in one pass, keeps motion, set, and clip audio, and includes optional FaceRefine lip repair. Its hard rules are useful:

- one continuous shot, no hard cuts;
- describe every person in the shot, not only changed people;
- provide a scene reference where every face is visible;
- make changes visually explicit;
- use a new seed if outfits or details drift.

Its reported timings are substantial:

| Hardware | 1.5 MP, 6 s, three people | Lip repair |
|---|---:|---:|
| RTX 5090 32 GB | ~18 min | ~2 min |
| RTX 4090 24 GB | ~26 min | ~5 min |
| RTX 4060 Ti 16 GB | ~92 min | ~16 min |

This is a direct competitor to Openjutsu's “recasting studio” positioning. It is also an opportunity:

- C1 v4 has stronger exact source-audio provenance, rights gating, operator review, and evidence receipts.
- H3 Recast has broader multi-person UX and a practical App-mode interface.

### Recommended strategy

Keep C1 v4 as the high-fidelity single-subject engine. Add a separate, explicitly optional multi-person engine profile after auditing `h3-recast`. Do not silently merge the two: multi-person mode introduces scene-reference generation, per-person prompt assignment, and FaceRefine cache behavior that need their own rights and QC gates.

## Ranked roadmap

### P0 — package the golden path locally, no GPU spend

1. Add a C1-v4 engine profile to Openjutsu Studio.
2. Update the public workflow and README away from v1.0 + Head Swap 0.35 + `source_blur=off`.
3. Parameterize source and reference inputs without embedding Jay or private footage.
4. Record the exact model and custom-node hashes.
5. Add regression tests for the v1.1/source-blur/exact-audio contract.
6. Produce a synthetic or owned-footage smoke path.

**Why first:** this converts a one-off successful render into a reproducible app and removes the biggest current mismatch between private success and public repository.

### P1 — one guided finishing test

Run H3 Video Upsampler at 2 MP and denoise 0.1 on the accepted final only. Accept only if:

- duration and frame count remain 8.000 s / 192;
- source PCM remains exactly restored;
- no motion or mouth-timing drift;
- no dreadlock or background texture boil;
- occluding arm and background sniper remain unchanged;
- human review prefers the upscaled result.

### P2 — measure warm-session production economics

In one authorized G4 session, run a small queue:

1. v4 baseline reproduction or current accepted output;
2. guided upscale;
3. optionally one 4-step draft of the same clip.

Record cold setup, each prompt's queue time, per-prompt CU if observable, cache hits, total CU, and stop time. Use the result to define the app's cost guard and batch policy. Do not draw cost conclusions from one cold session.

### P3 — multi-person engine audit and optional profile

Clone and inspect `h3-recast` at an exact commit, list its licenses and model obligations, map its UX, and compare on a three-person synthetic clip. Only then decide whether to expose it as an Openjutsu profile.

### P4 — longer-form Relay-style production

Add continuous-shot segmentation, accepted-window caching, per-window reroll, review-before-finishing, and deterministic stitching. This is the path from one 8-second hero clip to repeatable short-form production.

## What not to do now

1. Do not replace C1 v4 with H3 Relay wholesale.
2. Do not add Head Swap back.
3. Do not change Character Swap v1.1, source blur, or Exact Audio Lock before packaging the public profile.
4. Do not use 4-step, new attention, or a new VAE for keeper renders without same-input A/B evidence.
5. Do not post or submit private Tears of Steel/Jay material.
6. Do not call the current result a formal keeper until the operator explicitly records acceptance.

## Source index

Local:

- `work/recast-engines/tears-of-steel-jay-c1-v4-20261023/LIVE_V4_SUCCESS.md`
- `work/recast-engines/tears-of-steel-jay-c1-v4-20261023/live-cli-tos-c1-v4-live-e/status.json`
- `work/recast-engines/tears-of-steel-jay-c1-v4-20261023/c1_workflow.json`
- `work/recast-engines/tears-of-steel-jay-c1-v4-20261023/live-cli-tos-c1-v4-live-e/review.zip`
- `workflows/openjutsu_h3_lipsync_local.json`
- `README.md`
- `docs/SUBMISSION_CHECKLIST.md`

External:

- [Alissonerdx Character Swap v1.1 guide](https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/blob/main/docs/character-swap.md)
- [ComfyUI Wiki: Character Swap v1.1](https://comfyui-wiki.com/en/news/2026-10-18-h3-character-swap-v1-1)
- [ComfyUI-H3-Video-Upsampler](https://github.com/dntpi/ComfyUI-H3-Video-Upsampler)
- [H3 Video Upsampler README on Hugging Face](https://github.com/dntpi/ComfyUI-H3-Video-Upsampler/blob/main/README_HF.md)
- [ComfyUI-H3-FaceRefine](https://github.com/Carasibana/ComfyUI-H3-FaceRefine)
- [H3 Relay](https://github.com/akatz-ai/h3-relay)
- [Bambushu/h3-recast](https://github.com/Bambushu/h3-recast)
- [Official Comfy MiniMax H3 tutorial](https://github.com/Comfy-Org/docs/blob/main/tutorials/video/minimax/minimax-h3.mdx)
- [ComfyUI MiniMax H3 VAE speedup](https://blog.comfy.org/p/making-the-minimax-h3-video-vae-2x)
- [WhichH3 LoRA speed/quality library](https://www.whichh3.com/en/lora/)
- [MiniMax H3 speed-up notes](https://github.com/matsuo-koya/minimax-h3-notes/blob/main/README.md)
