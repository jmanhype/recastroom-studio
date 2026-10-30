# RecastRoom Studio — local evidence snapshot, 2026-10-30 UTC

M1 native browser proof at tested SHA `1ad5c82aaa027a1c1034ff7c7cec183d0d2cab6f`:
`APP/.venv/bin/python -m pytest -q` returned **393 passed, 1 known Starlette
deprecation warning**, exit 0 in each managed/ordinary inherited/strict environment.
The pinned `openjutsu-cpu-routing-windows-v1-20261027` table qualifies only measured
CPU routing here; CPU dry-run and retained replay remain non-inference/offline evidence.
[Receipts and hashes](docs/evidence/recastroom-m1/final-20261030/README.md) distinguish
real known-ID local recovery from the explicitly offline unknown-state presentation fixture.
Independent PM/Anchor acceptance and the coordinator's actual post-merge gate remain separate.
Whole-epic historical TDD preflight has 22 unmarked test-edit commits requiring Anchor
applicability review; the scoped capstone authorization check passed. No history was rewritten.
Live H3/provider qualification, deployment and publication remain **OWNER_BLOCKED**.

---

# Historical record — Openjutsu Studio status, 2026-10-16

Everything below is preserved historical reporting, not a current readiness or legal-enforcement claim.

## Completed in this pass

- Created MIT-licensed project package.
- Added Python package metadata and clean-install configuration.
- Added FastAPI web UI.
- Added the operator attestation gate.
- Added media preflight using `ffprobe`.
- Added Whisper word-timing parser.
- Added one-based frame schedule generator.
- Added the authorized-reference prompt contract.
- Added 28-node MiniMax H3 Ref2VA workflow mutation.
- Packaged the accepted lip-sync graph:
  - Character Swap `1.0`
  - Head Swap `0.35`
  - 8-step Turbo
  - `with_audio=true`
  - `source_blur=off`
  - seed `49`
- Added local ComfyUI upload/queue/history/download runner.
- Added official Comfy SDK adapter.
- Added app endpoints:
  - prepare job,
  - run job,
  - job status,
  - workflow download,
  - prompt download,
  - artifact download.
- Added ffmpeg helpers:
  - normalize to 24 fps,
  - contact sheet,
  - source-audio restoration,
  - source/final side-by-side.
- Added contest plan, demo plan, rights documentation, architecture docs, and submission checklist.

## Verified

```text
5 passed
```

Clean virtual-environment checks:

```text
pip install -e .
pip install -r requirements.txt
pip check → No broken requirements found
python scripts/openjutsu.py --version → 0.1.0
```

Web API smoke test:

```text
GET  /api/health                         200
GET  /                                  200
POST /api/prepare                        200
GET  /api/jobs/{id}/workflow             200
GET  /api/jobs/{id}/prompt               200
```

Synthetic preflight:

```text
960×384
24 fps
6.0 seconds
audio present
recommended=true
```

## Not done yet

- No human source plate with recorded operator authority yet.
- No fresh H3 generation using a fully documented permission record yet.
- Official Comfy SDK path is implemented but not live-smoke-tested because it requires a configured Comfy Developer Platform deployment and API key.
- No public GitHub repository or release yet.
- No deployed app yet.
- No two-minute demo video yet.
- No Typeform submission yet.

## Contest deadline

```text
October 30, 2026, 9:00 AM PT
```

## Source snapshot

Staged Git archive:

```text
work/openjutsu-studio-v0.1.0.zip
```

SHA-256:

```text
c8b55c576c3b05a6eade6b02269b196d49d504fa7a7eb778bd4e40681557998e
```

# Update — 2026-10-17

## Synthetic Plan B production

The synthetic performer path is now complete and human-approved:

- Synthetic Plate A generated natively.
- Seed 50 Jay core swap completed and human-approved.
- Eleven keeper candidates cover every approved format concept.
- Whisper recovered every intended line exactly.
- Qwen video QC passed the repaired keeper set.
- The optional anime variant was rejected because the core H3 graph converted
  the cel-shaded reference to photoreal.

Human approval receipt:

```text
work/openjutsu_planb/slate_keepers/HUMAN_APPROVAL.md
```

Machine-readable keeper manifest:

```text
work/openjutsu_planb/slate_keepers/SLATE_KEEPERS.json
```

## Demo v1

`openjutsu-demo-v1.mp4` replaces demo v0's 40-second app-placeholder segment
with an actual local Openjutsu Studio walkthrough:

- upload the synthetic source,
- add two performer references,
- add Whisper word timings,
- enter identity and seed,
- attest rights,
- prepare the job,
- inspect the returned workflow/prompt URLs.

Verified specs:

```text
1152×768
2590 video frames
108.052 seconds
stereo AAC
integrated loudness −17.15 LUFS
true peak −1.50 dBTP
```

SHA-256:

```text
7cbe824a3e7dc4ff515c23fe1672630e938e2520e9b7c3686c87fa90a4db089d
```

## Local app/API smoke — reproduced

```text
python -m pytest -q
5 passed

pip check
No broken requirements found

GET /api/health
200

GET /
200

POST /api/prepare
200

GET /api/jobs/{id}/workflow
200

GET /api/jobs/{id}/prompt
200
```

The UI walkthrough was driven in a real browser using the bundled synthetic
test source, both synthetic references, the example word schedule, identity
text, seed 50, and the operator attestation gate.

## Remaining blocker

The official Comfy SDK execution path still requires a configured Comfy
Developer Platform deployment and `COMFY_API_KEY`. No Comfy API key is present
in the current environment. Instantiating `ComfySdkRunner(api_key=None)` fails
closed with `MissingApiKey`, as expected.

## v0.1.1 clean-checkout verification

Clean non-editable install from the packaged tree:

```text
7 passed
No broken requirements found
openjutsu --version → 0.1.1
GET /api/health → 200, workflow_exists=true
GET / → 200
```

This pass found and fixed a normal-install path bug: the app previously
derived the bundled workflow from the installed module path and reported
`workflow_exists=false` outside an editable checkout. `load_settings()` now
prefers a repository-root workflow when Openjutsu is run from a checkout and
resolves relative environment paths from the current directory.

The final v0.1.1 archive and tree hash are recorded outside the archive in
`work/openjutsu_planb/RELEASE_RECEIPTS.md`; a self-contained archive cannot
embed its own final SHA-256 without changing that hash.
