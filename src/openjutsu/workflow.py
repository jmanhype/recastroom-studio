# SPDX-License-Identifier: MIT
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


class WorkflowError(RuntimeError):
    pass


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
