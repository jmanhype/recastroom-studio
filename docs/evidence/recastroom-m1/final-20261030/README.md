# OJ-vqyg final developer proof — 2026-10-30 UTC

**Tested source:** `1ad5c82aaa027a1c1034ff7c7cec183d0d2cab6f`.
This bundle is developer delivery evidence, not independent acceptance, a live
provider qualification, publication, or a claim that a later docs-only commit ran
these four profiles. The final candidate is bound separately by app/src/tests/tools
tree-byte parity in the external delivery receipt and native story comment.

## Actual matrix

| Source location | Environment | Result | Elapsed |
|---|---|---|---|
| Managed story worktree | inherited, credential variables removed | 393 passed, 1 warning; exit 0 | 180.91s |
| Managed story worktree | strict explicit env -i | 393 passed, 1 warning; exit 0 | 178.21s |
| Ordinary git source archive | inherited, credential variables removed | 393 passed, 1 warning; exit 0 | 176.83s |
| Ordinary git source archive | strict explicit env -i | 393 passed, 1 warning; exit 0 | 179.58s |

All four execute `APP/.venv/bin/python -m pytest -q`, all 393 collected tests,
zero skipped and zero failures. Strict commands prepend `/usr/bin/env -i` and
explicit PATH/HOME/TMPDIR/PYTHONPATH/GIT_ALLOW_PROTOCOL/OJ_VQYG_EVIDENCE entries;
the exact argument vectors and environment aliases are in `matrix-results.json`.
`provenance.json` binds the raw external matrix hash and test-source digest;
public text substitutes local directory aliases, without altering raw external logs.
Coverage percentage was not measured; no coverage score is fabricated.

## Real journey and artifact map

The canonical browser receipts here are from **managed-strict at the tested SHA**.
The other three full-profile browser bundles remain in the external matrix directory.

| AC | Real observations / receipts |
|---|---|
| 1 | `phase1.json`: native project/reference/source upload and confirmed exact [0,8), [8,16), [16,24) pass-through partition. `phase2.json`: checked attestation and two separately authorized CPU attempts, worker OFF. `phase3.json`: same IDs completed after restart with worker ON and real receipts. `phase4.json`: native file+receipt replay uploads, synchronized comparison, human keeper reviews, same-shot select/reselect/deselect/select, trim/reorder/audio policy and actual download. |
| 2 | `safety.json`: delayed delivery of the real fetched old-project GET response after switching projects; new project remains authoritative. Native reset/reload/refresh preserve durable scene/takes and create no attempt POST. Same-shot challenger completes, duplicate returns same ID, every old take ID/hash remains unchanged (`phase3.json`). Separate queued attempt is cancelled through native controls. Explicit offline fenced DB unknown fixture appears visibly paused; no provider lookup/recovery/refund claim. |
| 3 | `journey-receipt.json`: source/CPU clip/selected/final hashes, protected binding and operation fingerprint, canonical Whisper-compatible LF digest, effective schedule digest, nonempty shot-b word [9/24,10/24) shifted to [1/24,2/24), formatter frames 2–3 / 0.042–0.083s. Actual exported 16 frames/PTS zero, pixel correspondence, source/render/pad/decode/placement and edit-map audio checks. `phase4.json` and `08-refusal-detail.png` show missing-take refusal with no edit/export/download, separately from the successful export. |
| 4 | Four actual full profiles above; five owned server processes stopped, listeners closed (`journey-receipt.json`), captured browser request method/full URL/origin before independent allowed-origin checks, and redacted DB event/receipt ledger. Independent PM/Anchor and actual primary-main post-merge gate are still downstream, not self-certified here. |

`02-cpu-dry-runs.png` shows **prepared** records before restart; completion is
proved in phase3. `03-challenger-truthful-cancel.png` is the retained filename for
the **completed challenger** screenshot; separate actual queued cancellation is
`06-queued-cancel.png`. Cancellation wording in the app uses its stored terminal
enum; this fixture proves local queued prevention only, not remote cancellation.
`09-paused-detail.png` is the readable offline unknown-state presentation.
`actual-download.mp4` is Chrome's actual downloaded artifact, not a copied server file.

## Gates, history and limits

- E2E source: one file, 635 total lines (authorized budget: at most 800 over at most two).
- Substance, E2E presence, no-mock scan, diff check and scoped TDD guard all PASS.
  The scoped guard is `48f466a..1ad5c82`, **not whole-epic TDD**.
- `pvg gates`: PASS, zero skipped; disclosed CCN 29>15 and 597 nonblank lines>400 warnings.
- Every full profile reports the known Starlette TestClient/httpx deprecation warning.
  No dependency install or unrelated warning fix was performed.
- `whole-epic-tdd-preflight.log` is the parent's separate historical preflight:
  FAIL, 22 unmarked historical test-edit commits. Applicability remains for independent
  Anchor review. This delivery neither waives that result nor rewrites history/settings.
- Current focused convergence: attempt1 PASS; attempt2 FAIL from a harness teardown
  `FoundationServer.port` attribute error; corrected attempt3 PASS. Logs retained.
  Helpers were then extracted to satisfy the blocking complexity threshold before the
  committed four-profile matrix. No assertions were removed by that extraction.
- `historical-initial-attempts.json` hashes all 19 initial logs: 17 failures/errors,
  2 passes; old 348-test proof is a baseline, not final evidence.
- CPU table: `openjutsu-cpu-routing-windows-v1-20261027`; **h3_qualified=false**.
  Live H3/provider lookup/cancellation qualification, deployment and publication are
  **OWNER_BLOCKED**. Unknown presentation is intentionally an offline fixture.

Verify this bundle with `shasum -a 256 -c SHA256SUMS` from this directory.
