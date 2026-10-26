# OJ-v983 quality-gate evidence

This directory records the measured validation for commit
`80821d7e73bb0116e7ab70daab7718d309939d55`.

The refactor keeps `openjutsu.evidence.verify_manifest` as the stable public
entry point and moves receipt, keeper, artifact, and file-set validation stages
into `openjutsu.manifest_verifier`. No schema, threshold, keeper hash, or
acceptance semantic was changed.

The fresh final-gate output was written under ignored `work/` storage and is
summarized in `validation.json`; the 83 MB public-package zip is deliberately
not committed. The gate exited 2 only for the eight recorded owner blockers,
with 11 PASS, 0 FAIL, and no release-audit errors.
