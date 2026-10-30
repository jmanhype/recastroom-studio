# RecastRoom Studio

```text
Same take. New lead.
```

RecastRoom Studio is an open-source creative workspace built around **MiniMax H3 Ref2VA**, **ComfyUI**, interchangeable Comfy API workflows, and performance-preserving character replacement. Its supported app and CLI paths require a recorded operator attestation before generation; RecastRoom does **not** verify legal rights, ownership, consent, model licensing, or clearance.

[![RecastRoom public hero: same take, new lead](media/recastroom-hero-poster.jpg)](media/recastroom-public-hero-16x9.mp4)

## Repository layout

![RecastRoom Studio repository map](docs/images/repository-map.svg)

```text
README.md              Product overview and quickstart
RIGHTS.md              Source, likeness, and model rights policy
MODELS.md              Bundled H3 workflow model roles and license boundary
NOTICE                 Copyright, model redistribution, and AI-output notice
setup.sh               Local environment setup
run.sh                 Start the FastAPI studio on 127.0.0.1:8768
app/                   FastAPI server and static web workspace
src/openjutsu/         Python application package
workflows/             Bundled RecastRoom H3 workflow
media/                 Rights-clean public hero and comparison videos
examples/              Input templates and rights attestation example
scripts/               Local trial and CLI helpers
tests/                 Application, API, workflow, and browser regression tests
tools/                 Release and verification utilities
docs/                  Architecture, deployment, and product documentation
```

RecastRoom Studio is a practical answer to Comfy's **#OpenSourceHiggsfield**
challenge: turn “put a different performer into this clip” into a reproducible
local app that people can run, inspect, fork, and improve.

## What it does

RecastRoom Studio helps you:

1. inspect a source clip you own or are licensed to use,
2. reject risky or low-quality shot candidates before GPU time is spent,
3. transcribe word timings with Whisper,
4. build an H3 character-swap prompt,
5. run the production **Recast Room** workflow or import a RecastRoom-compatible Comfy API graph,
6. restore the original dialogue,
7. produce a source/final review artifact.

The studio presents a focused workflow catalog. **Recast Room** is the production path; cinematic camera, re-shoot, and VFX lanes are labeled as concept work rather than production features.

The bundled local workflow uses the RecastRoom H3 performance-preserving graph:

- MiniMax H3 Ref2VA
- BFSShotH3ConditioningSimple
- Character Swap LoRA v1.1 at `1.0`
- Head Swap disabled
- 8-step Turbo
- `source_blur=head + hands (keep mouth)`
- SAM 3.1 source segmentation
- source-audio conditioning
- MiniMax H3 Exact Audio Lock
- exact word/frame schedule

## Three surfaces

| Route | Purpose |
|---|---|
| `/landing.html` | Public overview with the 23.8-second hero video |
| `/` | Production workspace: source, references, attestation, workflow, renderer, and review |
| `/sound-lab.html` | Keeper-video review plus the local Tone.js cue family |
| `/legal.html` | Local-demo privacy, terms, and rights responsibilities |

The public hero is a metadata-clean stream copy of the frozen demonstration master.
Its specifications and hash are recorded in [`media/README.md`](media/README.md).

## Production scope

RecastRoom Studio is a local-first production preview for one-person,
continuous-shot dialogue recasting. It is not a general-purpose hosted video
suite.

Included:

- FastAPI studio and static web workspace
- Local ComfyUI runner
- Official Comfy SDK adapter
- Whisper-compatible word timing
- Rights attestation gate
- Media preflight and review artifacts
- Public landing, sound-design review, and legal surfaces
- Automated application, API, workflow, and browser tests

CI runs on Python 3.11 and 3.12 and executes the full test suite.
Detailed release status is recorded in [`docs/RELEASE_STATUS.md`](docs/RELEASE_STATUS.md).

## Screenshots

| App and readiness | Prepared job |
|---|---|
| ![RecastRoom Studio workflow catalog](docs/images/app-landing-v2.png) | ![RecastRoom prepared job result](docs/images/app-prepared-job.png) |

Readiness detail: [`docs/images/readiness-visual.png`](docs/images/readiness-visual.png)

Full walkthrough contact sheet: [`docs/images/app-walkthrough.jpg`](docs/images/app-walkthrough.jpg)

Demo storyboard: [`docs/images/demo-v1-contact.jpg`](docs/images/demo-v1-contact.jpg)

## Media kit

| Asset | Purpose |
|---|---|
| [24-second showreel](media/recastroom-showreel-24s-16x9.mp4) | Hero plus proof-gallery overview |
| [Six-second 16:9 teaser](media/recastroom-teaser-6s-16x9.mp4) | Fast social hook |
| [Six-second vertical teaser](media/recastroom-teaser-6s-9x16.mp4) | Shorts, Reels, and TikTok hook |
| [Source-versus-recast proof](media/recastroom-proof-9x16.mp4) | Direct before/after proof |
| [Workflow diagram](docs/images/workflow-diagram.png) | Source-to-export pipeline |
| [Architecture diagram](docs/images/architecture-diagram.png) | App/runtime/data boundaries |
| [Media contact sheet](docs/images/media-contact-sheet.jpg) | One-page asset overview |

The full inventory and hashes are in [`media/README.md`](media/README.md).

## Quickstart

Install FFmpeg first. macOS users can run `brew install ffmpeg`; Ubuntu users can run `sudo apt-get install ffmpeg`.

Fastest local path:

```bash
./setup.sh
./run.sh
```

`setup.sh` uses **uv** when available and falls back to standard `venv` + `pip`
otherwise.

`run.sh` listens on `127.0.0.1:8768` by default; override it with `PORT=8897`.

Detailed setup, release verification, and HTTP examples are available in
[`docs/QUICKSTART.md`](docs/QUICKSTART.md),
[`docs/RELEASE.md`](docs/RELEASE.md), and
[`docs/API_EXAMPLES.md`](docs/API_EXAMPLES.md).

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"

export RECASTROOM_COMFY_URL="http://127.0.0.1:8188"
export RECASTROOM_WORKFLOW="workflows/recastroom_h3_workflow.json"

uvicorn app.main:app --reload --port 8768
```

Open:

```text
http://127.0.0.1:8768
```

The public overview is at `/landing.html`; the sound-design review surface is at `/sound-lab.html`.

## CLI

After installing the package, use the `recastroom` entry point.

Inspect a clip:

```bash
recastroom inspect path/to/source.mp4
```

Extract word timings with local Whisper:

```bash
recastroom words path/to/source.mp4 --json path/to/words.json
```

Prepare a runnable workflow:

```bash
recastroom prepare \
  --attest-rights \
  --source source.mp4 \
  --reference-1 character-front.png \
  --reference-2 character-three-quarter.png \
  --identity "the target performer shown in the reference images" \
  --words words.json \
  --output work/prepared.json
```

Queue to a local ComfyUI API:

```bash
recastroom run --attest-rights work/prepared.json
```

The CLI also requires `--attest-rights` before queueing a workflow. This records your representation; it does not investigate ownership or prove consent.

## Architecture

```text
source clip
  -> scene and timing preflight
  -> authorized references
  -> recorded operator attestation
  -> RecastRoom-compatible MiniMax H3 workflow
  -> local ComfyUI or official Comfy SDK runner
  -> original-audio restoration
  -> source/final review artifact and provenance manifest
```

The FastAPI app owns validation and job state. The web client reports readiness and review state without claiming an automated quality score. FFmpeg handles probing, remuxing, and review renders. The bundled workflow keeps identity, performance, scene, and audio as separate responsibilities.

## Rights policy

RecastRoom Studio is for clips you own, clips you are licensed to use, or clips you have explicit permission to modify.

The UI requires an operator attestation before a job can start. The repository must not ship:

- unlicensed film or television footage,
- celebrity or public-figure likenesses without consent,
- clips of deceased performers without estate consent,
- non-consensual sexual, political, harassing, or deceptive media.

See [`RIGHTS.md`](RIGHTS.md) and [`examples/RIGHTS_ATTESTATION.md`](examples/RIGHTS_ATTESTATION.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Renderer disconnected` | Start ComfyUI and confirm `RECASTROOM_COMFY_URL` points to it |
| Preparation returns 422 | Check that the source is a supported video and the rights box is checked |
| Whisper timing fails | Confirm the CLI can read the file and that it contains audible speech |
| Browser preview is blank | Use an MP4 or MOV preview; server preflight can still inspect other supported containers |
| SDK run reports missing credentials | Set `COMFY_API_KEY` and `COMFY_BASE_URL` for the configured deployment |

## Limitations

- RecastRoom does not prove legal clearance; it records your attestation.
- The public demo path still requires rights-clear source footage and references.
- Hosted Comfy SDK execution needs owner credentials and a configured deployment.
- Visual and audio quality remain human review gates; no automated score replaces playback.
- The current production graph is tuned for one-person continuous dialogue shots, not arbitrary multi-shot scenes.

## Contest alignment

RecastRoom Studio is built for Comfy's **#OpenSourceHiggsfield** challenge as
one focused, performance-preserving MiniMax H3 recasting studio: one owned or
licensed continuous dialogue shot, authorized references, word-level timing,
original-audio restoration, rights gating, and a reproducible Comfy workflow.
It is not an attempt to recreate every feature of a broad commercial video
platform.

The public demo must use owned, licensed, or original footage. The private film/TV experiments that informed the workflow will not be included in the repository.
