# Final submission packet — PUBLIC REPOSITORY / CONTEST FORM NOT FILED

The public GitHub repository is live and uses a filtered release history. The
public X post, Typeform receipt, hosted try URL, and final two-minute demo are
still owner-gated. This packet is an offline assessment, not publication
authority for those remaining actions. Final-gate matrices are commit-bound,
not permanent authority: tracked receipts identify their exact evaluated
revisions, and later corrections are not implicitly covered by older evidence.
Official baseline: `CONTEST.md` and `SUBMISSION_CHECKLIST.md`.

## Repeat the local gate

From an installed checkout, set `DEMO` to the known demo-v1 candidate and use
a fresh output directory (the tool refuses overwriting prior evidence):

```bash
DEMO="../openjutsu_planb/demo_v1/recastroom-demo-v1.mp4"
python tools/final_submission_gate.py --commit HEAD --demo "$DEMO" --output work/final-gate
```

The current rebranded demo candidate SHA-256 is
`a14b3eb287e3daf0ed4dd27e238048c1725c087c0b48cf8ffb301758e637f13f`.

A fresh-environment install and loopback launch proof for source package
`8a5f376` is in
[`evidence/clean-install-8a5f376/REPORT.md`](evidence/clean-install-8a5f376/REPORT.md).
The owner must still repeat the check on the exact final public commit.

The official Comfy API proof is a successful full RecastRoom C1 render through
`ComfySdkRunner`:
[`evidence/comfy-api-sdk-c1-20261030/README.md`](evidence/comfy-api-sdk-c1-20261030/README.md).
The earlier no-model Cloud smoke remains preliminary transport evidence at
[`evidence/comfy-sdk-smoke-20261025/REPORT.md`](evidence/comfy-sdk-smoke-20261025/REPORT.md).

It extracts the selected Git commit, filters local control files, audits public
content/headers/metadata/credential patterns and paths, verifies keepers, builds
the archive twice, runs the complete tests and pip consistency check in the
extracted package, and probes only the hash-allowlisted demo. No install,
credential lookup, external request, GPU or cloud job is made. In-process app
tests exercise dry-run upload-to-output; loopback binding and exposure-scan
tests cover deployment constraints. The earlier real loopback deployment
receipt is `evidence/OJ-2t3g-local-trial/receipt.json`, not a public deployment.

Exit 0 means eligible; 1 means failed local check; 2 means owner-blocked.
Missing tools, malformed evidence and timeouts fail closed. Each child check
has a 240-second timeout; ffprobe has 30 seconds. Retain failed evidence and
retry into a new directory only after diagnosing the cause.

## PRE-PUBLICATION STOP (owner only)

1. Review the matrix and archive SHA-256. Resolve every FAIL and mandatory
   OWNER_BLOCKED item. Optional deployment may be explicitly waived in an
   owner-signed receipt, never misrepresented as deployed. The current gate
   intentionally cannot auto-clear publication/rights/live-SDK blockers from
   arbitrary pasted URLs. A follow-up reviewed evidence update is required.
2. Verify the official rules/deadline from the contest link in `CONTEST.md`;
   recorded deadline is October 30, 2026, 9:00 AM PT. Confirm the official
   Typeform destination by following that page; do not guess its URL.
3. Complete the owner-authorized SDK smoke described in
   `evidence/OJ-i6n6-comfy-sdk.md`; retain redacted job ID, workflow/output
   hashes and timings. Credentials stay outside repository and evidence.
   Missing live platform proof is a blocker, not a risk waiver that passes.
4. Approve the demo's exact timeline/audio provenance and consent, third-party
   model/node licenses and final repository URL card. Re-probe any changed
   bytes. Check all source/final comparison, contact sheet, word timings and
   QC receipts in the keeper manifest; visually review the final exported demo.
5. Unpack the audited ZIP into an empty directory. Follow `QUICKSTART.md` in a
   fresh virtual environment, install `.[dev]`, run `pip check`, full pytest,
   and `recastroom --version`. Run the loopback trial below. Archive the output
   and exact commit/hash. Existing environment tests do not prove clean install.

## Public repository history boundary

Do not push the development history: it contains local control artifacts that
are excluded from public archives. Continue public changes from the filtered
public history or rebuild from a newly audited archive. Before publishing any
future archive, verify the repository, LICENSE, setup, workflow, screenshots,
examples and tag while signed out. Publish the approved demo as a release asset
or owner-controlled video page, then download it and compare SHA-256. Never
include local paths, secret values or private media.

## Owner-only X post and Typeform

Unpublished X draft (fill real verified links, upload the approved video):

> RecastRoom Studio: an open-source, attestation-gated MiniMax H3 recasting app with
> a usable UI and downloadable Comfy workflow. Source: [verified repo link].
> Demo: [verified demo link]. #OpenSourceHiggsfield

Do not claim dry-run copies are live model generation. Preview the native
video, audio, hashtag and links, then post only after owner approval. Save the
final post URL and verify it signed-out. Do not alter the account profile.

Open Typeform only through the official contest page. Enter app name, concise
description, public repository, approved demo, public hashtag post, applicable
categories, and optional deployed link only if actually available. Review every
field and terms; stop before the final Submit button until all gates pass and
the owner explicitly approves submission. Save the confirmation/receipt ID,
timestamp and submitted URLs after submitting; a filled form is not a receipt.

## Owner-only local/VPN reviewer trial, timeout and rollback

```bash
python scripts/local_trial.py --host 127.0.0.1 --port 8890 --output-dir work/owner-trial
RECASTROOM_BACKEND=dry_run RECASTROOM_DATA_DIR="$PWD/work/owner-review" \
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8890
```

Confirm health shows dry_run/workflow present and exercise synthetic upload,
rights rejection/attestation, prepare, run and complete output. For a remote
reviewer, keep the service loopback-bound and first establish an owner-managed
authenticated VPN/proxy with per-person authentication, 60 requests/minute,
100 MiB upload limit, access logs and review-end deletion. Test denial from an
unauthorized client before allowing a reviewer. Never expose an unauthenticated
tunnel or bind all interfaces. If this boundary cannot be verified, share only
the reproducible local instructions; optional deployed URL remains absent.

Stop on readiness/job timeout or errors; preserve sanitized receipts, stop the
specific trial/server process, disable VPN/proxy access and quarantine only the
review data directory after confirming its path. Do not retry model/cloud work
automatically. If publication hangs, inspect signed-out GitHub/X/form state
before retrying to prevent duplicates. If an upload hash or public content
fails verification, stop submission, remove the faulty release asset/post or
make the new repository private, revoke exposed credentials if any, and record
the incident. A form already submitted cannot be assumed reversible: use the
official organizer correction/withdrawal channel and keep its receipt.

**Do not submit while any gate fails or any mandatory owner blocker remains.**
