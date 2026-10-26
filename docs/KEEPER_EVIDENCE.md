# Eleven-workflow keeper evidence pack

`docs/evidence/slate/` is the contest-grade evidence copy for the human-approved
Plan B slate. It intentionally contains:

- eleven final videos, side-by-side compares, contact sheets, and Qwen reports;
- the source keeper receipt, final human approval, synthetic-asset manifest,
  and H3 source authorization notes;
- one machine-readable `manifest.json` with rights provenance, consent,
  workflow parameters, seed, QC result, human verdict, media specs, byte size,
  and SHA-256 for every imported artifact.

The pack excludes the rejected anime variant and all prior private film/TV
experiments. The included sources are project-generated synthetic plates/targets
plus the operator-authorized Jay identity; provenance receipts are copied under
`receipts/`.

For public release, the twenty-two MP4s are stream-copy remuxes with no container
workflow metadata. Their encoded video/audio packet hashes remain unchanged from
the human-approved keepers; only the manifest's container byte/hash receipts
changed.

## Intended eleven-workflow enumeration

| Keeper | Intended format concept | Seed | Qwen overall |
|---|---|---:|---:|
| `seed50_jay_plate_a` | Core identity swap | 50 | 9 |
| `era_1985_plate_a` | Era restyle | 50 | 8 |
| `era_noir_plate_a_fullbw` | Era restyle | 50 | 9 |
| `fanwipe_man_plate_a` | Fan wipe | 50 | 9 |
| `fanwipe_young_plate_a` | Fan wipe | 50 | 9 |
| `impossible_robot_mechanical_mouth` | Impossible casting | 51 | 8 |
| `hotel_jay_repair_seed51` | Singing performance swap | 51 | 9 |
| `object_jay` | Object preservation | 50 | 9 |
| `twoperson_jay_trimmed_hostrestored` | Selective person swap | 50 | 9 |
| `lenspush_jay_repair_seed51` | Lens interaction | 51 | 9 |
| `cameramove_jay_stretch` | Camera-move preservation | 50 | 8 |

The rejected optional `era_anime_plate_a` variant is documented in the manifest
but has no included artifact.

Verify from the repository root:

```bash
python tools/verify_keeper_evidence.py docs/evidence/slate/manifest.json
```

To reproduce the immutable pass plus controlled one-byte failure transcript:

```bash
python tools/selftest_keeper_evidence.py \
  docs/evidence/slate/manifest.json \
  --report docs/evidence/slate-verification.md
```

The verifier requires the manifest to account for every file in the directory.
It fails closed on missing or changed bytes, unsafe or symlinked paths, omitted
keepers, private-IP or unconsented rights fields, missing approvals, invalid
workflow/QC fields, media-spec drift, and unmanifested files.
