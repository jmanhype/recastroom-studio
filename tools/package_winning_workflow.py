#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_PROMPT = """{{IDENTITY}}

Use the supplied word/frame schedule and source audio. Match the source performance frame by frame."""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    workflow = json.loads(args.source.read_text(encoding="utf-8"))
    plan = json.loads(workflow["1189"]["inputs"]["plan"])
    plan["video"] = "source.mp4"
    plan["global_ref"] = "reference_1.png"
    plan["global_ref2"] = "reference_2.png"
    plan["audio_mode"] = "auto"
    workflow["1189"]["inputs"]["plan"] = json.dumps(plan, separators=(",", ":"))
    workflow["1152"]["inputs"]["value"] = DEFAULT_PROMPT
    workflow["1177"]["inputs"]["with_audio"] = True
    workflow["1177"]["inputs"]["source_blur"] = "off"
    workflow["13"]["inputs"]["noise_seed"] = 49
    workflow["181"]["inputs"]["steps"] = 8
    workflow["586"]["inputs"]["strength_model"] = 1.0
    workflow["1192"]["inputs"]["strength_model"] = 0.35
    workflow["751"]["inputs"]["filename_prefix"] = "openjutsu/result"
    workflow["1110"]["inputs"]["filename_prefix"] = "openjutsu/result_compare"
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    print(args.destination)


if __name__ == "__main__":
    main()
