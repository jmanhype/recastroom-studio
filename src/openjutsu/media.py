# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path
import subprocess


def run_ffmpeg(args: list[str], ffmpeg: str = "ffmpeg") -> None:
    subprocess.run([ffmpeg, *args], check=True)


def make_contact_sheet(video: str | Path, destination: str | Path, ffmpeg: str = "ffmpeg") -> None:
    run_ffmpeg(
        [
            "-y",
            "-v",
            "error",
            "-i",
            str(video),
            "-vf",
            "fps=2,scale=480:-2,tile=6x5",
            "-frames:v",
            "1",
            str(destination),
        ],
        ffmpeg,
    )


def strip_container_metadata(
    source: str | Path,
    destination: str | Path,
    *,
    ffmpeg: str = "ffmpeg",
) -> None:
    """Remux media without container tags while preserving encoded streams."""
    run_ffmpeg(
        [
            "-y",
            "-v",
            "error",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-map_metadata",
            "-1",
            "-map_chapters",
            "-1",
            "-c",
            "copy",
            "-fflags",
            "+bitexact",
            "-flags:v",
            "+bitexact",
            "-flags:a",
            "+bitexact",
            str(destination),
        ],
        ffmpeg,
    )


def normalize_to_24fps(
    source: str | Path,
    destination: str | Path,
    *,
    width: int = 960,
    height: int = 384,
    ffmpeg: str = "ffmpeg",
) -> None:
    run_ffmpeg(
        [
            "-y",
            "-v",
            "error",
            "-i",
            str(source),
            "-vf",
            f"fps=24,scale={width}:{height}:flags=area,setsar=1",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "16",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(destination),
        ],
        ffmpeg,
    )


def restore_source_audio(
    generated: str | Path,
    source: str | Path,
    destination: str | Path,
    *,
    ffmpeg: str = "ffmpeg",
    frame_count: int | None = None,
) -> None:
    args = [
        "-y",
        "-v",
        "error",
        "-i",
        str(generated),
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-vf",
        "setsar=1",
    ]
    if frame_count is not None:
        args.extend(["-frames:v", str(frame_count)])
    args.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "16",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )
    run_ffmpeg(args, ffmpeg)


def make_side_by_side(
    source: str | Path,
    final: str | Path,
    destination: str | Path,
    *,
    width: int = 960,
    height: int = 384,
    ffmpeg: str = "ffmpeg",
) -> None:
    """Compose two videos on centered, equal-sized tiles without stretching."""
    if width < 2 or height < 2 or width % 2 or height % 2:
        raise ValueError("width and height must be even integers of at least 2 pixels")

    fit_tile = (
        f"scale=trunc(min({width}\\,{height}*dar)/2)*2:"
        f"trunc(min({height}\\,{width}/dar)/2)*2,setsar=1,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    )
    run_ffmpeg(
        [
            "-y",
            "-v",
            "error",
            "-i",
            str(source),
            "-i",
            str(final),
            "-filter_complex",
            f"[0:v]{fit_tile}[a];[1:v]{fit_tile}[b];[a][b]hstack[v]",
            "-map",
            "[v]",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-movflags",
            "+faststart",
            str(destination),
        ],
        ffmpeg,
    )
