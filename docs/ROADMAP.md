# RecastRoom roadmap

This roadmap keeps RecastRoom focused on performance-preserving dialogue recasting. It borrows competitive patterns only when they make the core job clearer, more trustworthy, more reproducible, or easier to review.

## v0.1: Focused contest release

Status: local release candidate complete; public repository/demo/social/form remain owner-gated.

Scope:

- one-person continuous dialogue recast;
- recorded operator attestation across app and CLI paths;
- exact source-audio restoration;
- deterministic dry run;
- local ComfyUI and official SDK runners;
- public landing, sound lab, proof gallery, runtime-cost disclosure, setup diagnostics, and focused comparison.

Release gate:

```text
all local technical gates pass
public repository and final demo URL published
clean-checkout install/launch rerun
X post and Typeform submitted
```

## v0.2: Production recasting

Purpose: turn the focused proof into a dependable production engine.

- multi-person target assignment;
- separate references and masks per performer;
- separate rights and provenance fields per performer;
- per-person QC report;
- shot/take timeline;
- rerender one take;
- accepted-take provenance;
- consent and provenance pack.

Promotion gate:

```text
multi-person demo passes human identity/background/audio review
every target has an independent rights record
take state survives app restart
```

## v0.3: Studio surface

Purpose: expose production capability without becoming a generic video studio.

- expanded workflow catalog;
- shareable recipe schema;
- model/runtime/cost roles;
- queue persistence;
- take-review editor;
- public recipe gallery.

Promotion gate:

```text
recipe import validates safely
jobs and takes persist across restart
recipe provenance is exportable
```

## v0.4: Developer platform

Purpose: make RecastRoom controllable by agents and external production systems.

- MCP server;
- structured API errors and job events;
- CLI-friendly status/review commands;
- webhooks;
- SDK examples;
- machine-readable evidence export.

Promotion gate:

```text
external agent completes inspect → prepare → run → review without hidden UI state
API contract has versioning and tests
```

## v0.5: Hosted try mode

Purpose: provide a public try path without endangering operator credentials or public users.

- public deterministic dry run;
- upload validation and malware scanning;
- abuse controls;
- rate limits;
- hosted GPU execution;
- spend caps;
- reporting and takedown.

Promotion gate:

```text
security review passes
cost and abuse limits are enforced server-side
privacy and retention boundaries are public
```
