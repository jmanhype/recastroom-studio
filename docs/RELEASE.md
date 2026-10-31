# Release candidate review guide

This is a local release candidate for RecastRoom Studio `0.3.5`. It is ready
for owner review. The public repository may already exist, but no `v0.3.5` tag,
public release, social post, submission form, or remote push is part of this
path.

## Reviewer entry points

| Item | Path |
|---|---|
| Exact setup | `docs/QUICKSTART.md` |
| HTTP examples | `docs/API_EXAMPLES.md` |
| App screenshots | `docs/images/app-workspace.png`, `docs/images/readiness-visual.png`, `docs/images/app-prepared-job.png` |
| Public landing | `/landing.html` |
| Sound-design review | `/sound-lab.html` |
| Walkthrough | `media/recastroom-user-journey-8s-16x9.mp4` |
| Rights policy | `RIGHTS.md` |
| Model/license boundary | `MODELS.md` |
| Copyright and AI-output notice | `NOTICE` |
| Public media manifest | `media/README.md` |
| Public media contact sheet | `docs/images/media-contact-sheet.jpg` |
| Workflow diagram | `docs/images/workflow-diagram.png` |
| Architecture diagram | `docs/images/architecture-diagram.png` |
| One-command setup | `setup.sh` |
| Local studio launcher | `run.sh` |
| Model/runtime requirements | `docs/PIPELINE.md` |
| Archived evidence verifier | `docs/evidence/slate-verification.md` |
| Architecture | `docs/ARCHITECTURE.md` |

## Public-content audit

The release audit checks release paths, credential-like assignments, absolute
user paths, private network addresses, cached private-reference markers, media
container tags, the bundled workflow plan, and MIT SPDX coverage. Run it from an
unpacked release archive (not the development repository):

```bash
python tools/audit_release.py --root . --report work/release/audit.txt
```

The final line must be `PASS: release audit`.

The development repository intentionally retains Paivot/nd control files and
contest initialization tools. The archive builder excludes those local-only
paths; they are not deleted from source control. The twenty-two evidence MP4s
are stream-copy remuxes with identical video/audio packet hashes, updated
container receipts, and no cached private-reference workflow metadata. Weights,
custom nodes, and hosted credentials are not bundled.

## Required local gates

Run from a clean checkout or unpacked archive:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[dev]"
python -m pip check
node --check app/web/landing.js
node --check app/web/sound-lab.js
node --check app/web/studio.js
node --check app/web/m1.js
python -m pytest -q
recastroom --version
```

Then start the app in default preview mode and verify:

```bash
export RECASTROOM_WORKFLOW="$PWD/workflows/recastroom_h3_workflow.json"
RECASTROOM_BACKEND=dry_run uvicorn app.main:app --port 8768 &
curl --fail http://127.0.0.1:8768/api/health
curl --fail http://127.0.0.1:8768/ >/dev/null
kill %1
```

The health response must report `workflow_exists=true` and `backend=dry_run`.
No credential or GPU is used by these gates.

## Archived evidence verifier

```bash
python tools/verify_keeper_evidence.py docs/evidence/slate/manifest.json
python tools/selftest_keeper_evidence.py \
  docs/evidence/slate/manifest.json \
  --report work/release/keeper-selftest.txt
```

The immutable verifier must report the expected archived set and artifact count.
The self-test additionally proves a one-byte change in a temporary copy fails.

## Reproducible archive

After the release commit is clean:

```bash
python tools/build_release_archive.py \
  --commit HEAD \
  --output work/release/recastroom-studio-v0.3.5.zip \
  --receipt work/release/recastroom-studio-v0.3.5.receipt.json
```

The tool records the source commit, source Git tree, filtered-content digest,
archive byte size, and archive SHA-256. Build the same commit twice and compare
the two SHA-256 values to reproduce the archive.

## Design-process credit

The v0.3.5 landing redline process was guided by Damir Sokolovsky’s
[unslop](https://github.com/heydamir/unslop) skill, licensed CC BY 4.0. No
unslop application code or media was copied into RecastRoom.

## Local tag instruction only

After the owner approves the exact commit and receipt, and only then:

```bash
git tag -a v0.3.5 -m "RecastRoom Studio 0.3.5" <approved-commit>
git show v0.3.5 --stat
```

Do not push the branch or tag during candidate preparation. Publication requires
a separate explicit owner instruction.
