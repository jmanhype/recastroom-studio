# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

from .config import Settings
from .m1_types import WindowMap
from .profiles import RecastProfile
from .timing import WordInterval, format_word_schedule, load_whisper_words
from .workflow import configure_workflow, load_workflow


@dataclass
class PreparedJob:
    job_id: str
    source: str
    reference_1: str
    reference_2: str | None
    rights_attested: bool
    word_schedule_path: str | None
    workflow_path: str
    prompt_path: str
    seed: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2) + "\n"


@dataclass(frozen=True)
class ManagedWorkflowPreparation:
    """Effective managed inputs plus the concrete prepared artifacts."""

    job: PreparedJob
    workflow: dict[str, Any]
    effective_workflow: dict[str, Any]
    prompt: str
    word_schedule: str
    effective_words: tuple[WordInterval, ...]
    effective_workflow_path: Path
    effective_workflow_sha256: str


def _managed_words(
    words: list[WordInterval], window: WindowMap, fps: Fraction
) -> tuple[WordInterval, ...]:
    start = Fraction(window.source_range.start) / fps
    end = Fraction(window.source_range.end) / fps
    clipped: list[WordInterval] = []
    for item in words:
        if item.end <= start or item.start >= end:
            continue
        clipped_start = max(item.start, float(start)) - float(start)
        clipped_end = min(item.end, float(end)) - float(start)
        # Exclude collapsed float intersections, but preserve legacy NaN failures.
        if clipped_end <= clipped_start:
            continue
        clipped.append(WordInterval(clipped_start, clipped_end, item.word))
    return tuple(clipped)


def _apply_managed_window(
    workflow: dict[str, Any], window: WindowMap, fps: Fraction, *, with_audio: bool
) -> dict[str, Any]:
    planner = workflow["1189"]
    plan = json.loads(planner["inputs"]["plan"])
    render_frames = window.render_range.end - window.render_range.start
    plan["fps"] = int(fps) if fps.denominator == 1 else float(fps)
    plan["start_f"] = window.render_range.start
    plan["end_f"] = window.render_range.end
    plan["start_s"] = float(Fraction(window.render_range.start) / fps)
    plan["end_s"] = float(Fraction(window.render_range.end) / fps)
    plan["min_s"] = float(Fraction(render_frames) / fps)
    plan["max_s"] = plan["min_s"]
    plan["segs"][0]["chain_history"] = window.expected_decoder_frames
    planner["inputs"]["plan"] = json.dumps(plan, separators=(",", ":"))
    workflow["1177"]["inputs"]["with_audio"] = with_audio
    workflow["200"]["inputs"]["start_frame"] = window.pad_left
    workflow["201"]["inputs"]["legacy_start_frame"] = window.pad_left
    return workflow


def _effective_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    effective = json.loads(json.dumps(workflow, sort_keys=True, separators=(",", ":")))
    planner = effective["1189"]
    plan = json.loads(planner["inputs"]["plan"])
    plan["video"] = "<source>"
    plan["global_ref"] = "<reference:1>"
    plan["global_ref2"] = "<reference:2>"
    planner["inputs"]["plan"] = json.dumps(plan, separators=(",", ":"))
    effective["751"]["inputs"]["filename_prefix"] = "<managed-output>"
    effective["1110"]["inputs"]["filename_prefix"] = "<managed-output-compare>"
    return effective


def prepare_managed_workflow(
    settings: Settings,
    *,
    job_id: str,
    source: str | Path,
    reference_1: str | Path,
    reference_2: str | Path | None,
    words_path: str | Path | None,
    rights_attested: bool,
    window: WindowMap,
    source_has_audio: bool,
    with_audio: bool,
    identity_description: str | None = None,
    seed: int,
    workflow_template: dict[str, Any],
) -> ManagedWorkflowPreparation:
    """Prepare an explicitly qualified managed window without legacy defaults."""
    if not rights_attested:
        raise ValueError("permission declaration is required")
    if not isinstance(window, WindowMap):
        raise ValueError("managed preparation requires a typed qualified WindowMap")
    if not isinstance(workflow_template, dict):
        raise ValueError("managed preparation requires a pinned workflow object")
    if with_audio and not source_has_audio:
        raise ValueError("with_audio=True is incompatible with a source that has no audio")
    frame_period = Fraction(window.source_timebase.num, window.source_timebase.den)
    if frame_period <= 0:
        raise ValueError("qualified source frame period must be positive")
    fps = Fraction(1, 1) / frame_period
    if window.source_timebase != window.render_timebase:
        raise ValueError("source/render timebase conversion is not qualified")

    job_dir = settings.data_dir / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    words = load_whisper_words(words_path) if words_path else []
    effective_words = _managed_words(words, window, fps)
    schedule = format_word_schedule(list(effective_words), fps=float(fps))
    profile = RecastProfile(
        identity_description=identity_description or RecastProfile().identity_description
    )
    prompt = profile.render_prompt(schedule)
    source_name = Path(source).name
    ref1_name = Path(reference_1).name
    ref2_name = Path(reference_2).name if reference_2 else None
    workflow = _apply_managed_window(
        configure_workflow(
            workflow_template,
            video_name=source_name,
            reference_1=ref1_name,
            reference_2=ref2_name,
            prompt=prompt,
            seed=seed,
            output_prefix=f"openjutsu/{job_id}",
            with_audio=with_audio,
        ),
        window,
        fps,
        with_audio=with_audio,
    )
    effective = _effective_workflow(workflow)
    effective_artifact = json.dumps(
        effective, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ) + "\n"
    effective_path = job_dir / "effective-workflow.json"
    effective_path.write_text(effective_artifact, encoding="utf-8")
    workflow_path = job_dir / "workflow.json"
    prompt_path = job_dir / "prompt.txt"
    manifest_path = job_dir / "job.json"
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    job = PreparedJob(
        job_id=job_id,
        source=str(source),
        reference_1=str(reference_1),
        reference_2=str(reference_2) if reference_2 else None,
        rights_attested=True,
        word_schedule_path=str(words_path) if words_path else None,
        workflow_path=str(workflow_path),
        prompt_path=str(prompt_path),
        seed=seed,
    )
    manifest_path.write_text(job.to_json(), encoding="utf-8")
    return ManagedWorkflowPreparation(
        job, workflow, effective, prompt, schedule, effective_words, effective_path,
        hashlib.sha256(effective_artifact.encode("utf-8")).hexdigest(),
    )


def prepare_workflow(
    settings: Settings,
    *,
    job_id: str,
    source: str | Path,
    reference_1: str | Path,
    reference_2: str | Path | None,
    words_path: str | Path | None,
    rights_attested: bool,
    identity_description: str | None = None,
    seed: int = 49,
    workflow_template: str | Path | None = None,
) -> tuple[PreparedJob, dict[str, Any]]:
    if not rights_attested:
        raise ValueError("permission declaration is required")
    job_dir = settings.data_dir / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    template = load_workflow(workflow_template or settings.workflow)
    words = load_whisper_words(words_path) if words_path else []
    schedule = format_word_schedule(words)
    profile = RecastProfile(identity_description=identity_description or RecastProfile().identity_description)
    prompt = profile.render_prompt(schedule)

    source_name = Path(source).name
    ref1_name = Path(reference_1).name
    ref2_name = Path(reference_2).name if reference_2 else None
    workflow = configure_workflow(
        template,
        video_name=source_name,
        reference_1=ref1_name,
        reference_2=ref2_name,
        prompt=prompt,
        seed=seed,
        output_prefix=f"openjutsu/{job_id}",
        with_audio=True,
    )
    workflow_path = job_dir / "workflow.json"
    prompt_path = job_dir / "prompt.txt"
    manifest_path = job_dir / "job.json"
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    job = PreparedJob(
        job_id=job_id,
        source=str(source),
        reference_1=str(reference_1),
        reference_2=str(reference_2) if reference_2 else None,
        rights_attested=True,
        word_schedule_path=str(words_path) if words_path else None,
        workflow_path=str(workflow_path),
        prompt_path=str(prompt_path),
        seed=seed,
    )
    manifest_path.write_text(job.to_json(), encoding="utf-8")
    return job, workflow
