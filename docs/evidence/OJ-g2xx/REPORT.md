# OJ-g2xx — current judge-facing package assessment

Date: 2026-10-18
Base: `0e8e3fb8808e9518c2ece8224c900378747924cc` (tree
`0e06c565932308470532e7995424cd43ab118a32`)
Scope: local evidence/package assessment only. No credential, cloud/GPU,
publication, X, or Typeform operation was performed.

## Verdict

Openjutsu has a strong local candidate for one focused, performance-preserving
MiniMax H3 recasting studio, but it is not submit-ready. The exact remaining
owner blockers are:

1. live Comfy Developer Platform execution proof,
2. public audited repository and demo,
3. public X post with the verified links,
4. Typeform submission through the official contest page.

An optional deployed try link is not a blocker. The latest final-gate receipts
predate the current base commit, so they are useful evidence of the gate design
and prior candidate quality, not certification of this exact tree.

## Rule hierarchy

### Current official signals

The submission plan follows the official contest page:
<https://comfy.org/open-source-higgsfield/>. Its material expectations are:

- one focused open-source creative app built on the Comfy Developer Platform;
- a public GitHub repository with an open-source license, setup instructions,
  and Comfy API-format workflow files;
- a demo no longer than two minutes;
- a public social post tagging `#OpenSourceHiggsfield`;
- an optional but encouraged public link people can try;
- lawful media with operator-recorded permission and consent where required;
- the MiniMax H3 bonus requires MiniMax H3 as the core model.

Official Comfy context for the Developer Platform and H3 model signal is:

- SDK/API deployment documentation:
  <https://docs.comfy.org/development/api-development/sdks>;
- API deployment guide:
  <https://support.comfy.org/articles/2703236295-comfy-api-deploy-your-comfyui-workflow-as-an-api>;
- Comfy H3 open-weights announcement:
  <https://blog.comfy.org/p/comfy-is-now-the-only-official-reseller>.

No network refresh was performed inside this story. These are the researched
official signals captured for the current assessment.

### Supporting, non-authoritative signals

Wiki notes, community summaries, and prior-challenge judging language may be
used only as supporting signals for presentation quality. They cannot add or
remove current requirements, redefine categories, or turn local-only evidence
into hosted proof. No requirement or blocker in this report depends on them.

## Winning narrative

Present **one complete recasting workflow**, not a general video platform:

> Openjutsu Studio is an open-source, attestation-gated MiniMax H3 Ref2VA recasting
> studio. Give it one continuous owned or licensed dialogue shot, two authorized
> reference images, and Whisper word timings. It prepares the H3 workflow,
> preserves the original performance audio, restores that audio to the recast
> result, and emits a source/final review artifact and downloadable Comfy
> API-format graph.

This framing is intentionally narrower than “an open-source Higgsfield”:
Openjutsu does not attempt a full replacement for Higgsfield’s broad creative
platform. Its strength is depth and reproducibility in one performance-preserving
recasting path: source-audio conditioning, exact word/frame timing, rights
gating, local/open-weights execution, and a reviewable output.

## Current local inventory

| Area | Current evidence | Boundary |
|---|---|---|
| Product scope | `README.md`, `docs/PIPELINE.md`, `docs/DEMO_PLAN.md` | One-person continuous-shot recasting flow, not a general platform |
| License/setup | `LICENSE`; `docs/QUICKSTART.md`; `docs/API_EXAMPLES.md` | MIT app license does not clear model or footage rights |
| Workflow | `workflows/openjutsu_h3_lipsync_local.json` | 28-node MiniMax H3 Ref2VA graph in Comfy API format |
| Rights/consent controls | `docs/RIGHTS.md`; `examples/RIGHTS_ATTESTATION.md`; UI rights gate | User attestation, not legal provenance detection |
| App/browser evidence | `docs/evidence/frontend-upgrade/`; `docs/evidence/OJ-vwzl-upload-to-output/` | Real UI/API dry-run upload-to-output path; no model inference claim |
| Keeper slate | `docs/evidence/slate/manifest.json` and verifier receipts | 11 keepers / 48 artifacts; human selection, not a legal conclusion |
| Demo candidate | Owner-local `openjutsu_planb/demo_v1/openjutsu-demo-v1.mp4` (outside Git); `docs/evidence/OJ-mbn5-final-gate/demo-provenance.md` | SHA-256 `7cbe824a…089d`, 24,873,113 bytes, 108.052 seconds; exact full-demo clearance remains owner-owned |
| Loopback trial | `docs/evidence/OJ-2t3g-local-trial/receipt.json` | Dry-run complete on loopback; `public_url=null` |
| SDK adapter/protocol | `src/openjutsu/comfy_sdk_runner.py`; `docs/evidence/sdk-assets/` | Real local SDK protocol fixtures and fail-closed config; no hosted run |
| Deployment candidate | `deploy/comfy/comfy-build.yaml`; `deploy/comfy/asset-manifest.json`; `deploy/comfy/validation.json` | Offline candidate/dry run only; no model upload, build, GPU, or hosted execution |
| Final gate | Latest local receipt `work/anchor-oj-fnna-final-gate-bf76411/gate.json` at commit `bf764110720aa29f38329562419a9f6ac4ff9b91`; tracked snapshot `docs/evidence/OJ-2gs4-release-audit/final-gate/gate.json` at `7381af42a00936305b20b74f5ded1febf5f94805` | Both exit owner-blocked and predate current HEAD; rerun on the final public candidate |

### Selected hashes

Current-base SHA-256 values:

| Path | SHA-256 |
|---|---|
| `LICENSE` | `cb8ae2027fe6590f93812475b0808fc8aa08166a2ed82c74f2d4be2979ca4e90` |
| `docs/QUICKSTART.md` | `08cacedab7ebf20e3565f21d872ed7c47962e9b6b632548fdeef8d4afc9b1a63` |
| `workflows/openjutsu_h3_lipsync_local.json` | `06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21` |
| `deploy/comfy/comfy-build.yaml` | `89a52d508ce9e5bbf2ff52f5540d8b297f76f78982a785858c7c13029cb42342` |
| `deploy/comfy/asset-manifest.json` | `2fb34f910fca9ad3bb9229ab3883a9b04539d77a457435e0700c096a47e106a0` |
| `deploy/comfy/validation.json` | `485ef1936a6b1d3ff40d72f1876170a4ae4a9aff86dce672228c224e5868d942` |
| `src/openjutsu/comfy_sdk_runner.py` | `b8fb72e2bb820223099b3756229a0b214464803712b6dc686e32368e2f64be4d` |

Latest recorded local audited archive:

| Item | Value |
|---|---|
| Evaluated commit | `bf764110720aa29f38329562419a9f6ac4ff9b91` |
| Source tree | `c7790be516b997307d71d49a72f0649b8d7151fd` |
| Archive | `work/anchor-oj-fnna-final-gate-bf76411/public-package.zip` |
| Archive bytes | `83,408,334` |
| Archive SHA-256 | `a6d49ddd1267aad1b346518cf55442e1e61ffd98ab2759f731d4ea882e0950f8` |
| Demo SHA-256 | `7cbe824a3e7dc4ff515c23fe1672630e938e2520e9b7c3686c87fa90a4db089d` |

That archive is not the current public package. It must be rebuilt and audited
after the final narrative/demo/URL card and owner-gated SDK proof are complete.

## Owner critical path

1. **Live Comfy Developer Platform proof — owner-gated.** Configure a paid or
   otherwise authorized deployment containing the required H3 models, custom
   nodes, and `custom_nodes/openjutsu_assets` bridge. Run one bounded SDK smoke.
   Record the workflow hash, redacted job/execution IDs, output hashes, elapsed
   time, and a sanitized transcript. Do not store or print the API key.
2. **Public audited repository/demo — owner-gated.** Resolve exact-demo rights
   and third-party license review, insert the confirmed repository URL card,
   rebuild/rerun the final gate on those exact bytes, publish the audited source
   and approved demo, and retain public URL/commit/tag/media hashes.
3. **X post — owner-gated.** Post the approved asset with verified repository
   and demo links plus `#OpenSourceHiggsfield`; save and signed-out-verify the
   final post URL. Do not alter the account profile.
4. **Typeform — owner-gated.** Open the form only through the official contest
   page, submit the verified links and category selections before the deadline,
   and retain the actual confirmation/receipt ID and timestamp.

These are the only remaining submission blockers. A try link, broader platform
features, and secondary judging heuristics must not displace this path.

## Verification

Commands and results:

- `../../../.venv/bin/python -m pytest -q` — `105 passed, 1 warning`;
  the warning is the existing Starlette/httpx deprecation.
- `git diff --check` — exit `0`, no output.
- changed-evidence PCRE2 scan for absolute private paths and credential-shaped
  assignments/values — `0` matches; exit `1`, ripgrep's expected no-match status.

Sanitized command transcripts are `pytest.txt`, `diffcheck.txt`, and
`scan.txt`; `SHA256SUMS` binds the report and refreshed contest-facing docs.

## Acceptance criteria

| AC | Result | Evidence |
|---|---|---|
| 1. Distinguish official current rules from secondary signals and cite official pages | Pass | `Rule hierarchy` above |
| 2. Inventory demo/final gate/release/repo/workflow/tests/rights/SDK artifacts with useful hashes | Pass | `Current local inventory` and `Selected hashes` |
| 3. Frame one performance-preserving MiniMax H3 recasting app, not a full platform | Pass | `Winning narrative`; refreshed README/contest/demo docs |
| 4. List only the four real owner blockers | Pass | `Owner critical path` |
| 5. Local checks pass with no secrets/private paths committed | Pass | Delivery note records full pytest, `git diff --check`, scan, and hash results |
