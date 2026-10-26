# DISCOVERED_BUG: predecessor release-audit regression

The selected commit in `gate.json` fails the existing public release audit.
Exact findings:

- `absolute user path: tests/test_local_trial.py`
- `possible credential value: tests/test_local_trial.py`

These are synthetic negative-test fixture literals introduced by OJ-2t3g,
not evidence that a real credential was exposed. Nevertheless the public
package audit correctly rejects the current candidate under its existing
policy. No exception, scanner waiver or predecessor repair is included here.
The dispatcher requested a separate finding/repair (one finding per PR).
Reproduce with the final gate or audit an unpacked final-gate archive.
After a separate accepted repair, rebuild and rerun the complete gate on that
new commit. The current archive must not be published or submitted.
