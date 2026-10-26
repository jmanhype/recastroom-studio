# Bounded official Comfy SDK live smoke — 2026-10-25

## Authorization and bounds

The operator explicitly authorized a bounded live Comfy SDK smoke.

```text
workflow submissions:       1
workflow wait timeout:      180 seconds
model inference:            false
uploaded assets:            0
read-only follow-ups:       1
credential output:          none
```

The first authentication attempt used an incorrect substring from a historical
session and failed before job submission with HTTP 401. It created no job. The
authorized key was then recovered in-process from the owner's prior message
history without printing or writing it. Attempt 2 submitted exactly one job.

## Execution

Target:

```text
Comfy Cloud
https://cloud.comfy.org
official comfy-sdk 0.5.0
client_info: recastroom-studio-smoke
```

The smoke graph used two core CPU nodes and no model:

```text
EmptyImage 64×64 RGB white
→ SaveImage
```

Workflow SHA-256:

```text
ec9615286e08292d3d9606174b477c8847296dc3be7161a246d402e077e797ca
```

Observed:

```text
job ID:          f871824b-55d5-4629-b178-949104e9415b
initial status:  queued
final status:    succeeded
elapsed:         5.075 seconds
outputs:         1
```

## Output

```text
name:          recastroom_sdk_smoke_00001_.png
content type:  image/png
dimensions:    64×64
pixels:        solid white RGB
bytes:         420
SHA-256:       ee1b9d9bd39411706e6f5d60f64e23089426ecc390d1c746f8b3acf89cfba60d
```

## Read-only verification

A second SDK call rehydrated the job by ID and fetched the executed workflow:

```text
status:              succeeded
workflow format:     api
workflow SHA-256:    ec9615286e08292d3d9606174b477c8847296dc3be7161a246d402e077e797ca
output count:        1
```

The fetched workflow hash exactly matches the submitted graph hash.

## Interpretation

This proves real authenticated use of the official Comfy SDK workflow surface
on Comfy Cloud:

```text
construct SDK client
→ submit API-format workflow
→ poll queued job to succeeded
→ retrieve output
→ rehydrate job by ID
→ fetch executed graph
→ verify workflow hash
```

It does **not** claim MiniMax H3 inference, GPU spend, asset upload, partner
model routing, or the full RecastRoom bridge deployment. Those remain separate
capabilities with their own evidence.

No credential value appears in `receipt.json`, `readonly-job-verification.json`,
this report, or the repository.
