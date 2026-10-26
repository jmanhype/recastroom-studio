**Evaluation method.** I compared the LEFT *original* (source woman + audio) against the RIGHT *result* (H3 repair) frame‑by‑frame at every available sample (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0 s), using Picture 1 / the top reference tile as the identity authority for *Jay*, and checked the previously‑failing ~2.5 s window specifically.

**Per‑criterion scores (0–10).**

- **Target identity / style – 9.** Every sampled frame in the result panel shows Jay: uniformly dark shoulder‑length locs, full black beard + mustache, broad nose, full lips, rounded jaw, dark skin tone — all consistent with Picture 1. No frame reverts to the source woman. The face reads slightly softer than the crisp studio reference, but that is correct here, because Jay must inherit the *scene's* flat warm key light, not the reference's dramatic gray‑backdrop light. Integration is clean.
- **Non‑target preservation – 9.** The chrome vintage mic is present, correctly placed at the mouth, in all 10 frames; the body/shoulder/arm pose transfers from the source (e.g. raised‑hand gesture at 1.0 s appears on Jay too; arms down at 2.0 s). Framing (centered medium close‑up) and lighting direction match the original. Only the person was swapped, as instructed.
- **Background – 10.** Solid orange backdrop preserved end‑to‑end; no bleed, no replacement of background regions.
- **Camera – 10.** Static camera matched; no drift or re‑framing introduced.
- **Gesture / gaze – 8.** Head rotations track the source (left tilt ~3–5 s, right tilt ~6–7 s, upward glance ~8 s). Gaze is performance‑plausible; a couple of frames sit a hair off the source's eye line but within natural singing motion.
- **Mouth / lip sync – 9.** Aperture and lip shape follow the source phonemes across the lyric line ("Same song brand new face…"): wide open at 0.0/3.0 s, toothy smile at 2.0 s, sustained open shapes through 5–7 s (held notes). Vibrato can't be seen in stills, but the sustained, modulating open‑mouth frames are consistent with the held notes in the audio.
- **Temporal stability – 9.** Identity is stable across all samples; locs and beard never flicker. Critically, the **2.5 s morph is gone** — the 2.0 s and 3.0 s frames bracketing it are both solidly Jay, so the prior failure mode is resolved at this sampling density.
- **Artifacts – 8.** Minor face smoothing on the forehead (≈8.0 s) and motion‑blurred/indistinct raised hands (≈1.0 s, matching the source's own blur). No gross blending seams at the hair/orange edge, no mic distortion, no extra limbs.

**Exact failure timestamps observed:** *None.* Checked 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0 s — all show Jay with correct mic/backdrop/pose. The previously failing ~2.5 s window is clean at its 2.0 s and 3.0 s neighbors. *(Caveat: samples are 1 s apart, so a sub‑2.5 s single‑frame flicker between 2.0 and 3.0 s could in principle hide; nothing at the visible resolution indicates one.)*

**Summary.** The repair holds Jay's identity for the full clip, preserves the orange backdrop, chrome mic, source pose, static camera, and frame‑accurate mouth shapes for the sung line and held notes, and eliminates the earlier woman‑morph at 2.5 s. Remaining issues are cosmetic (slight face softness, hand motion blur) and do not break identity or sync.

VERDICT: keeper candidate
