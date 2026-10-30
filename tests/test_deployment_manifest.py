# SPDX-License-Identifier: MIT
import hashlib
import json
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy" / "comfy"
WORKFLOW = ROOT / "workflows" / "recastroom_h3_workflow.json"
WORKFLOW_SHA256 = "79fa70d6b9d3e13852e179cff6f9a3aa36637a8543c600c36517be1b4a2d1a58"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_workflow_hash_and_birefnet_selection_are_unchanged() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    workflow = load_json(WORKFLOW)

    assert hashlib.sha256(WORKFLOW.read_bytes()).hexdigest() == WORKFLOW_SHA256
    assert manifest["workflow"] == {
        "path": "workflows/recastroom_h3_workflow.json",
        "sha256": WORKFLOW_SHA256,
        "node_count": 29,
        "unique_class_type_count": 26,
        "required_birefnet_variant": "BiRefNet-general",
    }
    assert workflow["1022"]["class_type"] == "BiRefNetRMBG"
    assert workflow["1022"]["inputs"]["model"] == "BiRefNet-general"


def test_recorded_repositories_and_source_pins_are_exact() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    repositories = {item["name"]: item for item in manifest["code"]["repositories"]}

    expected = {
        "ComfyUI": (
            "9fe7ef764d0452dcc9dcb925efd076d4e68eece1",
            "e7a2166150f7624311e71d8d2115b3a079c9b79a4702b59a186f76587ccaa121",
            "ea8139066d4e65b9e82fd1e3f6633ef853b10aac19acf8050433861a87bf6d8c",
        ),
        "ComfyUI-BFSNodes": (
            "de5c7215840097d68e29b6b4903663698319065a",
            "9524c3ee79765561cfd613a284080d823594550ff5ae97cb8e40e47d8a6cdff7",
            "daa6d4d043bf0978d4aad850f08b292c877a4f55d7376360692006707ea73aa8",
        ),
        "ComfyUI-KJNodes": (
            "37a6c45a07bb06cc392431ddbbc741e691c467f4",
            "e8cc1fb089c6e74bb5f326e949fd89ea7653de0d193d7a385c38af44e66656bd",
            "3c84ba5c3d134af053b3d832a67e616d25fcbc4e97b9d906ca608986aabd5b58",
        ),
        "ComfyUI-SolAttn_triton": (
            "26d816ebd4f1e43a2c6e4d4759be3137f10a7a73",
            None,
            None,
        ),
        "ComfyUI-RMBG": (
            "a66a5e641a54988d80ed6aad18946081c85f309e",
            "1a0c15a9d771cc7d6290258cdb713d2aa2b4141173b8a2d794fb282084a9ca6b",
            "184edc073ba444d31c0a354d1552ee996fcc2e406b14dadda5454bfa73b9af19",
        ),
        "ComfyUI-VideoHelperSuite": (
            "4d907bee61e92c2e65af3bd6383a4e4d356126d1",
            "dbf7158d81418ace41097db503440bb70f41b6250d5d0b3ab3b3c86271b7b2a3",
            "299e28c3c62ec7580003132bef62e58c01fa817eff6db5a51c9f5b9e1737160a",
        ),
        "ComfyUI-H3-ExactAudioLock": (
            "559196913108ca9bb58abf6f1a3d06be369532e9",
            "d65fcec7afa150547960f4b55fb8b15bc75f2906b43d2794e6dbbdcd6e324a1f",
            None,
        ),
    }
    assert set(repositories) == set(expected)
    for name, (commit, requirements_hash, pyproject_hash) in expected.items():
        assert repositories[name]["commit"] == commit
        assert repositories[name]["requirements_sha256"] == requirements_hash
        assert repositories[name]["pyproject_sha256"] == pyproject_hash
        assert len(repositories[name]["license_sha256"]) == 64


def test_all_assets_have_immutable_current_hash_size_and_destination() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    build = load_json(DEPLOY / "comfy-build.yaml")
    assets = manifest["assets"]
    build_sources = {item["sourceUri"] for item in build["definition"]["models"]}

    assert len(assets) == 13
    assert len({item["id"] for item in assets}) == 13
    for item in assets:
        assert len(item["revision"]) >= 40
        assert len(item["sha256"]) == 64
        assert item["bytes"] > 0
        assert item["destination"].startswith("models/")
        assert item["prior_byte_identity_proven"] is False
        if item["source"] == "huggingface":
            expected_uri = (
                f"https://huggingface.co/{item['repository']}/resolve/"
                f"{item['revision']}/{item['source_path']}"
            )
            assert expected_uri in build_sources
        else:
            expected_uri = (
                f"https://github.com/{item['repository']}/raw/"
                f"{item['revision']}/{item['source_path']}"
            )
            assert expected_uri in build_sources


def test_explicit_h3_model_pins_and_totals_match_recorded_inventory() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    by_id = {item["id"]: item for item in manifest["assets"]}
    explicit_ids = {
        "h3-diffusion",
        "h3-text-encoder",
        "h3-video-vae",
        "h3-audio-vae",
        "h3-turbo-lora",
        "h3-character-swap-lora",
        "sam31-segmenter",
    }

    assert set(by_id) >= explicit_ids
    assert sum(by_id[item]["bytes"] for item in explicit_ids) == 46_582_794_523
    assert sum(
        item["bytes"] for item in by_id.values() if item["kind"] == "model_weight"
    ) == 47_506_602_321
    assert manifest["closure"]["recorded_explicit_h3_weight_bytes"] == 46_582_794_523
    assert manifest["closure"]["model_weight_bytes"] == 47_506_602_321


def test_implicit_birefnet_and_opencv_closure_is_exact_but_not_historical_proof() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    by_id = {item["id"]: item for item in manifest["assets"]}

    expected = {
        "birefnet-code": (
            "birefnet.py",
            "a9566611aa07a6fbb68ddb6ac8e19e62c879a428fbfc2f44efa53d233f2e302f",
            92_068,
            "models/RMBG/BiRefNet/birefnet.py",
        ),
        "birefnet-config": (
            "BiRefNet_config.py",
            "e7b8c2a74f6cea6a59553d517f71d47f2c1d90e670a13416af17c25fe2f3dc52",
            298,
            "models/RMBG/BiRefNet/BiRefNet_config.py",
        ),
        "birefnet-general": (
            "BiRefNet-general.safetensors",
            "77277264c0e8c74149d3ff2fade4fd8176965b7108f3c5fc3b8c9c811edb4519",
            884_878_856,
            "models/RMBG/BiRefNet/BiRefNet-general.safetensors",
        ),
        "birefnet-runtime-config": (
            "config.json",
            "966a1f0165b072d2d1309756e71907750e535ba5c3790d8cd0e69713ff3a56cd",
            402,
            "models/RMBG/BiRefNet/config.json",
        ),
        "yunet": (
            "models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
            "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
            232_589,
            "models/opencv_face/face_detection_yunet_2023mar.onnx",
        ),
        "sface": (
            "models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
            "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
            38_696_353,
            "models/opencv_face/face_recognition_sface_2021dec.onnx",
        ),
    }
    for asset_id, (source_path, digest, size, destination) in expected.items():
        assert by_id[asset_id]["source_path"] == source_path
        assert by_id[asset_id]["sha256"] == digest
        assert by_id[asset_id]["bytes"] == size
        assert by_id[asset_id]["destination"] == destination
        assert by_id[asset_id]["prior_byte_identity_proven"] is False

    assert by_id["yunet"]["lfs_pointer_sha256"] == (
        "0b6ceccb83e3d6cb38ae9a92499469937eb210e0267f26f7e68c5a13b53818c3"
    )
    assert by_id["sface"]["lfs_pointer_sha256"] == (
        "056d0f5482483764dcac0d4b3beacc2a878e23f2b4ce935b50ded42624644fea"
    )
    assert by_id["birefnet-general"]["license_verified"] is False
    assert by_id["yunet"]["license_source_verified"] is True
    assert by_id["sface"]["license_source_verified"] is True


def test_implicit_asset_traces_cite_exact_pinned_code_paths() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    traces = {item["asset"] for item in manifest["code"]["implicit_asset_traces"]}

    assert traces == {"BiRefNet-general and support code/config", "YuNet and SFace"}
    birefnet = next(
        item
        for item in manifest["code"]["implicit_asset_traces"]
        if item["asset"] == "BiRefNet-general and support code/config"
    )
    opencv = next(
        item
        for item in manifest["code"]["implicit_asset_traces"]
        if item["asset"] == "YuNet and SFace"
    )
    assert birefnet["pinned_integration_path"] == "py/AILab_BiRefNet.py"
    assert birefnet["integration_commit"] == "a66a5e641a54988d80ed6aad18946081c85f309e"
    assert birefnet["source_lines"] == "33-45, 278-292, and 308-348"
    assert birefnet["expected_runtime_directory"] == "models/RMBG/BiRefNet"
    assert birefnet["dynamic_imports"] is True
    assert opencv["pinned_integration_path"] == "bfs_shot_loop.py"
    assert opencv["integration_commit"] == "de5c7215840097d68e29b6b4903663698319065a"
    assert opencv["source_lines"] == "728-751 and 759-786"
    assert opencv["expected_runtime_directory"] == "models/opencv_face"
    assert opencv["dynamic_imports"] is True


def test_build_spec_exactly_matches_asset_manifest() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    build = load_json(DEPLOY / "comfy-build.yaml")
    definition = build["definition"]
    manifest_by_id = {item["id"]: item for item in manifest["assets"]}
    build_sources = {item["sourceUri"] for item in definition["models"]}

    assert build["id"] is None
    assert build["syncedRevision"] is None
    assert "no runnable-build or license claim" in build["description"]
    assert definition["baseComfyVersion"] == "9fe7ef764d0452dcc9dcb925efd076d4e68eece1"
    assert len(definition["models"]) == 13
    for item in definition["models"]:
        matches = [
            asset
            for asset in manifest["assets"]
            if asset["sha256"] == item["sha256"]
            and asset["destination"] == f"models/{item['type']}/{item['filename']}"
            and item["sourceUri"] in build_sources
        ]
        assert len(matches) == 1
        assert manifest_by_id[matches[0]["id"]]["source_path"].endswith(item["filename"])

    custom_nodes = {item["name"]: item for item in definition["customNodes"]}
    assert {name: item.get("gitRef") for name, item in custom_nodes.items()} == {
        "ComfyUI-BFSNodes": "de5c7215840097d68e29b6b4903663698319065a",
        "ComfyUI-KJNodes": "37a6c45a07bb06cc392431ddbbc741e691c467f4",
        "ComfyUI-RMBG": "a66a5e641a54988d80ed6aad18946081c85f309e",
        "ComfyUI-VideoHelperSuite": "4d907bee61e92c2e65af3bd6383a4e4d356126d1",
        "ComfyUI-SolAttn_triton": "26d816ebd4f1e43a2c6e4d4759be3137f10a7a73",
        "ComfyUI-H3-ExactAudioLock": "559196913108ca9bb58abf6f1a3d06be369532e9",
        "openjutsu_assets": None,
    }
    assert custom_nodes["openjutsu_assets"] == {
        "name": "openjutsu_assets",
        "source": "local",
        "localPath": "openjutsu_assets",
    }

    turbo_lora = next(
        item
        for item in definition["models"]
        if item["filename"] == "minimax_h3_dmd_ref2va_8step_turbo_pruned.safetensors"
    )
    workflow = load_json(ROOT / "workflows/recastroom_h3_workflow.json")
    requested_lora = workflow["64"]["inputs"]["lora_name"]
    assert turbo_lora["type"] == "loras"
    assert requested_lora == turbo_lora["filename"]


def test_candidate_fails_closed_and_discloses_pending_sdk_bridge() -> None:
    manifest = load_json(DEPLOY / "asset-manifest.json")
    candidate = manifest["candidate"]

    assert candidate["candidate_only"] is True
    assert candidate["runnable_deployment_proven"] is False
    assert candidate["compatibility_status"] == "fail_closed_unknown"
    assert candidate["selected_base_image"] is None
    assert candidate["recorded_bfs_commit_fetchable_by_git_ref"] is False
    assert candidate["sdk_asset_bridge_status"] == "included_in_build_spec"
    assert candidate["sdk_asset_bridge_required_for_final_build_contents"] is True
    assert manifest["closure"]["current_public_metadata_resolved"] is True
    assert manifest["closure"]["historical_byte_identity_proven"] is False
    assert manifest["closure"]["runtime_destination_and_import_closure_proven"] is False
    assert manifest["rights"]["legal_conclusion_claimed"] is False
    assert "yunet" in manifest["rights"]["verified_license_sources"]
    assert "birefnet-general" in manifest["rights"]["unknown_or_unverified_assets"]


def test_dependency_matrix_fails_closed_without_exact_base_image() -> None:
    matrix = load_json(DEPLOY / "dependency-matrix.json")

    assert matrix["recorded_runtime"]["python"] == "3.13.15"
    assert matrix["recorded_runtime"]["torch"] == "2.11.0+cu130"
    assert matrix["recorded_runtime"]["dependency_lock_recorded"] is False
    assert {
        (item["python"], item["torch"], item["cuda"])
        for item in matrix["provider_base_images"]
    } == {("3.12", "2.12.1", "13.0"), ("3.13", "2.12.1", "13.0"), ("3.11", "2.8.0", "12.8")}
    assert matrix["selection"]["selected_base_image"] is None
    assert matrix["selection"]["decision"] == "fail_closed"
    assert matrix["dependency_analysis"]["packages_installed"] is False
    assert matrix["dependency_analysis"]["recorded_resolution_preview"]["exit_code"] == 1
    assert any("groundingdino-py" in item for item in matrix["dependency_analysis"]["blockers"])
    assert any("dynamically imports" in item for item in matrix["dependency_analysis"]["blockers"])
    assert any("BFSShotRepack.ref_image" in item for item in matrix["dependency_analysis"]["blockers"])


def test_cli_validation_receipt_cannot_be_promoted_to_runtime_proof() -> None:
    receipt = load_json(DEPLOY / "validation.json")

    assert receipt["validate"] == {
        "command": "uvx --from comfy-cli==1.24.0 comfy --json build validate deploy/comfy --custom-nodes-dir custom_nodes",
        "exit_code": 0,
        "ok": True,
        "remote": False,
        "model_count": 13,
        "custom_node_count": 7,
        "folder_case_checked": False,
    }
    assert receipt["push_dry_run"]["exit_code"] == 0
    assert receipt["push_dry_run"]["created"] is False
    assert receipt["push_dry_run"]["upload_count"] == 1
    assert receipt["push_dry_run"]["uploaded"] == 0
    assert receipt["interpretation"]["runnable_build_proven"] is False
    assert receipt["interpretation"]["hosted_compatibility_proven"] is False
    assert receipt["interpretation"]["model_weights_downloaded"] is False
    assert receipt["interpretation"]["custom_nodes_fetched"] is False
    assert receipt["interpretation"]["dynamic_imports_executed"] is False


def test_manifests_contain_no_private_paths_or_secret_material() -> None:
    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            DEPLOY / "asset-manifest.json",
            DEPLOY / "comfy-build.yaml",
            DEPLOY / "dependency-matrix.json",
            DEPLOY / "validation.json",
        )
    )

    for forbidden in ("/Users/", "/private/tmp", "account-status.json", "api_key", "credential"):
        assert forbidden not in serialized
    assert Path(DEPLOY / "account-status.json").exists() is False


def test_offline_test_contract_has_no_network_or_skips() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "urllib" not in imported_names
    assert "requests" not in imported_names
    assert "pytest" not in imported_names
    assert not any(
        node.decorator_list
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    )
