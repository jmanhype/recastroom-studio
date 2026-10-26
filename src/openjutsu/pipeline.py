# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .config import Settings
from .profiles import RecastProfile
from .timing import format_word_schedule, load_whisper_words
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
        raise ValueError("operator attestation is required")
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
