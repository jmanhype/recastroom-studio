# Pipeline

RecastRoom Studio currently uses a 29-node MiniMax H3 Ref2VA C1 V4 graph optimized for one-person dialogue replacement.

## Conditioning

```text
source clip
  ↓
BFSShotPlanner
  ↓
BFSShotH3ConditioningSimple
  ↓
MiniMax H3 Ref2VA
```

Core settings:

| Setting | Value |
|---|---:|
| Character Swap LoRA | v1.1 at `1.0` |
| Head Swap LoRA | disabled / absent |
| Steps | `8` |
| Seed default | `49` |
| Source blur | `head + hands (keep mouth)` |
| Source segmenter | `SAM 3.1` |
| Audio conditioning | `on` |
| Exact audio lock | `on` |

## Why source audio matters

Visual-only conditioning can turn speech into generic mouth ovals. The repair that produced the strongest result changed:

```text
with_audio = false
```

to:

```text
with_audio = true
```

and added an exact word schedule derived from Whisper:

```text
word → start/end timestamp → one-based source frame range
```

This lets the model distinguish:

- spoken words from silent pauses,
- labiodental contact from generic rounding,
- jaw drop from a static open mouth,
- phrase release from early closure.

## Required ComfyUI custom nodes

- ComfyUI-BFSNodes
- ComfyUI-KJNodes
- ComfyUI-RMBG
- ComfyUI-VideoHelperSuite
- ComfyUI-H3-ExactAudioLock

## Required model files

```text
models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors
models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
models/vae/minimax_h3_video_vae_fp16.safetensors
models/vae/minimax_h3_audio_vae_fp32.safetensors
models/loras/experimental/minimax_h3_dmd_ref2va_8step_turbo_pruned.safetensors
models/loras/minimax_h3_character_swap_v1.1_ref2va_fro.safetensors
models/checkpoints/sam3.1_multiplex_fp16.safetensors
```

The app also requires the ComfyUI-H3-ExactAudioLock custom node.

## Shot quality gate

Good clips:

- one target performer,
- visible eyes and mouth,
- stable camera,
- clear dialogue,
- one continuous shot,
- 5–8 seconds.

Reject or split clips containing:

- hats, sunglasses, or masks,
- strong profile angles,
- crowded frames,
- overlapping speakers,
- fast cuts,
- occluded mouths,
- heavy motion blur.

Bad source conditioning causes more failures than model choice. RecastRoom intentionally reports preflight risks before a GPU job is queued.

## Post-generation

After H3 returns a generated video:

1. trim to the exact source frame count,
2. restore the original source audio,
3. build a source/final side-by-side,
4. run human review,
5. optionally run multimodal QC.

The final public demo must receive human review before being called a keeper.
