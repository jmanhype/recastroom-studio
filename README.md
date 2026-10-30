# RecastRoom Studio

```text
Same take. New lead.
```

RecastRoom Studio changes the on-screen performer in a clip you have permission
to edit, while preserving the original performance, camera, scene, and dialogue.
It runs MiniMax H3 through ComfyUI on your own machine.

[![RecastRoom public hero: same take, new lead](media/recastroom-hero-poster.jpg)](media/recastroom-public-hero-16x9.mp4)

## See it work

These previews autoplay on GitHub. No click is required.

| Studio walkthrough | Result preview |
|---|---|
| ![RecastRoom studio walkthrough](media/previews/user-journey-16x9.webp) | ![RecastRoom result preview](media/previews/result-teaser-16x9.webp) |

The studio walkthrough shows the normal user path:

1. inspect the source,
2. add references and word timing,
3. record permission,
4. prepare the workflow,
5. review the prepared job.

The result preview shows the finished user outcome: the source performance stays
in place while the lead changes.

Full-length version: [`recastroom-user-journey-8s-16x9.mp4`](media/recastroom-user-journey-8s-16x9.mp4)

### Vertical preview

![RecastRoom source-versus-recast vertical preview](media/previews/source-vs-recast-9x16.webp)

RecastRoom Studio is a practical answer to Comfy's **#OpenSourceHiggsfield**
challenge: turn “put a different performer into this clip” into a reproducible
local app that people can run, inspect, fork, and improve.

## What it does

RecastRoom Studio helps you:

1. review an original clip you own or have permission to edit,
2. check clip quality before spending render time,
3. add the new lead and dialogue timing,
4. prepare the RecastRoom MiniMax H3 job,
5. run locally or through a compatible Comfy setup,
6. keep the original dialogue,
7. compare the before and after result.

The studio presents a focused workflow catalog. **Recast Room** is the production path; cinematic camera, re-shoot, and VFX lanes are labeled as concept work rather than production features.

The bundled workflow preserves:

- the original performance,
- camera and background,
- dialogue timing,
- the new performer’s identity,
- a frame-by-frame before/after review.

Exact model files and settings are documented in [`MODELS.md`](MODELS.md).

## The production workspace

RecastRoom opens directly into one workspace for reviewing the original clip,
adding the new lead, confirming permission, preparing the job, running it, and
checking the result.

The public overview, sound-design review tool, and legal notes are support
pages linked from the app footer. They are not separate products or separate
user journeys.

The public hero is a metadata-clean stream copy of the frozen demonstration master.
Its specifications and hash are recorded in [`media/README.md`](media/README.md).

## Production scope

RecastRoom Studio is a local-first production preview for one-person,
continuous-shot dialogue recasting. It is not a general-purpose hosted video
suite.

Included:

- one studio workspace
- local ComfyUI rendering
- optional hosted Comfy connection
- automatic dialogue timing
- a permission checkpoint
- clip checks and before/after review
- public overview and local review tools
- automated application, API, workflow, and browser tests

CI runs on Python 3.11 and 3.12 and executes the full test suite.
Detailed release status is recorded in [`docs/RELEASE_STATUS.md`](docs/RELEASE_STATUS.md).

## User interface

| Choose the workflow | Check readiness | Prepared job |
|---|---|---|
| ![RecastRoom Studio workflow catalog](docs/images/app-landing-v2.png) | ![RecastRoom readiness strip](docs/images/readiness-visual.png) | ![RecastRoom prepared job result](docs/images/app-prepared-job.png) |

Older full walkthrough contact sheet: [`docs/images/app-walkthrough.jpg`](docs/images/app-walkthrough.jpg)

Demo storyboard: [`docs/images/demo-v1-contact.jpg`](docs/images/demo-v1-contact.jpg)

## Downloadable media

### Full-length showreel

[![RecastRoom 24-second showreel](media/posters/showreel-16x9.webp)](media/recastroom-showreel-24s-16x9.mp4)

### Vertical result

[![RecastRoom vertical hero](media/posters/hero-9x16.webp)](media/recastroom-hero-9x16.mp4)

### Source-versus-recast proof

[![Source versus recast proof](media/posters/proof-9x16.webp)](media/recastroom-proof-9x16.mp4)

### Additional user previews

| 16:9 | Vertical | Square |
|---|---|---|
| [![16:9 teaser](media/posters/hero-16x9.webp)](media/recastroom-teaser-6s-16x9.mp4) | [![Vertical teaser](media/posters/hero-9x16.webp)](media/recastroom-teaser-6s-9x16.mp4) | [![Square teaser](media/posters/teaser-square.webp)](media/recastroom-teaser-6s-square.mp4) |

### Diagrams

| Workflow | Architecture | Media overview |
|---|---|---|
| [![Workflow diagram](docs/images/workflow-diagram.png)](docs/images/workflow-diagram.png) | [![Architecture diagram](docs/images/architecture-diagram.png)](docs/images/architecture-diagram.png) | [![Media contact sheet](docs/images/media-contact-sheet.jpg)](docs/images/media-contact-sheet.jpg) |

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

Advanced setup, release verification, and HTTP examples are available in
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

The app opens directly into that workspace. Public overview and legal notes are
linked in the footer.

## Repository guide

![RecastRoom Studio repository map](docs/images/repository-map.svg)

```text
README.md              Product overview and quickstart
RIGHTS.md              Source, likeness, and model rights policy
MODELS.md              Model files, roles, and licenses
NOTICE                 Copyright, model redistribution, and AI-output notice
setup.sh               Local environment setup
run.sh                 Start the FastAPI studio on 127.0.0.1:8768
app/                   FastAPI server and static web workspace
src/openjutsu/         Python application package
workflows/             Bundled RecastRoom H3 workflow
media/                 Public hero and comparison videos
examples/              Input templates and permission example
scripts/               Local trial and CLI helpers
tests/                 Application, API, workflow, and browser regression tests
tools/                 Release and verification utilities
docs/                  Architecture, deployment, and product documentation
```

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

The CLI also requires `--attest-rights` before queueing a workflow. This records
your permission confirmation; it does not investigate ownership or prove consent.

## Architecture

```text
original clip
  -> clip and timing check
  -> new lead reference
  -> permission confirmation
  -> RecastRoom MiniMax H3 workflow
  -> local or hosted Comfy rendering
  -> original dialogue restored
  -> before/after review and job summary
```

The FastAPI app owns validation and job state. The web client reports readiness and review state without claiming an automated quality score. FFmpeg handles probing, remuxing, and review renders. The bundled workflow keeps identity, performance, scene, and audio as separate responsibilities.

## Rights policy

RecastRoom Studio is for clips you own, clips you are licensed to use, or clips you have explicit permission to modify.

The UI requires permission confirmation before a job can start. The repository must not ship:

- unlicensed film or television footage,
- celebrity or public-figure likenesses without consent,
- clips of deceased performers without estate consent,
- non-consensual sexual, political, harassing, or deceptive media.

See [`RIGHTS.md`](RIGHTS.md) and [`examples/RIGHTS_ATTESTATION.md`](examples/RIGHTS_ATTESTATION.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| Render connection unavailable | Start ComfyUI and confirm `RECASTROOM_COMFY_URL` points to it |
| Preparation returns 422 | Check that the clip is supported and the permission box is checked |
| Dialogue timing fails | Confirm the CLI can read the file and that it contains audible speech |
| Browser preview is blank | Use an MP4 or MOV preview; the server can still inspect other supported containers |
| Hosted run reports missing credentials | Set `COMFY_API_KEY` and `COMFY_BASE_URL` for your hosted Comfy setup |

## Limitations

- RecastRoom does not prove legal clearance; it records your permission confirmation.
- The public demo path still requires footage and references you are allowed to use.
- Hosted rendering needs your credentials and configured deployment.
- You approve the final video and audio; no automated score replaces playback.
- The current workflow is tuned for one person in one continuous dialogue shot, not arbitrary multi-shot scenes.

## Contest alignment

RecastRoom Studio is built for Comfy's **#OpenSourceHiggsfield** challenge as
one focused MiniMax H3 recasting studio: one permitted continuous dialogue shot,
the new lead’s reference, dialogue timing, original-audio restoration, a
permission checkpoint, and a reproducible Comfy workflow.
It is not an attempt to recreate every feature of a broad commercial video
platform.

The public demo must use owned, licensed, or original footage. The private film/TV experiments that informed the workflow will not be included in the repository.
