# OJ-p8rd: atomic status publication

Base: `2b22504`. Scope: `app/main.py`, `tests/test_status_atomic.py`, and this
evidence directory only. No tracker transitions, commits, browser operations,
provider calls, or UI/media/workflow changes performed by this worker.

## Implementation

- A dedicated status lock serializes in-process read/merge/publish operations,
  independent of the long-running execution locks. Updates build a new mapping;
  the existing in-memory mapping is not mutated in place.
- Serialize before touching the destination. Write a uniquely created temporary
  file in the destination directory; close it before `os.replace` publishes it.
  Readers retain the unchanged status endpoint and see the old or new complete
  JSON file, not a truncation window. There are no JSON-error retries.
- Publish the in-memory snapshot only after successful replacement. The finally
  block removes an unpublished temporary file on normal exception paths.

## Measured verification

Run from the story worktree using the root project's virtualenv Python:

```sh
PYTHONPATH=src python docs/evidence/status-atomic/OJ-p8rd/verify.py
```

- `legacy-control.txt`: loads the actual `_set_status` AST from base commit
  `2b22504` into a separate test process, without editing any production file.
  The fixed implementation's publication-boundary test **fails as expected**:
  HTTP 500 instead of HTTP 200. This proves the regression rejects the original
  truncating implementation, rather than merely asserting a test-specific copy.
- `focused-1.txt` through `focused-3.txt`: **7 passed** on each run.
- `full-suite.txt`: **48 passed**.
- Stress case: three writers each publish 60 updates while three readers each
  make 60 actual FastAPI status requests. Iteration barriers bound and coordinate
  overlap; all 180 requests return HTTP 200 with coherent paired fields.
  Final disk/memory snapshots agree, all writer-specific fields survive, and
  all 181 recorded temporary publication paths are distinct and same-directory.
- Deterministic event barriers hold the legacy writer after truncation or the
  repaired writer immediately before replacement. The repaired endpoint returns
  the complete previous snapshot while paused and the new snapshot afterward.
- Serialization, partial temporary write, and replacement failure injections
  preserve existing disk/memory snapshots and leave no temporary files.
- Schema, invalid IDs, missing jobs, and missing status artifacts are tested;
  missing/invalid resources retain HTTP 404.
- Existing httpx/Starlette deprecation warning remains. The legacy control also
  reports an expected pytest import-rewrite warning from its in-process import.

## Guarantees and limits

Atomic reader visibility relies on same-filesystem `os.replace` semantics. The
status lock protects this process's updates only; this is not a multiprocess
shared-memory coordinator or queue admission redesign. Independent processes
still publish whole JSON files but could overwrite one another's logical state.
The lock serializes short status writes across jobs. No fsync/power-loss durability
guarantee is added. Abrupt process termination can leave a temporary file, though
the previously published status remains untouched before replacement. External
deletion/corruption and cleanup permission failures are not hidden or retried.

Browser retry validation and PM acceptance remain with the parent coordinator.
`SHA256SUMS` covers code, regression tests, runner, report, and captured outputs.
Captured outputs sanitize private absolute paths.
