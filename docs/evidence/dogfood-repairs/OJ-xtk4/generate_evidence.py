# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from openjutsu.media import make_side_by_side


EVIDENCE = Path(__file__).resolve().parent


def make_input(path: Path, size: tuple[int, int], color: str, frequency: int, sar: str | None = None) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color}:s={size[0]}x{size[1]}:r=24",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={frequency}:sample_rate=48000",
        "-t",
        "0.25",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
    ]
    if sar is not None:
        command.extend(["-vf", f"setsar={sar.replace(':', '/')}"])
    command.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            str(path),
        ]
    )
    subprocess.run(command, check=True)


def probe(path: Path) -> dict[str, Any]:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,sample_aspect_ratio,display_aspect_ratio",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    stream = json.loads(output)["streams"][0]
    return {key: stream.get(key) for key in ("width", "height", "sample_aspect_ratio", "display_aspect_ratio")}


def decoded_center_row(path: Path) -> list[tuple[int, int, int]]:
    frame = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ]
    )
    row_offset = 192 * 1920 * 3
    return [tuple(frame[row_offset + x * 3 : row_offset + (x + 1) * 3]) for x in range(1920)]


def close(actual: tuple[int, int, int], expected: tuple[int, int, int]) -> bool:
    return max(abs(actual[channel] - expected[channel]) for channel in range(3)) <= 16


def tile_measurement(row: list[tuple[int, int, int]], tile_index: int, color: str) -> dict[str, Any]:
    expected = (255, 0, 0) if color == "red" else (0, 128, 0)
    center = tile_index * 960 + 480
    left = center
    right = center
    while left > tile_index * 960 and close(row[left - 1], expected):
        left -= 1
    while right < (tile_index + 1) * 960 - 1 and close(row[right + 1], expected):
        right += 1
    return {
        "tile": [960, 384],
        "color": color,
        "center_rgb": list(row[center]),
        "left_padding_px": left - tile_index * 960,
        "right_padding_px": (tile_index + 1) * 960 - right - 1,
        "decoded_content_width_px": right - left + 1,
        "edge_samples": {
            "tile_x_5_rgb": list(row[tile_index * 960 + 5]),
            "tile_x_955_rgb": list(row[tile_index * 960 + 955]),
        },
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    cases = [
        ("3-2", (576, 384), None, (576, 384), None, [576, 576]),
        ("9-16-portrait", (216, 384), None, (216, 384), None, [216, 216]),
        ("16-9", (640, 360), None, (640, 360), None, [682, 682]),
        ("mixed-3-2-9-16", (576, 384), None, (216, 384), None, [576, 216]),
        ("non-square-sar-3-2-dar", (288, 384), "2:1", (576, 384), None, [576, 576]),
    ]
    measurements: dict[str, Any] = {"common_tile": [960, 384], "cases": {}}
    hashes: dict[str, str] = {}

    for name, source_size, source_sar, final_size, final_sar, expected_widths in cases:
        source = EVIDENCE / f"{name}-source.mp4"
        final = EVIDENCE / f"{name}-final.mp4"
        destination = EVIDENCE / f"{name}-paired.mp4"
        make_input(source, source_size, "red", 440, source_sar)
        make_input(final, final_size, "green", 660, final_sar)
        make_side_by_side(source, final, destination)

        row = decoded_center_row(destination)
        measurements["cases"][name] = {
            "source_input": probe(source),
            "final_input": probe(final),
            "paired_output": probe(destination),
            "expected_content_width_px": expected_widths,
            "source_tile": tile_measurement(row, 0, "red"),
            "final_tile": tile_measurement(row, 1, "green"),
        }
        hashes[destination.name] = sha256(destination)
        source.unlink()
        final.unlink()

    (EVIDENCE / "measurements.json").write_text(json.dumps(measurements, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE / "SHA256SUMS.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
