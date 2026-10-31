# SPDX-License-Identifier: MIT
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


class WorkflowError(RuntimeError):
    pass


def _schedule_from_prompt(prompt: str) -> str:
    marker = "Exact word/frame schedule:\n"
    start = prompt.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    end = prompt.find("\n\nIntegrate", start)
    return prompt[start:] if end < 0 else prompt[start:end]


def load_workflow(path: str | Path) -> dict[str, Any]:
    workflow = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(workflow, dict):
        raise WorkflowError("workflow root must be an object")
    return workflow


def configure_workflow(
    template: dict[str, Any],
    *,
    video_name: str,
    reference_1: str,
    reference_2: str | None,
    prompt: str,
    seed: int = 49,
    output_prefix: str = "openjutsu/result",
    with_audio: bool = True,
) -> dict[str, Any]:
    workflow = copy.deepcopy(template)
    try:
        planner = workflow["1189"]
        plan = json.loads(planner["inputs"]["plan"])
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise WorkflowError("workflow is missing a valid BFSShotPlanner node 1189") from error

    # ComfyUI can cache unrelated local reference descriptions in this field.
    # Public jobs intentionally carry only the generic runtime filenames below.
    plan.pop("ref_details", None)
    plan["video"] = video_name
    plan["global_ref"] = reference_1
    plan["global_ref2"] = reference_2 or ""
    plan["audio_mode"] = "auto"
    planner["inputs"]["plan"] = json.dumps(plan, separators=(",", ":"))

    required = {
        "1152": "PrimitiveStringMultiline prompt",
        "1177": "BFSShotH3ConditioningSimple",
        "13": "RandomNoise seed",
        "181": "BasicScheduler",
        "586": "Character Swap LoRA",
        "200": "MiniMax H3 timed source audio",
        "201": "MiniMax H3 exact audio lock",
        "751": "VideoCombine output",
        "1110": "Comparison output",
    }
    for node_id, label in required.items():
        if node_id not in workflow:
            raise WorkflowError(f"workflow is missing node {node_id} ({label})")

    workflow["1152"]["inputs"]["value"] = prompt
    workflow["1177"]["inputs"]["with_audio"] = with_audio
    workflow["1177"]["inputs"]["source_blur"] = "head + hands (keep mouth)"
    workflow["1177"]["inputs"]["source_blur_strength"] = 1.0
    workflow["1177"]["inputs"]["source_blur_segmenter"] = "SAM 3.1"
    workflow["1177"]["inputs"]["source_blur_effect"] = "blur"
    workflow["13"]["inputs"]["noise_seed"] = seed
    workflow["181"]["inputs"]["steps"] = 8
    workflow["586"]["inputs"]["strength_model"] = 1.0
    workflow["751"]["inputs"]["filename_prefix"] = output_prefix
    workflow["1110"]["inputs"]["filename_prefix"] = output_prefix + "_compare"
    if workflow["14"]["inputs"].get("latent_image") != ["201", 0]:
        workflow["14"]["inputs"]["latent_image"] = ["201", 0]
    workflow["200"]["inputs"]["start_frame"] = 0
    workflow["200"]["inputs"]["gain_db"] = 0.0
    workflow["201"]["inputs"]["mix_policy"] = "sum"
    workflow["201"]["inputs"]["overflow_policy"] = "crop"
    workflow["201"]["inputs"]["legacy_start_frame"] = 0
    return workflow


def prepared_run_contract(
    workflow: dict[str, Any],
    *,
    prompt: str,
    timing_input: str,
    timing_basis: str,
) -> dict[str, Any]:
    """Project the actual prepared graph without exposing local absolute paths."""
    try:
        plan = json.loads(workflow["1189"]["inputs"]["plan"])
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise WorkflowError("workflow is missing a valid BFSShotPlanner node 1189") from error

    if timing_input == "supplied":
        timing_status = "Word timings supplied"
    elif timing_input == "omitted":
        timing_status = "No word timings supplied; using fallback prompt"
    else:
        raise WorkflowError("timing_input must be supplied or omitted")

    conditioning = workflow["1177"]["inputs"]
    return {
        "source": plan.get("video", ""),
        "reference_1": plan.get("global_ref", ""),
        "reference_2": plan.get("global_ref2") or None,
        "seed": workflow["13"]["inputs"]["noise_seed"],
        "steps": workflow["181"]["inputs"]["steps"],
        "character_swap_strength": workflow["586"]["inputs"]["strength_model"],
        "audio_conditioning": bool(workflow["1177"]["inputs"].get("with_audio")),
        "source_treatment": {
            "blur": conditioning.get("source_blur", ""),
            "strength": conditioning.get("source_blur_strength"),
            "segmenter": conditioning.get("source_blur_segmenter", ""),
            "effect": conditioning.get("source_blur_effect", ""),
        },
        "timing": {
            "input": timing_input,
            "status": timing_status,
            "basis": timing_basis,
            "schedule": _schedule_from_prompt(prompt),
        },
        "nodes": {
            "planner": "1189",
            "prompt": "1152",
            "conditioning": "1177",
            "seed": "13",
            "scheduler": "181",
            "character_swap": "586",
            "audio": "200",
            "exact_audio_lock": "201",
            "output": "751",
        },
    }
