# OJ-2gs4 release-audit regression evidence

The unsafe local-trial scanner fixture is now constructed at runtime. The
committed test still exercises both negative finding kinds without retaining
their complete forbidden byte patterns in source.

The audited implementation commit is
`7381af42a00936305b20b74f5ded1febf5f94805`. Its filtered public package has a
zero-error release audit, a reproducible archive hash recorded in
`final-gate/gate.json`, and no local gate failure. The final gate exits `2`
only because eight publication, provenance, live-smoke, and clean-install
checks remain owner-gated.

- `validation.json` records command outcomes, exact package hashes, loopback
  status, and matrix counts.
- `final-gate/gate.json` is the unmodified machine-readable gate report.
- `local-trial/receipt.json` and `local-trial/secret-scan.json` record the
  isolated dry-run loopback trial.

No publication, submission, network generation, or credential use occurred.
