# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess


@dataclass
class SceneReport:
    path: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    has_audio: bool
    audio_channels: int
    risks: list[str]
    warnings: list[str]
    recommended: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2) + "\n"


def probe_video(path: str | Path, ffprobe: str = "ffprobe") -> dict:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _fps_from_rate(rate: str | None) -> float:
    if not rate or "/" not in rate:
        return float(rate or 0)
    numerator, denominator = rate.split("/", 1)
    denominator_value = float(denominator)
    return float(numerator) / denominator_value if denominator_value else 0.0


def analyze_scene(path: str | Path, ffprobe: str = "ffprobe") -> SceneReport:
    media_path = Path(path)
    if not media_path.is_file():
        raise FileNotFoundError(media_path)
    payload = probe_video(media_path, ffprobe)
    streams = payload.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if video is None:
        raise ValueError("source has no video stream")

    duration = float(payload.get("format", {}).get("duration") or video.get("duration") or 0)
    width, height = int(video.get("width", 0)), int(video.get("height", 0))
    fps = _fps_from_rate(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    audio_channels = int(audio.get("channels", 0)) if audio else 0
    risks: list[str] = []
    warnings: list[str] = []

    if duration < 2:
        risks.append("clip is shorter than 2 seconds; H3 has little performance context")
    if duration > 12:
        warnings.append("clip is longer than 12 seconds; split into single shots before recasting")
    if width < 640 or height < 240:
        risks.append("resolution is too low for reliable face and mouth conditioning")
    if fps < 15:
        risks.append("frame rate is too low for stable speech timing")
    if not audio or audio_channels == 0:
        risks.append("no audio stream; word-level lip conditioning cannot run")
    if abs(fps - 24.0) > 1.5:
        warnings.append(f"source is {fps:.3f} fps; normalize to 24 fps before generation")
    if duration > 5.875 and duration <= 12:
        warnings.append("clip will be padded or trimmed to the 17n+5 H3 grid; verify the exact frame window")

    # Human review remains mandatory. Automated probes do not detect hats, sunglasses,
    # profiles, occluded mouths, overlapping speakers, or crowded frames reliably.
    warnings.append("manual shot review required: eyes visible, mouth visible, one target speaker, stable camera")

    return SceneReport(
        path=str(media_path),
        duration_seconds=duration,
        width=width,
        height=height,
        fps=fps,
        has_audio=bool(audio),
        audio_channels=audio_channels,
        risks=risks,
        warnings=warnings,
        recommended=not risks,
    )
