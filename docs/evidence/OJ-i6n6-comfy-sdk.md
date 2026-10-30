# OJ-i6n6 — official Comfy SDK execution-path evidence

Date: 2026-10-17

## Decision and category impact

**Decision.** Keep the local, weight-loading MiniMax H3 graph as Openjutsu's
default/open-weights execution path, but do not present local-only `legacy` HTTP
execution as the contest's complete integration proof. Before submission, the
owner must either provide a configured Comfy API deployment and API key for a
minimum live SDK smoke, or explicitly accept the submission-risk blocker. No
credential lookup, credential use, GPU use, deployment call, or publication was
performed for this story.

**Why.** The official contest page says entries are apps built using the Comfy
Developer Platform and identifies an Open Weights Only category with “No partner
nodes or closed-source APIs, open-weights models only”
([contest source](https://comfy.org/open-source-higgsfield/)). The official SDK
documentation says the same Python SDK can target Comfy Cloud, a Comfy API
deployment selected with `COMFY_BASE_URL`, or self-hosted ComfyUI; a Comfy API
deployment uses `https://<deployment>.run.comfy.app` and requires an API key
([SDK source](https://docs.comfy.org/development/api-development/sdks)). The
official API support guide likewise says each deployment has its own endpoint and
is called with a Comfy API key using the official SDKs
([API source](https://support.comfy.org/articles/2703236295-comfy-api-deploy-your-comfyui-workflow-as-an-api)).

**Category impact.**

- Best Overall / Most Innovative / Most Viral: eligible only while the submitted
  app includes a genuine Comfy Developer Platform integration. The existing
  local app and workflow are useful evidence, but the missing live SDK smoke is
  a compliance/risk blocker for the final submission.
- Open Weights Only: the existing graph loads MiniMax H3-family weights and does
  not use partner API nodes. Comfy's H3 announcement says H3 “dropped with open
  weights” ([H3 source](https://blog.comfy.org/p/comfy-is-now-the-only-official-reseller)).
  Packaging that same weight-loading graph in a Comfy API Build remains
  open-weights-oriented; switching H3 execution to a partner/closed-source API
  node would remove this category eligibility.
- MiniMax H3 bonus: H3 remains the core model in the existing graph, so the
  local/open-weights path remains category-relevant. The missing SDK smoke is an
  execution-evidence blocker, not by itself evidence that H3 is absent.

## Fail-closed configuration contract

`ComfySdkRunner` now validates both required Developer Platform settings before
importing `comfy_sdk` or constructing its client:

- missing `COMFY_API_KEY` → `ComfySdkConfigurationError` with code
  `missing_comfy_api_key`;
- missing `COMFY_BASE_URL` → `ComfySdkConfigurationError` with code
  `missing_comfy_base_url`.

Both exceptions expose a JSON-serializable `as_dict()` envelope containing
`error.code`, `error.message`, and `error.environment_variable`. This prevents a
blank/unset deployment URL from silently falling through to Comfy Cloud and
ensures no network request can begin without owner-provided configuration.

## PM rework — 2026-10-17

The first delivery validated the resolved explicit/environment key but still
passed the original `api_key` argument to `Comfy()`. The rework corrected this to
pass `resolved_api_key`. Parameterized regression coverage now proves:

1. an explicit `api_key` is forwarded as the explicit test value;
2. when `api_key=None`, `COMFY_API_KEY` is resolved and forwarded as the
   environment test value.

The test fake records constructor arguments without making a network request or
using a real credential.

Credential-shaped scan over the rework files:

```text
rg -n --pcre2 -i '(comfyui-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|authorization[[:space:]]*[:=][[:space:]]*["]?[A-Za-z0-9._~+/=-]{20,}|bearer[[:space:]]*[:=][[:space:]]*["]?[A-Za-z0-9._~+/=-]{20,})' docs/evidence/OJ-i6n6-comfy-sdk.md src/openjutsu/comfy_sdk_runner.py tests/test_comfy_sdk_runner.py
```

Result:

```text
0 matches; exit status 1 (ripgrep's expected no-match status)
```

## Local verification

Command:

```text
../../../.venv/bin/python -m pytest tests/test_comfy_sdk_runner.py tests/test_config.py -q
```

Result:

```text
.......                                                                    [100%]
7 passed in 0.02s
```

Command:

```text
../../../.venv/bin/python -m pytest -q
```

Result:

```text
...............                                                           [100%]
15 passed in 3.62s
```

Command:

```text
../../../.venv/bin/python -m pip check
```

Result:

```text
No broken requirements found.
```

## Owner-gated live-smoke blocker

No owner-provided Comfy API deployment or key was supplied to this bounded
worker, so no live smoke, GPU/compute spend, credential read, or output hash is
claimed. To unblock, the owner (outside this story) must provide:

1. `COMFY_BASE_URL=https://<deployment>.run.comfy.app`;
2. `COMFY_API_KEY` through a secret-bearing environment, without printing it;
3. a deployment Build containing the models/custom nodes in `docs/PIPELINE.md`.

The minimum owner-run smoke must then record workflow SHA-256, SDK job/execution
identifier, each output SHA-256, elapsed time, and a redacted command transcript.

## Update — bounded smoke completed, 2026-10-25

The operator authorized a bounded live smoke. A two-node, no-model API-format
workflow was submitted once to Comfy Cloud through official `comfy-sdk` 0.5.0:

```text
queued → succeeded in 5.075s
one 64×64 PNG output
executed workflow hash re-fetched and matched
```

The full redacted job/output record and hash verification are in
[`comfy-sdk-smoke-20261025/REPORT.md`](comfy-sdk-smoke-20261025/REPORT.md).
This clears the *SDK workflow-surface execution* blocker. It does not claim a
full H3 deployment or model inference.

## Secret scan

Command:

```text
rg -n --pcre2 -i '(comfyui-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|authorization[[:space:]]*[:=][[:space:]]*["]?[A-Za-z0-9._~+/=-]{20,}|bearer[[:space:]]*[:=][[:space:]]*["]?[A-Za-z0-9._~+/=-]{20,})' docs/evidence/OJ-i6n6-comfy-sdk.md src/openjutsu/comfy_sdk_runner.py src/openjutsu/config.py tests/test_comfy_sdk_runner.py tests/test_config.py docs/CONTEST.md docs/ARCHITECTURE.md docs/QUICKSTART.md
```

Result:

```text
0 matches; exit status 1 (ripgrep's expected no-match status)
```

The scan covers every file changed by this story. No credential value is stored
in the evidence file or tests.
