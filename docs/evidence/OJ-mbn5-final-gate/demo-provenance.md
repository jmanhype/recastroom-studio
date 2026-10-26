# Demo v1 provenance boundary

Current candidate: `recastroom-demo-v1.mp4` from the owner's
`openjutsu_planb/demo_v1` public-candidate directory. It is the previously
assessed demo with only the final twelve-second title card replaced to resolve
the public-name collision. No private development media was inspected.

The source demo remains bound by `openjutsu_planb/RELEASE_RECEIPTS.md` and
`demo_v1/openjutsu_demo_v1.html` to SHA-256
`7cbe824a3e7dc4ff515c23fe1672630e938e2520e9b7c3686c87fa90a4db089d`.
The rebranded candidate is SHA-256
`a14b3eb287e3daf0ed4dd27e238048c1725c087c0b48cf8ffb301758e637f13f`.
The first 96 seconds are a visual re-encode of that source; the closing card
now reads **RecastRoom Studio**. The source audio stream is copied unchanged:
decoded stereo PCM SHA-256 is
`06f5984c4e2d771437a6fd028efb9e4861f9f70b55e7905898baf8faa7b7fe15` for both
files. Duration remains 108.052 seconds and is independently re-probed by the
final gate, not trusted from the source receipt.

Public keeper provenance and consent are recorded in
`docs/evidence/slate/manifest.json`, with source basis project-generated
synthetic plates/targets and operator-authorized Jay identity, and linked
`receipts/HUMAN_APPROVAL.md`. The keeper verifier checks the artifact bytes.

**Boundary:** these receipts do not constitute a frame-by-frame composition
manifest for the complete demo or separate clearance for narration/music,
UI capture and every third-party model/node license. Therefore exact-demo
rights remain OWNER_BLOCKED, not PASS. Before publication the owner must
provide a hash-bound timeline/source manifest covering every segment and audio
track and confirm permission/consent and model/node license compliance.
Human keeper approval is not expanded into legal clearance for other material.
Changing the demo (including its final URL card) requires a new approved hash,
provenance receipt and probe; the gate refuses unknown bytes before probing.
