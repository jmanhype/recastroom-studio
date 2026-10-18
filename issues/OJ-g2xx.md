---
id: OJ-g2xx
title: "Prepare the judge-facing Openjutsu winning package"
status: closed
priority: 0
type: task
labels: [contest, local, evidence, accepted]
parent: OJ-fglb
created_at: 2026-10-18T20:09:03Z
created_by: speed
updated_at: 2026-10-18T20:30:00Z
content_hash: "sha256:97e4490e6bc466788d7686fafdc2cd6e43d9d762287e7b8af76e34ccfda204a6"
assignee: dev-OJ-g2xx
closed_at: 2026-10-18T20:30:00Z
close_reason: "Independent PM approved commit 38bd79c4f449f42d64a171793fe8cf7572530eb2; all five ACs verified, manifest/test/scope checks passed, and only the four documented owner-gated submission blockers remain."
---

## Description
## USER INTENT
As the owner, I want a current judge-facing package assessment and refreshed winning narrative based on official Comfy signals, so the submission emphasizes one complete performance-preserving H3 recasting app rather than unrelated platform features.

## Scope
- Own docs/evidence and local package/readiness inspection only.
- Review official contest/blog/example-app signals already captured in docs and research.
- Inventory existing final gate, demo plan, release packet, workflow, and owner blockers.
- Refresh the contest-facing pitch/checklist so it leads with one polished recasting studio, exact judge expectations, and the remaining critical path.
- Run local deterministic verification appropriate to docs/package changes.

## Out of scope
No credentials, cloud/GPU spend, live SDK run, push, publication, X activity, Typeform submission, or new product features.

## Acceptance Criteria
1. A current judge-facing report distinguishes official current rules from secondary/prior-challenge judging signals and cites the official contest/blog pages.
2. The report inventories existing demo, final gate, release package, repo, workflow, tests, rights, and SDK-proof artifacts with paths/hashes where available.
3. The winning narrative explicitly frames Openjutsu as one focused performance-preserving MiniMax H3 recasting app and avoids a full-Higgsfield-platform scope.
4. The critical path lists only real remaining blockers: live Comfy Developer Platform proof, public repo/demo publication, X post, and Typeform, with owner-gated actions marked.
5. Local checks pass or any pre-existing limitation is explicitly recorded; no secrets/private paths/private media are committed.

## Testing
- Run repository full pytest.
- Verify any updated evidence hashes.
- Run git diff --check and a credential/private-path scan over changed evidence.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

PROOF:

### CI/Test Results
Commands run:
- `../../../.venv/bin/python -m pytest -q`
- `git diff --check`
- `git diff --cached --check`
- `pvg verify README.md docs/CONTEST.md docs/DEMO_PLAN.md docs/FINAL_SUBMISSION_PACKET.md docs/SUBMISSION_CHECKLIST.md docs/evidence/OJ-g2xx --format=text`
- `shasum -a 256 -c docs/evidence/OJ-g2xx/SHA256SUMS`
- changed-evidence PCRE2 private-path/credential scan recorded in `docs/evidence/OJ-g2xx/scan.txt`

Summary: full pytest PASS (`105 passed, 1 warning`; existing Starlette/httpx deprecation); whitespace PASS (both diff checks exit 0, no output); pvg verify PASS; all 10 recorded hashes OK; scan had 0 matches (ripgrep no-match exit 1 expected). Coverage is not applicable to this docs/evidence-only change.

Commit SHA: 38bd79c4f449f42d64a171793fe8cf7572530eb2
Branch: story/OJ-g2xx

### AC Verification
| AC # | Requirement | Status |
|---|---|---|
| 1 | Official current rules distinguished from secondary signals with official citations | PASS |
| 2 | Current asset inventory with useful paths/hashes | PASS |
| 3 | One performance-preserving MiniMax H3 recasting studio narrative | PASS |
| 4 | Only the four real owner blockers listed | PASS |
| 5 | Local checks pass; no secrets/private paths/private media committed | PASS |

LEARNINGS:
- Use the verifier's exact plain labels; in particular, `Commit SHA:` must contain the bare hexadecimal SHA, not markdown backticks.
- Final-gate receipts are commit-bound and must be rerun on the future public candidate.
- Stage newly created evidence before the final whitespace check so untracked-file trailing spaces are caught.

### OBSERVATIONS
- [TOOLING] The configured `pvg notes search` vault `Claude` is absent; both relevant searches failed without repository changes.
- [PROCESS] Prior audited archives recorded 31 tests while current HEAD records 105 passing tests, reinforcing that old gate output is not current-tree certification.

## nd_contract
status: delivered

### evidence
- Full pytest: `105 passed, 1 warning`; existing Starlette/httpx deprecation.
- `git diff --check` and `git diff --cached --check`: exit 0, no output.
- Private-path/credential scan: 0 matches; expected ripgrep exit 1.
- Hash receipt: all 10 entries verified OK.
- Commit SHA: 38bd79c4f449f42d64a171793fe8cf7572530eb2

### proof
- [x] AC #1: Official current signals are separated from supporting wiki/prior-challenge signals and official URLs are cited.
- [x] AC #2: Current assets, boundaries, paths, commit/tree IDs, and selected hashes are inventoried.
- [x] AC #3: The refreshed narrative frames one performance-preserving MiniMax H3 recasting studio.
- [x] AC #4: The only listed blockers are live Developer Platform proof, public repo/demo, X post, and Typeform.
- [x] AC #5: Full pytest, whitespace, verification, hash, and private-path/credential checks pass; no credentials or private media were committed.

## Implementation Evidence

PROOF:

### CI/Test Results
Commands run:
- `../../../.venv/bin/python -m pytest -q`
- `git diff --check`
- `git diff --cached --check`
- `pvg verify README.md docs/CONTEST.md docs/DEMO_PLAN.md docs/FINAL_SUBMISSION_PACKET.md docs/SUBMISSION_CHECKLIST.md docs/evidence/OJ-g2xx --format=text`
- `shasum -a 256 -c docs/evidence/OJ-g2xx/SHA256SUMS`
- changed-evidence PCRE2 private-path/credential scan recorded in `docs/evidence/OJ-g2xx/scan.txt`

Summary: full pytest PASS (`105 passed, 1 warning`; existing Starlette/httpx deprecation); whitespace PASS (both diff checks exit 0, no output); pvg verify PASS; all 10 recorded hashes OK; scan had 0 matches (ripgrep no-match exit 1 expected). Coverage is not applicable to this docs/evidence-only change.

Commit SHA: `38bd79c4f449f42d64a171793fe8cf7572530eb2` on `story/OJ-g2xx`.

### AC Verification
| AC # | Requirement | Status |
|---|---|---|
| 1 | Official current rules distinguished from secondary signals with official citations | PASS |
| 2 | Current asset inventory with useful paths/hashes | PASS |
| 3 | One performance-preserving MiniMax H3 recasting studio narrative | PASS |
| 4 | Only the four real owner blockers listed | PASS |
| 5 | Local checks pass; no secrets/private paths/private media committed | PASS |

LEARNINGS:
- Use the verifier's exact plain `## Implementation Evidence`, `Commands run:`, `Summary:`, and `Commit SHA:` labels; decorated variants can carry the same facts but fail structural preflight.
- Final-gate receipts are commit-bound and must be rerun on the future public candidate.
- Stage newly created evidence before the final whitespace check so untracked-file trailing spaces are caught.

### OBSERVATIONS
- [TOOLING] The configured `pvg notes search` vault `Claude` is absent; both relevant searches failed without repository changes.
- [PROCESS] Prior audited archives recorded 31 tests while current HEAD records 105 passing tests, reinforcing that old gate output is not current-tree certification.

## nd_contract
status: delivered

### evidence
- Full pytest: `105 passed, 1 warning`; existing Starlette/httpx deprecation.
- `git diff --check` and `git diff --cached --check`: exit 0, no output.
- Private-path/credential scan: 0 matches; expected ripgrep exit 1.
- Hash receipt: all 10 entries verified OK.
- Commit: `38bd79c4f449f42d64a171793fe8cf7572530eb2` on `story/OJ-g2xx`.

### proof
- [x] AC #1: Official current signals are separated from supporting wiki/prior-challenge signals and official URLs are cited.
- [x] AC #2: Current assets, boundaries, paths, commit/tree IDs, and selected hashes are inventoried.
- [x] AC #3: The refreshed narrative frames one performance-preserving MiniMax H3 recasting studio.
- [x] AC #4: The only listed blockers are live Developer Platform proof, public repo/demo, X post, and Typeform.
- [x] AC #5: Full pytest, whitespace, verification, hash, and private-path/credential checks pass; no credentials or private media were committed.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-10-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `../../../.venv/bin/python -m pytest -q`
  - `git diff --check`
  - `git diff --cached --check`
  - `pvg verify README.md docs/CONTEST.md docs/DEMO_PLAN.md docs/FINAL_SUBMISSION_PACKET.md docs/SUBMISSION_CHECKLIST.md docs/evidence/OJ-g2xx --format=text`
  - `shasum -a 256 -c docs/evidence/OJ-g2xx/SHA256SUMS`
  - changed-evidence PCRE2 private-path/credential scan recorded in `docs/evidence/OJ-g2xx/scan.txt`
- Summary: full pytest PASS (`105 passed, 1 warning`; existing Starlette/httpx deprecation); whitespace PASS (both diff checks exit 0, no output); pvg verify PASS; all 10 recorded hashes OK; scan had 0 matches (ripgrep no-match exit 1 expected).
- Coverage: not applicable — docs/evidence-only change, with no production or test code changed.
- Key output: sanitized transcripts are committed as `docs/evidence/OJ-g2xx/pytest.txt`, `diffcheck.txt`, and `scan.txt`.

### Commit
- Branch: `story/OJ-g2xx`
- SHA: `38bd79c4f449f42d64a171793fe8cf7572530eb2`
- Base: `0e8e3fb8808e9518c2ece8224c900378747924cc`

### pvg verify
- `VERIFY: PASSED (0 files scanned, 0 issues)` for the changed docs/evidence set.
- `VERIFY: PASSED (0 files scanned, 0 issues)` for `docs/evidence/OJ-g2xx/run_checks.sh`.

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | Official current rules distinguished from secondary/prior-challenge signals with official citations | `docs/evidence/OJ-g2xx/REPORT.md` rule hierarchy; `docs/CONTEST.md` | `docs/evidence/OJ-g2xx/REPORT.md` AC table | PASS |
| 2 | Current demo/final-gate/release/repo/workflow/tests/rights/SDK inventory with useful paths/hashes | `docs/evidence/OJ-g2xx/REPORT.md` inventory/hash sections | `docs/evidence/OJ-g2xx/SHA256SUMS` | PASS |
| 3 | Narrative frames one performance-preserving MiniMax H3 recasting studio, not a full Higgsfield platform | `README.md`; `docs/CONTEST.md`; `docs/DEMO_PLAN.md`; `docs/SUBMISSION_CHECKLIST.md` | `docs/evidence/OJ-g2xx/REPORT.md` AC table | PASS |
| 4 | Critical path lists only live Developer Platform proof, public repo/demo, X post, and Typeform | `docs/evidence/OJ-g2xx/REPORT.md`; `docs/SUBMISSION_CHECKLIST.md` | `docs/evidence/OJ-g2xx/REPORT.md` AC table | PASS |
| 5 | Local checks pass; no secrets/private paths/private media committed | OJ-g2xx evidence only | `pytest.txt`; `diffcheck.txt`; `scan.txt`; `SHA256SUMS` | PASS |

LEARNINGS:
- Final-gate receipts are commit-bound: the newest archive receipt is useful design/quality evidence but predates current HEAD and cannot certify this tree.
- Current contest decisions should cite only the official contest/blog/Developer Platform signals; wiki or prior-challenge rubrics remain supporting presentation signals.
- Run `git diff --check` again after staging newly created evidence; the unstaged scan missed trailing spaces in the then-untracked report, and the staged check caught them before commit.

### OBSERVATIONS (unrelated)
- [TOOLING] `pvg notes search "Openjutsu contest final gate"` and the second configured search failed because the configured vault `Claude` is absent; available vaults include `nd-vault`, `Obsidian Vault`, and `.vault`. No repository files were changed by that failed lookup.
- [PROCESS] The prior audited archives recorded 31 tests while current HEAD has 105 passing tests; this reinforces the need to rerun the final gate on the exact future public candidate.

## nd_contract
status: delivered

### evidence
- Full pytest: `105 passed, 1 warning`; warning is the existing Starlette/httpx deprecation.
- `git diff --check` and `git diff --cached --check`: exit 0, no output.
- Private-path/credential scan over changed docs/evidence: 0 matches; expected ripgrep exit 1.
- Hash receipt: all 10 entries in `docs/evidence/OJ-g2xx/SHA256SUMS` verified OK.
- Commit: `38bd79c4f449f42d64a171793fe8cf7572530eb2` on `story/OJ-g2xx`.

### proof
- [x] AC #1: Official current signals are separated from supporting wiki/prior-challenge signals and official contest/blog/docs URLs are cited.
- [x] AC #2: Current assets, boundaries, paths, commit/tree IDs, and selected SHA-256 values are inventoried.
- [x] AC #3: README, contest, demo, checklist, and report consistently frame one performance-preserving MiniMax H3 recasting studio.
- [x] AC #4: The only listed submission blockers are live Developer Platform proof, public audited repo/demo, X post, and Typeform.
- [x] AC #5: Full pytest, whitespace, verification, hash, and private-path/credential checks pass; no credentials or private media were committed.

## History
- 2026-10-18T20:09:20Z status: open -> in_progress
- 2026-10-18T20:09:20Z claimed by dev-OJ-g2xx
- 2026-10-18T20:22:09Z status: in_progress -> in_progress
- 2026-10-18T20:22:43Z status: in_progress -> in_progress
- 2026-10-18T20:30:00Z status: in_progress -> closed

## Links
- Parent: [[OJ-fglb]]

## Comments
