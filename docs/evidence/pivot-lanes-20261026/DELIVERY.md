# Pivot-lane absorption

Date: 2026-10-26

## Scope

The operator asked to absorb the three competitive directions while skipping a rights-compliance platform pivot. To protect the focused contest submission, RecastRoom absorbed them as honest product surfaces rather than pretending unfinished systems were production-ready.

## What was added

### 1. Broad studio direction

The workflow catalog now includes a `Studio Queue` concept card for take history, rerenders, and provenance. It is explicitly unavailable in this release.

### 2. Multi-person recasting direction

The catalog and landing roadmap now name a `Multi-Person Recast` engine with per-person references, masks, consent records, and QC. The current proof gallery includes an existing two-person keeper comparison, while the UI clearly states that arbitrary multi-person selection is a roadmap engine.

### 3. Viral gallery direction

`/landing.html` now has a three-result proof gallery:

- core recast;
- style lane;
- two-person proof.

The videos are existing synthetic 480p keeper comparison artifacts from the evidence corpus. No new generation was run.

## Intentional boundary

No new multi-person engine, queue backend, generic VFX marketplace, hosted GPU service, or rights-compliance platform was implemented before the contest deadline.

## Verification

```text
node work/verify_pivot_lanes.mjs
PASS
```

Observed:

- desktop viewport: 1280px;
- desktop horizontal overflow: 0px;
- mobile viewport: 390px;
- mobile horizontal overflow: 0px;
- gallery videos loaded: 3;
- roadmap cards: 4;
- browser console errors/warnings: 0.

Targeted page/catalog tests:

```text
10 passed
```

## Gallery assets

```text
app/web/media/gallery-core-recast.mp4
app/web/media/gallery-style-lane.mp4
app/web/media/gallery-two-person.mp4
```

The source artifacts are the synthetic keeper comparison videos under
`docs/evidence/slate/keepers/`.
