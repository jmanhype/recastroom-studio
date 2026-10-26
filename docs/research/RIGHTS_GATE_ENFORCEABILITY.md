# Rights gate enforceability review

Date: 2026-10-26

## Question

Is RecastRoom's rights gate technically enforceable, legally meaningful, and viable as a product-control mechanism, or does it overclaim and create avoidable friction?

## Short answer

The control should be called a **recorded rights attestation gate**, not a consent-verification system or legal-clearance system.

It is technically enforceable inside the supported application path:

1. the web UI requires the attestation before preparation;
2. `/api/prepare` rejects missing or invalid attestation before creating a job;
3. the prepared manifest records the attestation;
4. dry-run, legacy ComfyUI, and official Comfy SDK execution recheck that manifest before generation;
5. the CLI now requires an explicit `--attest-rights` flag for both preparation and queueing.

It cannot prove that the uploader told the truth. A local user can edit source code, alter a manifest, or call ComfyUI directly. Those are outside an open-source local application's control boundary.

Therefore, the defensible claim is:

> RecastRoom fail-closes its supported app and CLI paths until the operator records a rights attestation, and it keeps that representation in the job manifest.

The indefensible claim would be:

> RecastRoom verifies consent or guarantees legal clearance.

## Code findings before this review

The inspection found three uneven enforcement points:

1. Web/API preparation correctly rejected missing attestation.
2. Dry-run execution rechecked the manifest.
3. Legacy ComfyUI and official SDK execution did not recheck the manifest immediately before generation.
4. The CLI's `prepare` command silently passed `rights_attested=True`, without an explicit user flag.
5. The CLI's `run` command accepted any workflow without an explicit rights acknowledgement.

Those gaps are corrected in this change set.

## What the gate can and cannot enforce

| Level | Can RecastRoom enforce it locally? | Current status |
|---|---|---|
| User must click/type a representation before using the supported path | Yes | Implemented |
| Unattested jobs are rejected by web/API/CLI | Yes | Implemented |
| Job manifest records that a representation was made | Yes | Implemented |
| Every supported backend rechecks the recorded representation | Yes | Implemented |
| The source/reference files match the prepared manifest | Partially | App routing checks the prepared plan; a local operator can tamper with files |
| The uploader actually owns or licenses the source | No | Outside the system |
| Every depicted/reference person actually consented | No | Outside the system |
| Consent is valid for the jurisdiction and intended use | No | Legal judgement |
| Third parties cannot bypass the app and send a workflow directly to ComfyUI | No | Open local tooling cannot control this |
| Output is cryptographically attributable to a consent record | Not yet | Optional future provenance pack / C2PA work |

## External patterns

### Kestrel

Kestrel's acceptable-use policy covers prompts, uploaded source/reference media, and generated output. For real-person swapping, it requires permission from the person in the photo and every identifiable person in the video, including the person being replaced. It records a per-generation confirmation, automatically screens prompts, and supports reporting/removal.

Relevant pattern:

- per-generation recorded confirmation;
- automated policy screening;
- account/report enforcement.

Source: <https://www.kestrel.video/acceptable-use>

### HeyGen

HeyGen requires a short consent video before creating a video-based digital twin. If the avatar is for another person, that person records their own consent video, including remotely by QR code.

Relevant pattern:

- stronger than a checkbox for self/other likeness;
- fixed consent script;
- remote consent capture.

Source: <https://help.heygen.com/en/articles/12092609-recording-your-consent-video>

### IMAI

IMAI requires prior, informed, written consent and a valid release for real-person likeness or voice, covering the intended generation, commercial use, markets, and duration. It also requires a real-person consent confirmation before video generation and requires users to retain and produce consent records on request. It identifies face and voice inputs as sensitive/biometric data under laws such as GDPR and BIPA.

Relevant pattern:

- consent scope matters: use, market, duration, and commercial context;
- records must be retained and producible;
- likeness/voice inputs can be biometric data.

Source: <https://influencermarketing.ai/ai-content-acceptable-use-notice/>

### VeyoLabs

VeyoLabs uses an Identity Library and asset approval before real-face generation, but explicitly states that its technical route does not certify authorship, rights, consent, or legal clearance.

Relevant pattern:

- identity/liveness workflows can reduce some abuse;
- even stronger verification does not equal legal clearance;
- clear role separation is necessary.

Source: <https://veyolabs.com/terms>

### C2PA Content Credentials

C2PA defines cryptographically bound provenance assertions. It can show that an asset and its provenance history have not been tampered with since signing and can record actions such as AI use. C2PA itself says the data does not judge whether the provenance is true; it checks validity, trust in the signer, and binding to the asset.

Relevant pattern:

- useful for tamper-evident history;
- not a consent detector;
- not a substitute for a release or licence.

Source: <https://spec.c2pa.org/specifications/specifications/2.2/explainer/Explainer.html>

### Legal direction

Rights of publicity, privacy, voice, and digital-replica rules vary by jurisdiction and use. California AB 2602 requires specific, informed provisions for performer digital replicas and representation in negotiation. Proposed federal NO FAKES legislation would create authorization and liability rules for unauthorized digital replicas, but proposed legislation is not a reason to present current uncertainty as settled law.

These signals support explicit AI-specific consent records, especially for commercial performances. They do not make a local checkbox legally sufficient by itself.

Sources:

- California AB 2602 overview: <https://www.gov.ca.gov/2024/09/17/governor-newsom-signs-bills-to-protect-digital-likeness-of-performers/>
- NO FAKES reintroduction: <https://www.coons.senate.gov/news/press-releases/senators-coons-blackburn-reps-salazar-dean-colleagues-reintroduce-no-fakes-act-to-protect-individuals-and-creators-from-digital-replicas>

## Product assessment

The gate is not debilitating in its current form because it is one explicit action in the supported workflow. It becomes debilitating if it:

- demands legal information the user does not have;
- blocks local deterministic dry runs in a way that prevents judges from trying the app;
- claims legal certainty it cannot prove;
- requires a hosted identity workflow that a local open-source tool cannot satisfy;
- treats every educational or private experiment as a commercial production.

The gate is valuable when it:

- makes the operator pause at the moment of upload;
- binds the representation to concrete job media;
- creates a persistent manifest;
- keeps supported execution paths fail-closed;
- leaves legal responsibility and evidence retention explicit.

## Recommended positioning

### Keep

- Required web attestation.
- Explicit CLI acknowledgement.
- Manifest recording.
- Backend recheck.
- Clear legal boundary text.
- Public wording: "No attestation, no render."

### Rename

Use **rights attestation gate**, not:

- consent verification;
- legal clearance;
- rights enforcement;
- provenance proof.

### Add later, without blocking the contest

1. **Provenance pack**
   - source licence URL or ownership note;
   - reference consent reference ID;
   - consent scope: project, use, market, duration;
   - hashes of source/reference media;
   - UTC timestamp;
   - operator identity;
   - canonical attestation text and version.

2. **Optional signed output**
   - C2PA Content Credential recording the RecastRoom edit;
   - link to the local provenance pack without exposing private personal data.

3. **Hosted verified mode**
   - consent video or signed release;
   - identity/liveness match for self-replacement;
   - separate review queue for third-party likeness;
   - revocation, reporting, and takedown.

4. **Demo fixture**
   - pre-attested synthetic fixture for judges;
   - no real-person likeness;
   - demonstrates the gate without forcing a legal claim about third-party media.

## Final judgement

The rights gate is realistic and worth keeping only if it is positioned as an **audit and accountability control**. It is not a legal guarantee and should not be the project's only differentiator.

RecastRoom's stronger differentiators are:

1. exact source-audio restoration;
2. performance-preserving workflow;
3. deterministic evidence manifests;
4. reproducible Comfy graph;
5. rights responsibility made explicit;
6. reviewable source/final artifacts.

Responsibility controls should support those capabilities, not replace them.
