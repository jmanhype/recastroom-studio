# Models used by the bundled workflow

RecastRoom Studio does not redistribute model weights. The bundled ComfyUI API
workflow expects a self-hosted ComfyUI installation with the following upstream
assets already installed. Each model remains under its upstream license.

| Pipeline role | Asset used by `workflows/openjutsu_h3_lipsync_local.json` | Notes |
|---|---|---|
| Video generator | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | MiniMax H3 Ref2VA int8 ConvRot; core H3 model |
| Text/vision encoder | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | Qwen3-VL 32B MiniMax-H3 text/vision loader |
| Character swap | `minimax_h3_character_swap_v1.1_ref2va_fro.safetensors` | Character Swap LoRA v1.1 at strength `1.0` |
| Turbo scheduler | `experimental/minimax_h3_dmd_ref2va_8step_turbo_pruned.safetensors` | 8-step DMD/Turbo LoRA |
| Video VAE | `minimax_h3_video_vae_fp16.safetensors` | Decodes H3 video latents |
| Audio VAE | `minimax_h3_audio_vae_fp32.safetensors` | Used by source-audio conditioning and exact audio lock |
| Source segmentation | SAM 3.1 | Selected by `source_blur_segmenter`; used for `head + hands (keep mouth)` |

## Word timing

The app accepts Whisper-compatible word-timing JSON. Whisper is used as a
timing format and local transcription aid; it is not a rights-clearance system.

## Execution boundary

- The bundled graph is intended for a self-hosted ComfyUI runtime.
- The official Comfy SDK adapter is present, but hosted execution requires a
  configured deployment and credentials.
- CPU dry runs do not load these models and must not be presented as H3 inference.

## License boundary

The MIT license in this repository covers application code, workflow JSON, and
documentation. It does not cover model weights, provider accounts, source
footage, reference likenesses, or generated outputs.
