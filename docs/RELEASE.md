# Release candidate review guide

This is a local release candidate for RecastRoom Studio `0.1.2`. It is ready for
owner review, but no public repository, tag, social post, submission form, or
remote push is part of this path.

## Reviewer entry points

| Item | Path |
|---|---|
| Exact setup | `docs/QUICKSTART.md` |
| HTTP examples | `docs/API_EXAMPLES.md` |
| App screenshots | `docs/images/app-landing.png`, `docs/images/app-prepared-job.png` |
| Public landing | `/landing.html` |
| Sound-design review | `/sound-lab.html` |
| Walkthrough | `docs/images/app-walkthrough.jpg` |
| Rights policy | `docs/RIGHTS.md` |
| Model/runtime requirements | `docs/PIPELINE.md` |
| Eleven-keeper QC and rights evidence | `docs/KEEPER_EVIDENCE.md` |
| Fail-closed verification transcript | `docs/evidence/slate-verification.md` |
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
python -m pytest -q
recastroom --version
```

Then start the app with the bundled workflow and verify:

```bash
export RECASTROOM_WORKFLOW="$PWD/workflows/openjutsu_h3_lipsync_local.json"
uvicorn app.main:app --port 8768 &
curl --fail http://127.0.0.1:8768/api/health
curl --fail http://127.0.0.1:8768/ >/dev/null
kill %1
```

The health response must report `workflow_exists=true`. No credential or GPU is
used by these gates.

## Eleven-keeper evidence

```bash
python tools/verify_keeper_evidence.py docs/evidence/slate/manifest.json
python tools/selftest_keeper_evidence.py \
  docs/evidence/slate/manifest.json \
  --report work/release/keeper-selftest.txt
```

The immutable verifier must report eleven keepers and forty-eight artifacts. The
self-test additionally proves a one-byte change in a temporary copy fails.

## Reproducible archive

After the release commit is clean:

```bash
python tools/build_release_archive.py \
  --commit HEAD \
  --output work/release/recastroom-studio-v0.1.2-rc.1.zip \
  --receipt work/release/recastroom-studio-v0.1.2-rc.1.receipt.json
```

The tool records the source commit, source Git tree, filtered-content digest,
archive byte size, and archive SHA-256. Build the same commit twice and compare
the two SHA-256 values to reproduce the archive.

## Local tag instruction only

After the owner approves the exact commit and receipt, and only then:

```bash
git tag -a v0.1.2-rc.1 -m "RecastRoom Studio 0.1.2 release candidate 1" <approved-commit>
git show v0.1.2-rc.1 --stat
```

Do not push the branch or tag during candidate preparation. Publication requires
a separate explicit owner instruction.
