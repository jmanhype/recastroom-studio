---
id: OJ-oc1m
title: "Prove live Comfy Developer Platform execution"
status: open
priority: 0
type: task
labels: [contest, external-integration, owner-gated]
parent: OJ-fglb
created_at: 2026-10-18T20:09:04Z
created_by: speed
updated_at: 2026-10-22T03:13:52Z
content_hash: "sha256:006ac68a1ad45bd3114c21eae386d6e15bb71977ea2c608048ea79eb00786b63"
blocks: [OJ-oain]
follows: [OJ-g2xx]
---

## Description
## USER INTENT
As the owner, I want one bounded real Comfy Developer Platform execution receipt, so judges can distinguish Openjutsu's actual SDK/API integration from local-only dry-run evidence.

## Authorization
The operator answered Yes to the proposed live Comfy proof. Use the smallest viable real job, prefer an existing configured deployment, and stop on credential, balance, deployment, or workflow errors. Never print or commit secret values.

## Scope
- Verify credential/deployment presence without exposing values.
- Reuse or create the minimum Comfy Developer Platform deployment required by the prepared build candidate.
- Upload only the synthetic rights-clean smoke fixtures needed for the smallest execution.
- Run Openjutsu through its official Comfy SDK adapter, not a bypass script.
- Download and hash real outputs; keep credentials and unnecessary raw provider diagnostics outside Git.
- Record sanitized setup, IDs, timings, credits/spend if exposed, output hashes, and teardown.

## Out of scope
No public repo push, X activity, Typeform submission, unrelated model experiments, benchmark suite, or repository history rewrite.

## Acceptance Criteria
1. Credential/deployment readiness is checked without secret disclosure; missing configuration fails closed.
2. A real Comfy Developer Platform job is created through Openjutsu's SDK adapter using the prepared workflow/deployment surface.
3. The job reaches a verified terminal state and at least one real output is downloaded and hash-verified.
4. Evidence records sanitized commands, environment variable names only, deployment identity, job/execution identifiers, timing, spend/credit signal if available, workflow hash, fixture hashes, and output hashes.
5. Any deployment/build changes remain bounded to the prepared Openjutsu asset bridge/workflow and are validated; no secret enters Git.
6. The live path is distinguishable from dry-run and local legacy paths in the receipt.
7. Teardown removes temporary QA processes/tabs where applicable and documents any intentionally retained deployment.

## Testing
- Run focused SDK/config/deployment tests before external spend.
- Run the external smoke once unless a transient provider failure requires one documented retry.
- Run full pytest after any code/config/evidence changes.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-10-18T20:49:05Z dep_added: blocks OJ-oain
- 2026-10-18T20:49:12Z status: open -> in_progress
- 2026-10-18T20:49:12Z auto-follows: linked to predecessor OJ-g2xx
- 2026-10-18T20:49:12Z claimed by dev-OJ-oc1m
- 2026-10-22T03:13:52Z status: in_progress -> open
- 2026-10-22T03:13:52Z released by speed

## Links
- Parent: [[OJ-fglb]]
- Blocks: [[OJ-oain]]
- Follows: [[OJ-g2xx]]

## Comments

### 2026-10-18T23:48:20Z speed
Live-proof checkpoint: blocked before external spend. Browser evidence shows Personal Workspace credits remaining 0, spend 0, and no deployments. API key `openjutsu-live-proof` exists only as a masked platform value; the external 0600 credential file fails official `comfy_sdk.models.list` with Unauthorized, so the captured value is incomplete/unusable. Billing is a free plan with Stripe options ($10/$25/$50/$100; $25 selected by default); no purchase was made. The offline deployment candidate also retains the documented BFS ref, dependency/runtime, 46.6GB asset, and asset-bridge blockers. Evidence: `docs/evidence/OJ-oc1m/README.md`, `auth-check.txt`, cropped dashboard/API-key/billing screenshots, `pytest.txt`, and `SHA256SUMS` on story branch `story/OJ-oc1m`. Full local tests: 105 passed, 1 warning. Required owner actions: action-time confirmation for a replacement API key and exact credit amount, plus a choice between strict deployment proof or formally rescoping to a bounded official Router proof.

### 2026-10-18T23:48:38Z speed
Evidence checkpoint committed locally on story/OJ-oc1m at c480e60. No merge, push, or external spend performed.

### 2026-10-18T23:52:34Z speed
Owner constraint update: no funds are currently available for Comfy credits or API spend. The Colab path was used because it was the available compute source. Do not continue to Stripe or any paid Comfy transaction. Investigate no-cost contest credits and local/SDK-proxy proof paths first.

### 2026-10-18T23:59:23Z speed
No-cost path checkpoint: owner confirmed no funds. A real local official-SDK execution succeeded on the 3090 through comfy-api-proxy 0.1.6 and comfy-sdk 0.5.0: job aada51c8-ddd6-437e-a664-f6a17829d576, 24-frame 320x180 H.264 MP4, output SHA-256 c444aa186a05f623c0815f7dd4f099f3425e37955666953c756712921b4bb87d, provider credits used 0. Temporary ComfyUI/proxy processes were stopped. Boundary: core-node local SDK smoke, not the prepared H3 workflow or Openjutsu asset bridge, so strict OJ-oc1m AC remains unmet. Evidence committed at 8822da8 on story/OJ-oc1m. Official signup form remains a possible free-credit route; no personal data submitted yet.

### 2026-10-19T00:19:35Z speed
Official free-credit signup was submitted with owner authorization. Typeform returned You're in, with credits on the way if the submission made the first 200. After a wait and refresh, Comfy still showed 0 credits, 0 spend, and no deployments, so no replacement API key was created and no payment occurred. Sanitized signup and post-signup evidence committed at 81bc6cc on story/OJ-oc1m; full tests remain 105 passed, 1 warning.

### 2026-10-22T03:13:52Z speed
Owner-directed queue checkpoint 2026-10-22: released the stale dev-OJ-oc1m claim only because pvg loop next reported the story stalled. This is NOT acceptance or completion. Existing branch/worktree/evidence remain untouched. Strict live Developer Platform AC remains unmet: the prior local official-SDK smoke was core-node only, while credits/API key/deployment/asset-bridge decisions remain owner-gated and no external spend is authorized. A local offline C1 preset story now precedes this story so queue work can continue without GPU/provider spend.
