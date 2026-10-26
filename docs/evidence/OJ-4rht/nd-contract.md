## Implementation Evidence
Summary: Cinematic static studio implemented, real browser smoke passed; independent acceptance pending.
Commit SHA: 90ec73d

### CI/Test Results
Commands run:
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q
- git diff --check
- node --check app/web/studio.js

## nd_contract
status: delivered

### evidence
- Implementation b5fd8e4; browser fix/evidence 90ec73d on story/OJ-4rht.
- env -u OPENJUTSU_DATA_DIR PYTHONPATH=src root/.venv/bin/python -m pytest -q: 31 passed, 1 existing warning in 11.08s. docs/evidence/OJ-4rht/pytest.txt.
- git diff --check and node --check app/web/studio.js: exit 0.
- CUA browser real synthetic dry-run job 3af79afdac1c completed with source, final, paired videos and artifact links; paired download SHA256 eaecc945dc74d1c4008bf4403c20ad4c2ffb133f4421ef45715b648bb60aefd9 matches server artifact.
- docs/evidence/OJ-4rht/desktop-review.jpg SHA256 e1129e68d907e0b8bd7f039334c4f55e1cae0d146f3fb73c1deeb43a1415c9db.
- docs/evidence/OJ-4rht/mobile-review.jpg SHA256 5839db2d82d46cb44dd5eb5bfa395a48ffcd17023a3691a7fa01b2ad829db082.
- Widths 375/414/768/1024/1440 had no horizontal overflow. Keyboard Space consent; two-reference job c00bba38d22c; reset during run remained cleared after server completion. Malformed timing input displayed actionable prepare error and disabled Run.
- Full procedure and limitations: docs/evidence/OJ-4rht/DELIVERY.md.

### proof
- [x] AC #1: Responsive source/two-reference previews, labels/focus/keyboard Space, reduced-motion stylesheet.
- [x] AC #2: Explicit unchecked rights gate, guided select/prepare/run/review with disabled explanations.
- [x] AC #3: Server states only, unknown health not free/local, dry_run explicitly no AI inference.
- [x] AC #4: Complete job shows final/paired review and real artifact links; paired download byte-hash verified.
- [x] AC #5: Inline errors and retry/reset; epoch/job snapshots, abort, URL revocation and text-safe API rendering. Browser reset race exercised; broader permutations reserved for dependent regression story.
- [x] AC #6: Backend unchanged, 31 baseline tests pass, real browser smoke and screenshot hashes saved.

### LEARNINGS
- Form control id reset shadows form.reset; use the prototype method. Browser smoke exposed and verified this repair.

### OBSERVATIONS
- No live inference/GPU/paid calls. No formal screen-reader or exhaustive race-suite claim. User judges aesthetics; independent PM acceptance remains required. Preview loopback 8892 remains running for review.
