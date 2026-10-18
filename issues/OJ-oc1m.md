---
id: OJ-oc1m
title: "Prove live Comfy Developer Platform execution"
status: in_progress
priority: 0
type: task
labels: [contest, external-integration, owner-gated]
parent: OJ-fglb
created_at: 2026-10-18T20:09:04Z
created_by: speed
updated_at: 2026-10-18T23:48:20Z
content_hash: "sha256:513e5cc029c1ecc5e3fbd5453cc476b96a1899144918c60dc16aa8b7df7c7d99"
blocks: [OJ-oain]
assignee: dev-OJ-oc1m
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

## Links
- Parent: [[OJ-fglb]]
- Blocks: [[OJ-oain]]
- Follows: [[OJ-g2xx]]

## Comments

### 2026-10-18T23:48:20Z speed
Live-proof checkpoint: blocked before external spend. Browser evidence shows Personal Workspace credits remaining 0, spend 0, and no deployments. API key `openjutsu-live-proof` exists only as a masked platform value; the external 0600 credential file fails official `comfy_sdk.models.list` with Unauthorized, so the captured value is incomplete/unusable. Billing is a free plan with Stripe options ($10/$25/$50/$100; $25 selected by default); no purchase was made. The offline deployment candidate also retains the documented BFS ref, dependency/runtime, 46.6GB asset, and asset-bridge blockers. Evidence: `docs/evidence/OJ-oc1m/README.md`, `auth-check.txt`, cropped dashboard/API-key/billing screenshots, `pytest.txt`, and `SHA256SUMS` on story branch `story/OJ-oc1m`. Full local tests: 105 passed, 1 warning. Required owner actions: action-time confirmation for a replacement API key and exact credit amount, plus a choice between strict deployment proof or formally rescoping to a bounded official Router proof.
