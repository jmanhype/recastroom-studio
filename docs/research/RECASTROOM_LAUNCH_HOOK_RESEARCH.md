# RecastRoom launch hook: external research brief

Date: 2026-10-25

Scope: validate the five-reviewer Qwen 3.8 panel's priority fixes against current platform documentation and established production guidance. This is research only; no hook edit was made in this pass.

## Verdict

The panel's diagnosis is directionally correct and supported by platform evidence:

1. **Keep the 0–5s source-to-recast hook.** TikTok explicitly recommends hooking viewers in the first three seconds and skipping long intros/logo openings; its Creative Codes also report that 90% of ad-recall impact is captured within the first six seconds.
2. **Retime and raise the voiceover.** The current master measures `-19.8 LUFS integrated`, `1.9 LU loudness range`, and `-5.5 dBTP`, so there is ample headroom. A delivery around `-14 to -16 LUFS` with a `-1 dBTP` ceiling is a defensible mobile-feed target. No official TikTok/Instagram/X LUFS target was found, so this should be labeled a production target rather than a platform rule.
3. **Replace the dense UI section with large proof cards.** TikTok recommends high-resolution vertical creative, safe zones, and text overlays; its creative research says text overlays increase view time/recall and product-on-screen imagery increases brand affinity/recall. The current full-screen UI asks viewers to read too much at once.
4. **Cut or label the unrelated montage.** Platform guidance favors a clear hook/body/close structure and value proposition. Two tightly labeled examples are preferable to five unrelated scenes.
5. **Use one explicit CTA and shorten the static hold.** TikTok recommends a strong close/CTA. X Media Studio supports a clickable video CTA in metadata, but the in-video end card should still carry one unambiguous action.

The current 31.17s runtime is not inherently wrong—TikTok recommends 21–34s for most ads—but the panel's suggested 22–25s v2 is a better focused cut and remains inside TikTok's recommendation. A separate 12–15s vertical X teaser may be useful because X's vertical ad guidance recommends under 15 seconds.

## Current artifact evidence

Local master:

- `work/recastroom-hook/recastroom-hook-v1.mp4`
- 1920×1080, 30 fps, 31.166667 seconds, H.264
- Integrated loudness: `-19.8 LUFS`
- Loudness range: `1.9 LU`
- True peak: `-5.5 dBFS`
- Qwen panel average overall: `6.4/10`; all five verdicts: `SMALL FIX`

The opening transcript begins “Watch this take” at 0.00s in the mux, but the panel identified an audible/visual perception delay of roughly 250ms. The v2 edit should validate sync by ear and waveform against the first visual beat, not rely only on the mux timestamp.

## Platform evidence

### Hook, structure, pacing, and CTA

- **TikTok SMB video guide:** mobile-first 9:16, 1080×1920 or higher, safe zones, hook in the first three seconds, product in action immediately, 21–34 seconds for most ads, quick cuts, and a natural CTA shown visually and in voiceover.
  - https://ads.tiktok.com/business/en/guides/video-advertising-guide?redirected=1
- **TikTok Creative Codes:** hook/body/close; communicate value early because 90% of ad-recall impact is captured within the first six seconds; product on screen increases brand affinity/recall; CTA cards improve recall/likeability; text overlays increase view time/recall; faster scene changes can draw viewers in; sound is vital.
  - https://ads.tiktok.com/business/en/blog/creative-best-practices-top-performing-ads
- **YouTube retention guidance:** viewer attention commonly declines over time; move compelling content earlier if top moments occur late, and inspect dips/skips to diagnose sections that lose viewers.
  - https://support.google.com/youtube/answer/9314415
- **Google bumper ads:** six-second or less formats reinforce one memorable message/CTA. This is useful for a teaser derivative, not a replacement for the main 22–25s launch cut.
  - https://support.google.com/google-ads/answer/12803192
- **Wistia CTA analysis:** for interactive video CTAs, videos under one minute converted best with CTA placement in the first quarter; action words such as “try,” “download,” “register,” and “click” performed best. Social video differs because the post itself carries the link, but this argues against relying only on a late static end card.
  - https://wistia.com/blog/using-video-ctas

### Aspect ratio and safe zones

- **X Media Studio / organic upload:** landscape maximum 1920×1080, recommended 1280×720 landscape and 720×720 square; H.264, AAC, up to 60 fps; subtitles can be CEA-608/708 or SRT. Premium uploads can reach four hours/16GB, while non-Premium uploads remain up to 140 seconds/512MB.
  - https://help.x.com/en/using-x/media-studio-faqs
  - https://help.x.com/en/using-x/x-videos
- **X Ads:** standalone 16:9 recommends 1920×1080; supported formats include 16:9 1920×1080, 1:1 1080×1080, 4:5, 2:3, and 9:16 1080×1920. Vertical Video Ads recommend under 15 seconds and 720×1280 minimum.
  - https://help.x.com/en/business-and-advertising/creative-ad-specifications
- **TikTok in-feed ads:** vertical 9:16 is recommended (minimum 540×960); horizontal 16:9 is supported (minimum 960×540). Safe zone varies by dimension, caption length, and add-ons; TikTok supplies downloadable safe-zone files rather than one universal pixel inset.
  - https://ads.tiktok.com/resources/help/article/tiktok-auction-in-feed-ads?lang=en-GB
- **Implication:** keep a high-quality 16:9 master for X/desktop, but create a purpose-built 9:16 1080×1920 version for TikTok/Reels/Shorts rather than center-cropping and hoping no caption/UI collision occurs.

### Audio loudness

No authoritative TikTok, Instagram, or X document publishing an exact social-video LUFS target was found. The recommended target below is therefore a cross-platform production practice:

- **Spotify** officially normalizes to `-14 dB LUFS`, recommends targeting `-14 dB integrated LUFS`, and keeping below `-1 dBTP` for lossy encoding safety.
  - https://support.spotify.com/nl-en/artists/article/loudness-normalization/
- **Apple Podcasts** recommends around `-16 dB LKFS ±1 dB` with true peak no higher than `-1 dBFS` to avoid content-driven volume adjustment and encoding clipping.
  - https://podcasters.apple.com/support/893-audio-requirements
- **EBU R 128** establishes loudness normalization and a true-peak ceiling of `-1 dBTP`; short-form ads/promos are explicitly covered by R 128 s1.
  - https://tech.ebu.ch/docs/r/r128v4_0.pdf

## Comparison signal: Brendan Jowett's AI-video utility post

Observed post: https://x.com/jowettbrendan/status/2113937838563864798

At inspection it showed:

- 33.6K views
- 30 replies
- 54 reposts
- 581 likes
- 1.5K bookmarks

The post's pattern is useful even though it is not a RecastRoom competitor:

1. **Utility-first hook:** “If you want to edit videos with Claude or ChatGPT, bookmark this.”
2. **One-line outcomes:** each linked repository is paired with the user-visible result—cuts/captions/B-roll, renders locally, scripts/edits/publishes shorts, writes Remotion code, times every word, or removes silence.
3. **Screenshot-forward proof:** the media carousel shows readable project pages and examples rather than abstract branding.
4. **Conversation prompt:** it ends with “What did I miss?”, inviting additions.
5. **The strongest embedded example is itself a 15-second, 1920×1080, 60fps showreel**, supporting the idea of a shorter high-impact derivative alongside the main cut.

Application to RecastRoom:

- Use the video to prove the transformation and keep the technical inventory in the post/thread.
- Add a “three steps to first recast” visual pattern: owned source → authorized reference/consent → review recast.
- Make the post copy utility-first, not platform-first: “If you want to keep the performance and change the lead, bookmark this.”
- Provide one clear result per linked component; avoid asking one 31-second video to carry an entire product tour.
- A 15s showreel/teaser may be the better bookmark bait asset, with the 22–25s cut as the fuller launch hook.

This is a directional pattern, not causal proof; the author's existing reach and audience also contribute to engagement.

## Comparison signal: Alex Becker's locked-audio generation recipe

Observed post: https://x.com/ZssBecker/status/2113320998527221875

At inspection it showed:

- 127.7K views
- 39 replies
- 78 reposts
- 1,041 likes
- 3,113 bookmarks
- Embedded video: 24.233 seconds, 810×1080 (3:4), autoplay player

The post is a direct recipe for one-shot spoken AI ads. Its key claims and structure are:

1. **Generate or record the voice separately.** He names ElevenLabs or a real recording as the source, then places that complete dialogue/script in the prompt.
2. **Lock the audio.** The prompt explicitly says the audio is passed through unchanged, at original speed and length, with no added, removed, or changed words. This prevents the video model from inventing new speech or re timing the performance.
3. **Separate reference responsibilities.** The prompt assigns distinct roles to:
   - identity reference;
   - location reference;
   - laptop-screen reference;
   - facial-expression/performance video;
   - voice/dialogue audio.
4. **Write the event and camera path.** It specifies a single continuous amateur selfie take, the man already walking mid-sentence, the laptop reveal around second 8, the return to the face, and the final natural stop.
5. **Use deliberate production constraints.** It asks for a low-quality, soft, slightly noisy phone look, small natural expressions, no wide-eyed exaggeration, no captions/lower-thirds/logos, no cuts, no flicker, and no sudden exposure changes.

The bookmark-to-like ratio is especially high: **3,113 bookmarks vs. 1,041 likes**. Like the Jowett post, this behaves as reusable knowledge, not just a demo.

Application to RecastRoom:

- **Make “audio is locked, not recreated” a primary visual claim.** Becker's post confirms that exact audio preservation is a major practitioner pain point and differentiator.
- **Expose a reference-role manifest in the launch evidence.** The app should show which input controls identity, performance, scene, screen content, and audio. This is clearer and more persuasive than a generic workflow screenshot.
- **Adopt an explicit continuity contract.** The launch post can state that source camera, timing, performance, and decoded PCM are locked, then show the comparison/QC evidence.
- **Do not over-polish the proof clip.** The most shareable example deliberately asks for an amateur, continuous phone look. RecastRoom's cinematic source can remain cinematic, but any new teaser should avoid looking like a generic glossy AI montage.
- **Publish a reusable prompt/run contract.** A compact “locked-audio role manifest” in the thread or README would give judges and creators something immediately bookmarkable.

This comparison also suggests one v2 copy line:

> “The audio is not generated. It is the original recording, decoded and restored.”

That sentence is more concrete than the current “exact original audio” phrase because it distinguishes RecastRoom from text-to-speech/video pipelines that invent new dialogue.

Recommended v2 audio gate:

- Integrated loudness: `-14` to `-16 LUFS`; choose `-14 LUFS` for the social master if voice intelligibility remains natural.
- True peak: at or below `-1 dBTP`.
- Dialogue/music relationship: voice consistently dominant, music/SFX bed ducked approximately 3–4 dB under narration.
- Sync: no perceptible VO lag on the opening cut; verify by waveform and human playback.

## Prioritized v2 edit plan

### P0 — Audio repair

1. Remove the perceived 250ms VO offset; “Watch this take” should land with the first visual beat, not after it.
2. Normalize to `-14` or `-16 LUFS integrated`, limit to `-1 dBTP`, and preserve natural speech dynamics rather than making a flat, crushed VO.
3. Add only minimal transition accents/SFX and a low-level bed. The product promise is “exact original audio,” so the launch video's own mix must sound controlled and intelligible.

### P1 — Rebuild the middle as hook/body/proof

Target 22–25 seconds:

1. **0–5s: preserve source→recast.** Keep the strongest existing opening and lower-third system.
2. **5–10s: one or two labeled examples only.** Label what remains locked: movement, lighting, shot, and audio. Remove unrelated kitchen/robot/mic/card imagery unless it directly supports “same take, new lead.”
3. **10–15s: large rights/workflow cards.** Use three cards maximum: owned clip, authorized reference, recorded consent. Show state changes at motion-design scale; do not expose dense product UI.
4. **15–20s: real proof metadata.** Show one legible result strip: source hash/reference consent/decoded PCM match/render size/elapsed time. Add a compact reference-role manifest—identity, performance, scene, audio—rather than a dense UI capture. Label the 64×64 test as “transport smoke test,” or omit it from this launch cut.
5. **20–23/25s: moving close and one CTA.** End on a brief split-screen or actor reveal, then a two-second action card. Use one action only, e.g. “Try the open workflow.” The X post or Media Studio metadata carries the actual link.

### P2 — Format derivatives

1. **16:9 master:** 1920×1080, H.264/AAC, burned or sidecar captions as placement requires.
2. **9:16 social master:** 1080×1920, not a blind crop. Reframe each shot and keep all text inside a conservative shared safe zone. Preview against TikTok's current safe-zone file plus Reels/Shorts overlays.
3. **6–15s teaser:** optional hook-only derivative for X vertical placement or a pinned reply.

## Acceptance checks for v2

- Duration: 22–25s main cut.
- Opening: value proposition clear by 3s; no logo-only/opening-animation delay.
- Structure: hook/body/close with at most three proof cards.
- Legibility: every word readable at mobile scale and inside each platform overlay.
- Audio: `-14` to `-16 LUFS integrated`, `≤ -1 dBTP`, no perceptible VO delay.
- Proof: the video states that the original audio is decoded/restored rather than regenerated, and the supporting evidence identifies each reference role.
- CTA: one action, present in-video and in the post/link metadata.
- QC: repeat the five-role Qwen panel on the full native video, then human-review playback before calling it a keeper.

## Research caveats

- TikTok/Instagram/X do not appear to publish a single exact LUFS specification for organic social video; `-14 LUFS` should not be described as official for those platforms.
- Safe zones change with app version, caption length, and ad add-ons. Use current platform overlay files and a visual preview before export.
- Wistia's first-quarter CTA finding applies to interactive hosted video CTAs, not directly to X/TikTok autoplay posts. It supports early action visibility, but not replacing the social close/CTA entirely.

## Outcome: v5 locked-performance build

On 2026-10-25 the research was implemented as a local HyperFrames composition using all three approved repos:

1. **WhisperX** produced word-level timing for the Drama 3 Voice A narration.
2. **video-use** packed that transcript into phrase ranges and generated filmstrip/waveform checks around the opening and every major cut.
3. **HyperFrames** rendered the final 1920×1080 launch hook.

Final review candidate:

```text
work/recastroom-hook/v5/hyperframes/recastroom-locked-performance-v5-final-16x9.mp4
SHA-256: 4837f100347dbb47cda353a6ebda34492c4479ac067a93746040356d9099d6f5
```

Measured:

- Duration: 23.800 seconds / 714 frames at 30 fps.
- Audio: -13.8 LUFS integrated, 3.9 LU range, -1.5 dBTP true peak.
- HyperFrames final gate: zero lint, runtime, layout, contrast, and craft warnings.

Local Qwen 3.8 27B on the RTX 3090 watched a full-duration 4fps motion proxy plus a 1fps contact sheet. It could not hear audio; its sound section used the WhisperX timing and measured loudness. Its consensus was **7.5/10, SMALL FIX**, emphasizing second-half pacing and CTA specificity. The final render shortened the rights section, moved the proof section 0.6 seconds earlier, extended its scan, and changed the CTA to “Start your first recast.”

The local review artifacts are intentionally outside Git's ignored `work/` tree until the owner approves publication and rights clearance:

- `work/recastroom-hook/v5/hyperframes/REVIEW.md`
- `work/recastroom-hook/v5/review/index.html`
- `work/recastroom-hook/v5/review/qwen_v5_panel_full.md`
- `work/recastroom-hook/v5/review/contact_sheet-final.jpg`

## Superseded by v6b

A later pass applied Motion Video Kit and MotionMaxxing gates to the v5 render. That pass removed persistent footer chrome, eliminated the frozen source tail, added a continuous comparison scan, and reduced the end hold. The superseding artifact is:

```text
work/recastroom-hook/v5/hyperframes/recastroom-locked-performance-v6b-16x9.mp4
SHA-256: 83b810dd404113d045ac01e76e3a802353eaa9d481a5bc032c5000ddeb0350b3
```

See `docs/research/MOTION_VIDEO_REPO_SWEEP_20261025.md` for the full gate evidence.
