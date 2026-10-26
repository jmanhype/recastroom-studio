# Dogfood repair intake -- 2026-10-17

## Decision

The owner approved exactly three bounded repairs from the measured dogfood run:

1. Preserve the complete intrinsic geometry of portrait performer previews.
2. Preserve aspect ratio in paired review by scale-fitting and padding rather than stretching.
3. Preserve source-audio channel layout and loudness when restoring original speech.

This intake changes only the live Paivot/nd backlog and this receipt. It makes no application-source change, claims no repair test result, and does not redesign generation, APIs, or coarse progress reporting.

## Measured evidence

Read-only evidence is under `../frontend-evidence/dogfood-20261017/live/`:

- `REPORT.md` records the real job, defects, and local shutdown evidence.
- `browser-playback.json` records the 1086x1448 portrait rendering as 283x377.328 inside a clipped 285x150 container.
- `output-verification.json` records:
   - final video: 768x512, DAR 3:2, SHA-256 `f9091b391c96daf28697f46ba49263450112f70d1732fa26dcea73ccdadd2f98`;
   - paired review: 1920x384, DAR 5:1, SHA-256 `b2f61d3c292e53846f62bed6460d2b0517cbee7fd91c4b5d2f477aec84da613d`;
   - stereo source restored as 5.1, final/source mono gain `0.41418053682187445`, correlation `0.9999677326692922`, and equal 282,624-sample decoded length.

Correlation and nonzero audio prove related speech content, not preserved layout or loudness. That distinction is carried into the audio story.

## Current code references

These are intake observations, not test claims:

- At story/OJ-4rht revision `63b9c005e64fcfa0bdba04ee798acaedd79450e7`, `app/web/studio.js:159-160` freezes only the read-only `errorText` and `getState` seams. Stage, prepare, status, and reset behavior is private/event-driven.
- At main `7ab3b8c9adfe807c58a1139a8314973b6def64a4`, `src/openjutsu/media.py:156-198` scales both paired inputs to fixed 960x384 tiles. `src/openjutsu/media.py:105-153` and `181` force `aformat=channel_layouts=5.1`.

## Tracker changes

All changes were made through Paivot/nd operations against the shared live vault.

| Issue | Bounded change |
| --- | --- |
| `OJ-a7l6` | Expanded the epic scope to the three owner-approved local repairs and explicitly excluded generation/API, progress-UX, GPU, paid API, cloud, publication, and push work. |
| `OJ-4rht` | Retained the stale map as history and added an authoritative map for the real private/event-driven flow plus read-only `getState`/`errorText`. Added AC #9 for complete intrinsic portrait/landscape previews while retaining original AC #1-8 and the prior PM rejection. |
| `OJ-xtk4` | New atomic bug: paired review must scale-fit/pad with even dimensions and no stretch; regressions cover 3:2, portrait, 16:9, and mixed aspect pairs. |
| `OJ-inuo` | New atomic bug: restored final/comparison audio must preserve mono/stereo/5.1 layout and measured original-speech loudness; forced 5.1, silent channels, and correlation-only proof are insufficient. |
| `OJ-yf2c` | Reconciled consumption to real UI events plus read-only observation seams, rather than nonexistent mutation methods. AC #6 now distinguishes private raw evidence from sanitized checked-in receipts. |

Dependency ownership is:

- `OJ-xtk4` blocks `OJ-inuo` because both stories must edit `src/openjutsu/media.py`; this serializes shared-file ownership.
- `OJ-4rht`, `OJ-xtk4`, and `OJ-inuo` all block capstone `OJ-yf2c`.

At intake close, `OJ-4rht` and `OJ-xtk4` remained independently claimed for rework/repair. `OJ-inuo` and `OJ-yf2c` remained open and blocked. No story was accepted or closed, and the `OJ-4rht` rejected label and PM decision remain in place.

## Private evidence policy

Private raw CUA/browser evidence may remain outside the Git repository and retain absolute local paths for provenance. Checked-in receipts must sanitize user-specific and public paths, retain hashes and artifact identity, identify commands and limitations, and prevent credential/public leakage. The corrected `OJ-yf2c` AC #6 records this distinction; provenance is not suppressed.

## Verification

- `pvg nd doctor`: all 15 issues passed validation.
- `pvg lint --backlog --epic OJ-a7l6`: passed with 0 errors and 30 nonblocking review findings (retained duplicate/history sections and local-only integration warnings).
- `pvg nd sync --no-push`: `nd/backlog` up to date at local commit `905b666d`; no remote was contacted.
- No GPU, paid API, cloud inference, publication, push, source repair, or repair-test execution was performed by this intake.

Live tracker-file SHA-256 values at intake close:

- `OJ-a7l6`: `ec3f83946a4bb974687e3da0ab5b5817cc23d1491b06567b9aaab2d9d408fd98`
- `OJ-4rht`: `414547393fff2840bf46c92bc547cb580d5d49202ab3a7a3eaee43d16b08154c`
- `OJ-xtk4`: `ffaebbbb46cb5269affeb718ce951af7cfb88e79256ad3da40470eeeac32ea6f`
- `OJ-inuo`: `9844040c339d29726dfde4d572eb1a498ca7d544ed5ddbba37e5008850e7aa9e`
- `OJ-yf2c`: `1ea73cd36434bf44e4034b9f5fb2c875b6a2d9802faf52513c659dc820aa7d60`
