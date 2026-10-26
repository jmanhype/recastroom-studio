# SPDX-License-Identifier: MIT
"""v2's resolved filename widgets -> pinned BFSShotPlanner JSON STRING.

Install this directory in ComfyUI/custom_nodes in the deployment build.
Never fetch URLs or interpret asset IDs here: the v2 server must materialize
core/ASSET inputs before execution. Unresolved/missing inputs fail closed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TypeAlias

WidgetSpec: TypeAlias = tuple[str, dict[str, bool | str]]
InputSchema: TypeAlias = dict[str, dict[str, WidgetSpec]]


class OpenJutsuAssetPlan:
    @classmethod
    def INPUT_TYPES(cls: type[OpenJutsuAssetPlan]) -> InputSchema:
        return {"required": {"plan": ("STRING", {"multiline": True}),
                             "video": ("STRING", {}), "global_ref": ("STRING", {})},
                "optional": {"global_ref2": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("STRING",)
    FUNCTION = "bind"
    CATEGORY = "OpenJutsu"

    def bind(
        self: OpenJutsuAssetPlan,
        plan: str,
        video: str,
        global_ref: str,
        global_ref2: str = "",
    ) -> tuple[str]:
        import folder_paths

        def materialized(name):
            if not isinstance(name, str) or not name or "\\" in name or ":" in name:
                raise ValueError("Asset is not a materialized input filename")
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Asset filename is outside input directory")
            root = Path(folder_paths.get_input_directory()).resolve()
            path = Path(folder_paths.get_annotated_filepath(name)).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError("Asset was not materialized inside input directory")
            # Canonical relative name follows BFS _input_path exactly.
            return path.relative_to(root).as_posix()

        parsed = json.loads(plan)
        if not isinstance(parsed, dict):
            raise ValueError("Invalid BFS plan")
        parsed["video"] = materialized(video)
        parsed["global_ref"] = materialized(global_ref)
        parsed["global_ref2"] = materialized(global_ref2) if global_ref2 else ""
        if "global_refs" in parsed:
            parsed["global_refs"] = [parsed["global_ref"]]
            if parsed["global_ref2"]:
                parsed["global_refs"].append(parsed["global_ref2"])
        return (json.dumps(parsed, separators=(",", ":")),)


NODE_CLASS_MAPPINGS = {"OpenJutsuAssetPlan": OpenJutsuAssetPlan}
