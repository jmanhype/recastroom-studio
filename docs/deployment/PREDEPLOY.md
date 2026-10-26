# Openjutsu H3 Comfy pre-deployment candidate — 2026-10-18

## Result

This is an **offline local candidate and evidence package**, not a runnable
deployment and not a compatibility certification. No model weights were
downloaded, no provider media were uploaded, no remote build was created, no GPU
was started, and no paid service was used.

Owned artifacts:

- `deploy/comfy/comfy-build.yaml`
- `deploy/comfy/asset-manifest.json`
- `deploy/comfy/dependency-matrix.json`
- `deploy/comfy/validation.json`
- `tests/test_deployment_manifest.py`

The workflow remains the repository file
`workflows/openjutsu_h3_lipsync_local.json`, SHA-256
`06424abeb27ac5e7cf95e8fc3a0909c0d7c3e74d1c2b689f86a65719b72d7b21`.

## Pinned code and workflow

The candidate pins the recorded ComfyUI commit and four custom-node commits:

| Repository | Commit |
| --- | --- |
| `comfyanonymous/ComfyUI` | `c06bf5f569d268b80076e5f44126f87cdf835869` |
| `alisson-anjos/ComfyUI-BFSNodes` | `a93cea17a9f4315110f9c66a29935829e956a9cc` |
| `kijai/ComfyUI-KJNodes` | `17195fcfa8a05f601b766a0f09c9733284f47416` |
| `1038lab/ComfyUI-RMBG` | `229529e0ea63fb7085848225d74f91f6dc164956` |
| `Kosinkadink/ComfyUI-VideoHelperSuite` | `4d907bee61e92c2e65af3bd6383a4e4d356126d1` |

The BFS commit was force-moved away from advertised refs after the recorded
dogfood run. A direct bare-SHA Git fetch now fails with
`upload-pack: not our ref`. Reproducible source evidence remains available by
applying the public exact commit patch (SHA-256
`42202e85dd9dba1c59100171bebb80f7c86518660a328a68e65a359977e48e83`, 28,347
bytes) to public parent `7b57eacb7b755ac6d7d7358e0a62e4096d83fce7`. This
reconstruction hashes the exact `bfs_shot_loop.py` at SHA-256
`663541cd85225f6fc4f14b61fb00f4672a8e9330687ebcb3e170988c8c80824d`, but it does
**not** make a builder's bare `gitRef` fetch succeed. That remains a build
blocker.

## Model and implicit-asset closure

The original seven explicit H3 weights are pinned to current immutable Hugging
Face revisions and current LFS SHA-256 values in
`deploy/comfy/asset-manifest.json`. Their total recorded size remains
45,687,037,691 bytes. The dogfood evidence did not record their historical
hashes, so current metadata does **not** prove prior byte identity.

The three missing implicit downloads are now traced to exact pinned source and
current public metadata:

| Asset | Exact source | Current SHA-256 | Bytes | Code-expected destination |
| --- | --- | --- | ---: | --- |
| `birefnet.py` | `1038lab/BiRefNet@4d000788a9698c7f8d67c8c6ce2b40c768f5b909` | `a9566611aa07a6fbb68ddb6ac8e19e62c879a428fbfc2f44efa53d233f2e302f` | 92,068 | `models/RMBG/BiRefNet/birefnet.py` |
| `BiRefNet_config.py` | same revision | `e7b8c2a74f6cea6a59553d517f71d47f2c1d90e670a13416af17c25fe2f3dc52` | 298 | `models/RMBG/BiRefNet/BiRefNet_config.py` |
| `BiRefNet-general.safetensors` | same revision | `77277264c0e8c74149d3ff2fade4fd8176965b7108f3c5fc3b8c9c811edb4519` | 884,878,856 | `models/RMBG/BiRefNet/BiRefNet-general.safetensors` |
| `config.json` | same revision | `966a1f0165b072d2d1309756e71907750e535ba5c3790d8cd0e69713ff3a56cd` | 402 | `models/RMBG/BiRefNet/config.json` |
| YuNet ONNX | `opencv/opencv_zoo@47534e27c9851bb1128ccc0102f1145e27f23f98` | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | 232,589 | `models/opencv_face/face_detection_yunet_2023mar.onnx` |
| SFace ONNX | same revision | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | 38,696,353 | `models/opencv_face/face_recognition_sface_2021dec.onnx` |

The exact RMBG integration at commit
`229529e0ea63fb7085848225d74f91f6dc164956` names all four BiRefNet files at
`py/AILab_BiRefNet.py:33-45`, downloads them with `hf_hub_download` at
`:278-292`, and dynamically imports the downloaded config/model code at
`:327-336`.

The exact reconstructed BFS source at commit
`a93cea17a9f4315110f9c66a29935829e956a9cc` names both immutable OpenCV Zoo
URLs at `bfs_shot_loop.py:762-767`, downloads them at `:770-786`, and expects
them under `models/opencv_face`. It attempts InsightFace first at `:728-751`;
the recorded run used the OpenCV fallback after InsightFace was unavailable.

With the three implicit weights added, current metadata covers 10 model weights
totaling 46,610,845,489 bytes. This is current-metadata closure only. It does
not prove the files used in the historical dogfood run and does not prove that
ComfyBuild stages the custom `RMBG/BiRefNet` and `opencv_face` folders as the
pinned code expects.

## Licenses and rights

No legal conclusion is claimed.

- The OpenCV Zoo repository and both model-specific `LICENSE` files at the
  pinned commit identify Apache-2.0; their hashes are recorded in the manifest.
- `1038lab/BiRefNet` exposes no license metadata in the queried model card. The
  RMBG integration comment attributes BiRefNet models to an upstream
  Apache-2.0 family, but that comment is not license proof for this repository's
  distinct code or weight copy.
- Hugging Face `license: other` labels are metadata, not verified permission for
  this custom deployment.
- The application's MIT license does not confer rights to third-party models,
  custom nodes, or source footage.

## Runtime and dependency matrix

The recorded dogfood environment was Linux, Python 3.13.15, PyTorch
2.11.0+cu130, and ComfyUI 0.41.0. The provider catalog at evidence time listed:

| Base image | Python | Torch | CUDA |
| --- | --- | --- | --- |
| `cuda130-py312` (default) | 3.12 | 2.12.1 | 13.0 |
| `cuda130-py313` | 3.13 | 2.12.1 | 13.0 |
| `cuda128-py311` | 3.11 | 2.8.0 | 12.8 |

No image exactly matches Python 3.13.15 plus Torch 2.11.0+cu130. No base image
is selected. The non-installing Linux/Python 3.12 `uv pip compile --no-build`
preview failed because `groundingdino-py==0.4.0` has no usable wheel. That
proves a no-build resolution blocker, not that a source build or the recorded
runtime was impossible.

Additional closure blockers are listed in `dependency-matrix.json`: no recorded
dependency lock; dynamic imports in RMBG and BFS; unrecorded ffmpeg/OpenCV and
other resolutions; graph keys absent from captured object-info schemas; no real
base-image import test; and the now-unfetchable bare BFS Git ref.

## SDK asset bridge and finality

The current SDK runner does not upload or bind source/reference assets. Node
`1189.inputs.plan` embeds `video`, `global_ref`, and `global_ref2` filenames,
and the SDK contract requires those files to pre-exist in the deployment input
volume. A parallel story is developing the bridge under
`custom_nodes/openjutsu_assets`. The build contents cannot be called final until
that inclusion is resolved and reviewed.

## Verification boundary

Offline structural/hash/model-closure tests are in
`tests/test_deployment_manifest.py`. They parse only repository-owned JSON and
the canonical workflow, use no network, and contain no skip markers.

Measured local checks:

- `PYTHONPATH=src <root-repo>/.venv/bin/python -m pytest -q`:
  **75 passed, 1 pre-existing Starlette/httpx deprecation warning, 17.85s**.
- From the operator-approved temporary directory outside the repository:
  `uvx --offline --python 3.12 --from comfy-cli==1.22.0 comfy --json build validate <owned deploy/comfy directory>`:
  exit 0, `ok=true`, `remote=false`, 13 model entries, and
  `folder_case_checked=false`.
- From that same temporary directory:
  `uvx --offline --python 3.12 --from comfy-cli==1.22.0 comfy --json build push <owned deploy/comfy directory> --dry-run`:
  exit 0, `created=false`, `upload_count=0`, `upload_bytes=0`, `uploaded=0`,
  `deduped=0`, and `folder_case_checked=false`.

Any Comfy CLI `build validate` or `push --dry-run` result is syntax/plan
validation only. In particular, candidate validation leaves folder casing
unchecked and does not fetch custom nodes, download model weights, execute
dynamic imports, validate graph schema on a provider base image, or establish
hosted compatibility.

Therefore the only supported status is: **fail-closed local candidate; runnable
deployment unknown**.
