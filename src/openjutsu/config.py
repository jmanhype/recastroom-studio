# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    comfy_url: str
    backend: str
    workflow: Path
    data_dir: Path
    ffmpeg: str
    ffprobe: str
    whisper: str
    comfy_api_key: str | None = None
    comfy_base_url: str | None = None


SUPPORTED_BACKENDS = frozenset({"legacy", "sdk", "dry_run"})


def setting(source: dict[str, str], name: str, default: str | None = None) -> str | None:
    """Read the public RecastRoom setting, then the legacy Openjutsu value."""
    public = f"RECASTROOM_{name}"
    legacy = f"OPENJUTSU_{name}"
    if public in source:
        return source[public]
    if legacy in source:
        return source[legacy]
    return default


def load_settings(env: dict[str, str] | None = None) -> Settings:
    source = env or os.environ
    package_root = Path(__file__).resolve().parents[2]
    default_workflow = Path("workflows/recastroom_h3_workflow.json")
    # Editable checkouts and documented clean-checkout runs start from the
    # repository root. A normal wheel install cannot carry that root in
    # __file__, so prefer the checkout in the current directory when present.
    root = Path.cwd() if default_workflow.is_file() else package_root
    configured_workflow = setting(source, "WORKFLOW")
    workflow = (
        Path(configured_workflow)
        if configured_workflow
        else root / default_workflow
    )
    if not workflow.is_absolute():
        workflow = Path.cwd() / workflow
    configured_data_dir = setting(source, "DATA_DIR")
    data_dir = Path(configured_data_dir) if configured_data_dir else root / "work"
    if not data_dir.is_absolute():
        data_dir = Path.cwd() / data_dir
    backend = setting(source, "BACKEND", "legacy")
    if backend not in SUPPORTED_BACKENDS:
        supported = ", ".join(sorted(SUPPORTED_BACKENDS))
        raise ValueError(
            f"RECASTROOM_BACKEND (or legacy OPENJUTSU_BACKEND) must be one of: {supported}"
        )

    return Settings(
        comfy_url=setting(source, "COMFY_URL", "http://127.0.0.1:8188").rstrip("/"),
        backend=backend,
        workflow=workflow,
        data_dir=data_dir,
        ffmpeg=setting(source, "FFMPEG", "ffmpeg"),
        ffprobe=setting(source, "FFPROBE", "ffprobe"),
        whisper=setting(source, "WHISPER", "whisper"),
        comfy_api_key=(
            source.get("COMFY_API_KEY")
            or setting(source, "COMFY_API_KEY")
        ),
        comfy_base_url=source.get("COMFY_BASE_URL"),
    )
