# SPDX-License-Identifier: MIT
import pytest

from openjutsu.workflow import WorkflowError, configure_workflow, load_workflow


def test_configure_workflow_requires_planner() -> None:
    with pytest.raises(WorkflowError):
        configure_workflow({}, video_name="x.mp4", reference_1="a.png", reference_2=None, prompt="x")


def test_configure_workflow_mutates_known_nodes() -> None:
    import json

    template = {
        "1189": {
            "class_type": "BFSShotPlanner",
            "inputs": {"plan": json.dumps({"video": "old.mp4", "ref_details": {"cached.png|": "private"}})},
        },
        "1152": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": "old"}},
        "1177": {"class_type": "BFSShotH3ConditioningSimple", "inputs": {"with_audio": False, "source_blur": "face"}},
        "13": {"class_type": "RandomNoise", "inputs": {"noise_seed": 1}},
        "181": {"class_type": "BasicScheduler", "inputs": {"steps": 20}},
        "586": {"class_type": "LoraLoaderModelOnly", "inputs": {"strength_model": 0}},
        "200": {"class_type": "MiniMaxH3TimedAudio", "inputs": {"start_frame": 9, "gain_db": 2.0}},
        "201": {
            "class_type": "MiniMaxH3ExactAudioLock",
            "inputs": {"mix_policy": "replace", "overflow_policy": "fail", "legacy_start_frame": 9},
        },
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"latent_image": ["1177", 1]}},
        "751": {"class_type": "VHS_VideoCombine", "inputs": {"filename_prefix": "old"}},
        "1110": {"class_type": "SaveVideo", "inputs": {"filename_prefix": "old-compare"}},
    }
    result = configure_workflow(
        template,
        video_name="source.mp4",
        reference_1="ref1.png",
        reference_2="ref2.png",
        prompt="NEW PROMPT",
        seed=49,
        output_prefix="openjutsu/test",
    )
    plan = json.loads(result["1189"]["inputs"]["plan"])
    assert "ref_details" not in plan
    assert plan["video"] == "source.mp4"
    assert plan["global_ref"] == "ref1.png"
    assert plan["global_ref2"] == "ref2.png"
    assert result["1152"]["inputs"]["value"] == "NEW PROMPT"
    assert result["1177"]["inputs"]["with_audio"] is True
    assert result["1177"]["inputs"]["source_blur"] == "head + hands (keep mouth)"
    assert result["1177"]["inputs"]["source_blur_segmenter"] == "SAM 3.1"
    assert result["1177"]["inputs"]["source_blur_effect"] == "blur"
    assert result["13"]["inputs"]["noise_seed"] == 49
    assert result["181"]["inputs"]["steps"] == 8
    assert result["586"]["inputs"]["strength_model"] == 1.0
    assert result["14"]["inputs"]["latent_image"] == ["201", 0]
    assert result["200"]["inputs"]["start_frame"] == 0
    assert result["200"]["inputs"]["gain_db"] == 0.0
    assert result["201"]["inputs"]["mix_policy"] == "sum"
    assert result["201"]["inputs"]["overflow_policy"] == "crop"
    assert result["201"]["inputs"]["legacy_start_frame"] == 0


def test_bundled_workflow_is_c1_v4_contract() -> None:
    from pathlib import Path

    workflow = load_workflow(
        Path(__file__).resolve().parents[1] / "workflows/openjutsu_h3_lipsync_local.json"
    )
    assert "1192" not in workflow
    assert workflow["586"]["inputs"]["lora_name"] == "minimax_h3_character_swap_v1.1_ref2va_fro.safetensors"
    assert workflow["64"]["inputs"]["model"] == ["586", 0]
    assert workflow["14"]["inputs"]["latent_image"] == ["201", 0]
    assert workflow["1177"]["inputs"]["source_blur"] == "head + hands (keep mouth)"
    assert workflow["1177"]["inputs"]["source_blur_segmenter"] == "SAM 3.1"
    assert workflow["200"]["class_type"] == "MiniMaxH3TimedAudio"
    assert workflow["201"]["class_type"] == "MiniMaxH3ExactAudioLock"
