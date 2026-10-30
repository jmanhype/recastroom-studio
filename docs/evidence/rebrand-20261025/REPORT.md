# RecastRoom public rebrand — 2026-10-25

## Decision

The contest-facing project name is now **RecastRoom Studio**. This avoids the
earlier independent public `SydFloyd/openjutsu` repository and names the actual
production lane: the Recast Room.

The complete decision, collision check, compatibility boundary, and publication
rule are recorded in [`docs/BRANDING.md`](../../BRANDING.md).

## Collision evidence

GitHub repository search at the time of the decision returned:

```text
"RecastRoom":                0
"RecastRoom Studio":         0
"Performance Recast Studio": 0
"H3 Recast Studio":          0
```

The shorter generic phrase “Recast Studio” has unrelated repositories, so public
materials must use the complete name.

## Public surface changed

- README headline and active setup language;
- package name: `recastroom-studio`;
- CLI command: `recastroom`;
- FastAPI title;
- web title, masthead, workflow copy, and footer;
- primary public environment prefix: `RECASTROOM_*`;
- deterministic release archive prefix;
- active quickstart, release, rights, pipeline, demo, deployment, API, and
  final-submission documents;
- README UI screenshots;
- prepared-job screenshot;
- demo closing title card and storyboard contact sheet.

New primary screenshot hashes:

```text
app-landing.png / app-landing-v2.png:
a467420def1f4894985475d0ee5dcac17e759ad4013067ea53fcfaeb523e95ca

app-prepared-job.png:
c665b788f9d37eb7baed037be641ce3e769c073bb4ea00f703ad1e880ced5efd

app-walkthrough.jpg:
78d191414646d74be66648034e1f955148166557f2e677d82c9abdf10ea218c4

demo-v1-contact.jpg:
f42066ec15a9e3218dacf20070c5224d984bdc9a8d3e789785bc6378460e36bb
```

## Compatibility boundary

These identifiers intentionally remain unchanged in this release:

```text
src/openjutsu/
workflows/openjutsu_h3_lipsync_local.json
custom_nodes/openjutsu_assets/
OPENJUTSU_* legacy environment aliases
```

They are internal compatibility identifiers, not public brand claims. The new
`RECASTROOM_*` value takes precedence when both names are present.

## Demo rebrand

Source candidate:

```text
openjutsu-demo-v1.mp4
SHA-256 7cbe824a3e7dc4ff515c23fe1672630e938e2520e9b7c3686c87fa90a4db089d
```

Current candidate:

```text
recastroom-demo-v1.mp4
SHA-256 a14b3eb287e3daf0ed4dd27e238048c1725c087c0b48cf8ffb301758e637f13f
duration 108.052 seconds
```

The first 96 seconds are a visual re-encode of the previously assessed source.
The final twelve seconds were replaced with a RecastRoom Studio title card.
The audio stream was copied, and decoded stereo PCM is byte-identical:

```text
06f5984c4e2d771437a6fd028efb9e4861f9f70b55e7905898baf8faa7b7fe15
```

First-96-second PSNR against the source:

```text
average: 39.836496 dB
minimum: 10.018285 dB
maximum: 62.122670 dB
```

The low minimum is expected at the added outbound/inbound fade boundary; this is
a visual replacement record, not a claim that the demo was re-rendered by a model.

## Verification

Performed after the rename:

```text
editable install:       passed
recastroom --version:   0.1.1
pip check:              passed
compileall:             passed
pytest:                 113 passed, 1 warning
```

A separate credential-free API E2E run using the new environment prefix
completed:

```text
dry-run state:          complete
SDK state:              error, missing COMFY_API_KEY
secret removal:         COMFY, legacy, and RECASTROOM API variables removed
```

The SDK error is the expected fail-closed result before any network access.

## Owner boundary unchanged

This rebrand does not clear:

```text
exact demo rights/consent,
third-party model/node licenses,
live Comfy Developer Platform SDK execution,
clean-environment install,
public repository/release,
public demo URL card,
X post,
Typeform submission.
```

Those remain explicit owner blockers in the final submission gate.
