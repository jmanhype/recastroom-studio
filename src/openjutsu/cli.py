# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import uuid

from openjutsu import __version__
from openjutsu.comfy_legacy import ComfyLegacyRunner
from openjutsu.config import load_settings
from openjutsu.pipeline import prepare_workflow
from openjutsu.scene import analyze_scene


def command_inspect(args: argparse.Namespace) -> int:
    report = analyze_scene(args.source, args.ffprobe)
    print(report.to_json(), end="")
    return 0 if report.recommended else 2


def command_words(args: argparse.Namespace) -> int:
    command = [
        args.whisper,
        str(args.source),
        "--model",
        args.model,
        "--task",
        "transcribe",
        "--word_timestamps",
        "True",
        "--output_format",
        "json",
        "--output_dir",
        str(args.output_dir),
        "--verbose",
        "False",
    ]
    subprocess.run(command, check=True)
    stem = Path(args.source).stem
    generated = args.output_dir / f"{stem}.json"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        generated.replace(args.json)
        generated = args.json
    payload = json.loads(generated.read_text(encoding="utf-8"))
    print(json.dumps(payload, indent=2))
    return 0


def command_prepare(args: argparse.Namespace) -> int:
    settings = load_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    job_id = args.job_id or uuid.uuid4().hex[:12]
    job, workflow = prepare_workflow(
        settings,
        job_id=job_id,
        source=args.source,
        reference_1=args.reference_1,
        reference_2=args.reference_2,
        words_path=args.words,
        rights_attested=args.attest_rights,
        identity_description=args.identity,
        seed=args.seed,
    )
    output = Path(args.output) if args.output else Path(job.workflow_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    print(output)
    print(job.to_json(), end="")
    return 0


def command_run(args: argparse.Namespace) -> int:
    settings = load_settings()
    workflow = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    runner = ComfyLegacyRunner(settings.comfy_url)
    stats = runner.system_stats()
    print("COMFY_READY", json.dumps(stats, sort_keys=True))
    result = runner.run(workflow)
    print("PROMPT_ID", result.prompt_id)
    print(json.dumps(result.outputs, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RecastRoom Studio CLI")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="probe and preflight a source clip")
    inspect.add_argument("source", type=Path)
    inspect.add_argument("--ffprobe", default="ffprobe")
    inspect.set_defaults(handler=command_inspect)

    words = subparsers.add_parser("words", help="transcribe word timings with local Whisper")
    words.add_argument("source", type=Path)
    words.add_argument("--model", default="base.en")
    words.add_argument("--whisper", default="whisper")
    words.add_argument("--output-dir", type=Path, default=Path("work/words"))
    words.add_argument("--json", type=Path)
    words.set_defaults(handler=command_words)

    prepare = subparsers.add_parser("prepare", help="build a parameterized H3 workflow")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--reference-1", type=Path, required=True)
    prepare.add_argument("--reference-2", type=Path)
    prepare.add_argument("--words", type=Path)
    prepare.add_argument("--identity")
    prepare.add_argument("--seed", type=int, default=49)
    prepare.add_argument(
        "--attest-rights",
        action="store_true",
        required=True,
        help="confirm you own or have permission to modify the source and every reference likeness",
    )
    prepare.add_argument("--job-id")
    prepare.add_argument("--output", type=Path)
    prepare.set_defaults(handler=command_prepare)

    run = subparsers.add_parser("run", help="queue an API workflow to local ComfyUI")
    run.add_argument("workflow", type=Path)
    run.add_argument(
        "--attest-rights",
        action="store_true",
        required=True,
        help="confirm this workflow uses authorized source and reference media",
    )
    run.set_defaults(handler=command_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except KeyboardInterrupt:
        return 130
