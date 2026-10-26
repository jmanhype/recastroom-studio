#!/bin/sh
set -u

evidence=docs/evidence/OJ-g2xx
shared_root=$(CDPATH= cd ../../.. && pwd)
users_path=/Users
private_var_path=/private/var
tmp_path=/tmp

{
  printf '%s\n' '$ ../../../.venv/bin/python -m pytest -q'
  ../../../.venv/bin/python -m pytest -q
  printf 'exit=%s\n' "$?"
} > "$evidence/pytest.txt" 2>&1
sed -i '' "s|$shared_root|<shared-checkout>|g" "$evidence/pytest.txt"

{
  printf '%s\n' '$ git diff --check'
  git diff --check
  status=$?
  printf 'exit=%s\n' "$status"
} > "$evidence/diffcheck.txt" 2>&1

pattern="(${users_path}/|${private_var_path}/|${tmp_path}/|comfyui-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|(api[_-]?key|token|secret|password)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._~+/=-]{20,})"
{
  printf '%s\n' '$ rg -n --pcre2 -i <private-path-and-credential-pattern> <changed docs/evidence files>'
  rg -n --pcre2 -i "$pattern" \
    README.md \
    docs/CONTEST.md \
    docs/DEMO_PLAN.md \
    docs/SUBMISSION_CHECKLIST.md \
    docs/FINAL_SUBMISSION_PACKET.md \
    "$evidence"
  status=$?
  if [ "$status" -eq 1 ]; then
    printf '%s\n' '0 matches; exit status 1 is ripgrep expected no-match status'
  else
    printf '%s\n' "unexpected ripgrep exit=$status"
  fi
} > "$evidence/scan.txt" 2>&1

shasum -a 256 \
  README.md \
  docs/CONTEST.md \
  docs/DEMO_PLAN.md \
  docs/SUBMISSION_CHECKLIST.md \
  docs/FINAL_SUBMISSION_PACKET.md \
  "$evidence/REPORT.md" \
  "$evidence/pytest.txt" \
  "$evidence/diffcheck.txt" \
  "$evidence/scan.txt" \
  "$evidence/run_checks.sh" \
  > "$evidence/SHA256SUMS"

shasum -a 256 -c "$evidence/SHA256SUMS"
