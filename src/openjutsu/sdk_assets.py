# SPDX-License-Identifier: MIT
"""Local validation and narrowly scoped BFS asset binding (no network)."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from comfy_sdk import Comfy, Workflow

WorkflowGraph: TypeAlias = dict[str, dict[str, Any]]
PlannerData: TypeAlias = dict[str, Any]
AssetFiles: TypeAlias = dict[str, tuple[bytes, str]]

BRIDGE_ID = "openjutsu_assets"
BRIDGE_TYPE = "OpenJutsuAssetPlan"


def _require(condition):
    if not condition:
        raise ValueError("Unsupported input")


def validate_inputs(
    workflow: WorkflowGraph,
    source: str | Path,
    reference_1: str | Path,
    reference_2: str | Path | None = None,
) -> tuple[PlannerData, AssetFiles, str]:
    try:
        _require(workflow["1189"]["class_type"] == "BFSShotPlanner")
        _require(workflow["751"]["class_type"] == "VHS_VideoCombine")
        _require(BRIDGE_ID not in workflow)
        plan = json.loads(workflow["1189"]["inputs"]["plan"])
        _require(isinstance(plan, dict))
        _require(all(isinstance(plan.get(k), str) for k in ("video", "global_ref", "global_ref2")))
        _require(isinstance(plan.get("segs"), list))
        # This adapter owns only three file slots; don't silently retain other
        # local references, masks or newer multi-reference plans.
        _require(not plan.get("global_refs") or plan["global_refs"] == [plan["global_ref"], plan["global_ref2"]])
        def check_nested(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    if k in {"ref", "ref2", "refs", "mask_video", "file"}:
                        _require(not v)
                    check_nested(v)
            elif isinstance(value, list):
                for v in value:
                    check_nested(v)
        check_nested(plan)
        files = {}
        for key, value, suffixes in (
            ("video", source, {".mp4", ".mov", ".webm", ".mkv"}),
            ("global_ref", reference_1, {".png", ".jpg", ".jpeg", ".webp"}),
            ("global_ref2", reference_2, {".png", ".jpg", ".jpeg", ".webp"}),
        ):
            if key == "global_ref2" and value is None:
                continue
            path = Path(value)
            _require(path.is_file() and not path.is_symlink())
            _require(path.suffix.lower() in suffixes and path.stat().st_size > 0)
            # Snapshot once: hash, upload and retry identity refer to same bytes.
            files[key] = (path.read_bytes(), path.suffix.lower())
        canonical = json.dumps(workflow, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(canonical.encode())
        for key, (data, suffix) in files.items():
            fingerprint.update(key.encode() + suffix.encode() + hashlib.sha256(data).digest())
        return plan, files, fingerprint.hexdigest()
    except (KeyError, TypeError, ValueError, OSError):
        raise ValueError("Invalid SDK input files or unsupported BFS plan") from None


def bind_graph(
    client: Comfy,
    workflow: WorkflowGraph,
    plan: PlannerData,
    files: AssetFiles,
) -> Workflow:
    graph = copy.deepcopy(workflow)
    # Strip old local filenames even from the serialized bridge template.
    plan = dict(plan, video="", global_ref="", global_ref2="")
    if "global_refs" in plan:
        plan["global_refs"] = []
    inputs: dict[str, Any] = {"plan": json.dumps(plan, separators=(",", ":"))}
    for key, (data, suffix) in files.items():
        name = hashlib.sha256(data).hexdigest() + suffix
        asset = client.assets.from_bytes(data, filename=name)
        # Finish uploads before entering the ambiguous submit window.
        inputs[key] = asset.as_reference()
    graph[BRIDGE_ID] = {"class_type": BRIDGE_TYPE, "inputs": inputs}
    graph["1189"]["inputs"]["plan"] = [BRIDGE_ID, 0]
    return client.workflows.from_json(graph)
