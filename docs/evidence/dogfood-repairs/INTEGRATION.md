# Three bounded dogfood repairs — local integration

Verified 2026-10-18 UTC. No new generation, public deployment, or push.

## Accepted and merged

- OJ-4rht portrait preview: accepted source/evidence HEAD `6ca79a5`; merge `4374d1d`.
- OJ-xtk4 aspect-preserving comparison: accepted HEAD `415e3d5`; merge `cda27bc`.
- OJ-inuo source audio layout: accepted HEAD `5304b7a`; merge `c5dbe8c`.
- Integrated code commit: `c5dbe8cb338e5ce2a5414493af047decb0412396`.

The dispatcher used local `git merge --no-ff` after independent PM acceptance
because `pvg story merge` requires an absent origin remote. Shared nd state was
reopened and all three stories were closed/accepted. `pvg nd sync --no-push`
confirmed local backlog durability. Nothing was pushed.

## Integration verification

```sh
PYTHONPATH=src "$ROOT_VENV/bin/python" -m pytest -q
git diff --check
```

**41 passed, 1 pre-existing Starlette/httpx warning in 21.42s** on the merged
checkout. Raw private `integration-all-repairs.txt` SHA-256:
`326f5c5c2aa42b34b6b1fbd4e737a8ebf21bf4a86c7000f186d07db4cadcd74a`.

The earlier pre-audio integration attempt was invalidated by ENOSPC:
1 failed, 23 passed, 14 errors. Safe UV package-cache cleanup removed 1.3 GiB;
the pre-audio rerun then passed 38 tests, followed by the 41-test runs above.
No models, original media, project files, or existing outputs were deleted.

## Live local app and portrait proof

The loopback review app at `http://127.0.0.1:8893/` was restarted from the accepted
epic checkout with the same data directory and legacy backend. Health returns
`ok=true`, workflow exists. The former Colab forward remains offline; this is
only the local application server, not a new GPU session.

The already-open browser tab retained the old CSS until refreshed. Before
refresh, the portrait's intrinsic grid minimum was `auto`; afterward both minima
were `0px`, its displayed box was 283x148 with `object-fit:contain`, and the full
1086x1448 portrait was visible. Source and Jay reference were reselected locally;
rights stayed unchecked and Prepare disabled. No job was submitted.

Private focused screenshot `portrait-fixed-detail.png` SHA-256:
`afecd87d263b5deb45f6fa4d76ecc2fce62825d5ec8cd2bb80f179af61433452`.
Prior desktop/mobile, keyboard, reduced-motion and dry-run evidence remains in
the accepted OJ-4rht receipt; this refresh does not claim new exhaustive QA.

## Corrected exports, not a new render

Original job `61721c5f2c27` and its files remain unchanged. Its old final artifact
still downloads through the app with SHA-256
`f9091b391c96daf28697f46ba49263450112f70d1732fa26dcea73ccdadd2f98`.

Separate corrected files were created from the original source and existing
generated MP4 under private `dogfood-repairs-20261017/repaired/`:

- `final_audio_fixed.mp4`: 768x512, 141 frames, 24fps;
  `f69e776234249ee45dfbea199aba49adbd8d9c7c5a261ae7fd0d63329a9130c9`.
- `comparison_aspect_fixed.mp4`: 1536x512, square pixels, two 768x512 tiles;
  `062b8f59140981e0eefcf4be69958fc77fcdd5249fc65e0fe7594d4e107fb2a5`.

Both retain stereo/48kHz and 282,624 samples/channel. Measured RMS change is
approximately -0.00065545 dB; zero-lag correlation approximately 0.99999903.
Independent PM decoded and verified these results. The private verification
JSON and SHA256SUMS pass hash checks. This is **export/audio preservation**, not
an identity, creative-quality, or phoneme-sync verdict.

## Remaining boundary

OJ-yf2c, the broader frontend negative/race-state/browser capstone, is ready but
not executed or accepted here. The epic remains open; source integration is on
its local epic branch, not a production-release claim. `bd sync --from-main`
reports no Beads database; existing shared nd remains the tracker, with no new
competing database initialized.
