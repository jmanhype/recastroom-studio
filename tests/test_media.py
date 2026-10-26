# SPDX-License-Identifier: MIT
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Literal

import pytest

from openjutsu.media import make_side_by_side, strip_container_metadata


@pytest.fixture(autouse=True)
def _require_ffmpeg_tools() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.fail("ffmpeg and ffprobe are required for local media regression tests")


def test_strip_container_metadata_removes_tags_and_preserves_streams(tmp_path: Path) -> None:
    source = Path("docs/evidence/slate/keepers/seed50_jay_plate_a/seed50_jay_plate_a_compare_480p.mp4")
    destination = tmp_path / "clean.mp4"

    strip_container_metadata(source, destination)

    probe = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(destination)],
            text=True,
        )
    )
    assert [stream["codec_name"] for stream in probe["streams"]] == ["h264", "aac"]
    tags = dict(probe["format"].get("tags", {}))
    for stream in probe["streams"]:
        tags.update(stream.get("tags", {}))
    assert not {"prompt", "comment", "title"} & set(tags)


VideoColor = Literal["red", "green"]


def _make_solid_video(
    destination: Path,
    *,
    size: tuple[int, int],
    color: VideoColor,
    frequency: int,
    sample_aspect_ratio: str | None = None,
) -> None:
    width, height = size
    command = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color}:s={width}x{height}:r=24",
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
    if sample_aspect_ratio is not None:
        command.extend(["-vf", f"setsar={sample_aspect_ratio.replace(':', '/')}"])
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
            str(destination),
        ]
    )
    subprocess.run(command, check=True)


def _video_stream(path: Path) -> dict[str, object]:
    probe = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json", str(path)],
            text=True,
        )
    )
    streams = probe["streams"]
    assert isinstance(streams, list)
    assert len(streams) == 1
    stream = streams[0]
    assert isinstance(stream, dict)
    return stream


def _assert_geometry(path: Path, width: int, height: int) -> None:
    stream = _video_stream(path)
    assert stream["width"] == width
    assert stream["height"] == height
    assert stream["sample_aspect_ratio"] == "1:1"
    dar = Fraction(str(stream["display_aspect_ratio"]).replace(":", "/"))
    assert dar == Fraction(width, height)


def _decoded_rgb_frame(path: Path, width: int, height: int) -> bytes:
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
    assert len(frame) == width * height * 3
    return frame


def _assert_color(actual: tuple[int, int, int], expected: tuple[int, int, int]) -> None:
    assert max(abs(actual[channel] - expected[channel]) for channel in range(3)) <= 16


def _assert_centered_tile(
    frame: bytes,
    *,
    tile_index: int,
    content_width: int,
    color: VideoColor,
) -> None:
    tile_width = 960
    tile_height = 384
    y = tile_height // 2
    expected_rgb = (255, 0, 0) if color == "red" else (0, 128, 0)

    def pixel(tile_x: int) -> tuple[int, int, int]:
        x = tile_index * tile_width + tile_x
        offset = (y * 1920 + x) * 3
        return frame[offset], frame[offset + 1], frame[offset + 2]

    _assert_color(pixel(5), (0, 0, 0))
    _assert_color(pixel(tile_width // 2), expected_rgb)
    _assert_color(pixel(tile_width - 6), (0, 0, 0))

    left_pad = (tile_width - content_width) // 2
    _assert_color(pixel(left_pad + 8), expected_rgb)
    _assert_color(pixel(tile_width - left_pad - 9), expected_rgb)
    _assert_color(pixel(left_pad - 8), (0, 0, 0))
    _assert_color(pixel(tile_width - left_pad + 7), (0, 0, 0))


@pytest.mark.parametrize(
    ("source_size", "final_size", "source_content_width", "final_content_width"),
    [
        ((576, 384), (576, 384), 576, 576),
        ((216, 384), (216, 384), 216, 216),
        ((640, 360), (640, 360), 682, 682),
        ((576, 384), (216, 384), 576, 216),
    ],
)
def test_make_side_by_side_scale_fits_and_pads_without_stretching(
    tmp_path: Path,
    source_size: tuple[int, int],
    final_size: tuple[int, int],
    source_content_width: int,
    final_content_width: int,
) -> None:
    source = tmp_path / "source.mp4"
    final = tmp_path / "final.mp4"
    destination = tmp_path / "paired.mp4"

    _make_solid_video(source, size=source_size, color="red", frequency=440)
    _make_solid_video(final, size=final_size, color="green", frequency=660)
    _assert_geometry(source, *source_size)
    _assert_geometry(final, *final_size)

    make_side_by_side(source, final, destination)

    _assert_geometry(destination, 1920, 384)
    frame = _decoded_rgb_frame(destination, 1920, 384)
    _assert_centered_tile(frame, tile_index=0, content_width=source_content_width, color="red")
    _assert_centered_tile(frame, tile_index=1, content_width=final_content_width, color="green")


def test_make_side_by_side_preserves_display_aspect_for_non_square_sar_input(
    tmp_path: Path,
) -> None:
    source = tmp_path / "non-square-sar.mp4"
    final = tmp_path / "square-sar.mp4"
    destination = tmp_path / "paired.mp4"

    _make_solid_video(
        source,
        size=(288, 384),
        color="red",
        frequency=440,
        sample_aspect_ratio="2:1",
    )
    _make_solid_video(final, size=(576, 384), color="green", frequency=660)
    source_stream = _video_stream(source)
    assert (source_stream["width"], source_stream["height"]) == (288, 384)
    assert source_stream["sample_aspect_ratio"] == "2:1"
    assert source_stream["display_aspect_ratio"] == "3:2"
    _assert_geometry(final, 576, 384)

    make_side_by_side(source, final, destination)

    _assert_geometry(destination, 1920, 384)
    frame = _decoded_rgb_frame(destination, 1920, 384)
    _assert_centered_tile(frame, tile_index=0, content_width=576, color="red")
    _assert_centered_tile(frame, tile_index=1, content_width=576, color="green")


def test_make_side_by_side_rejects_odd_tile_dimensions(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="width and height must be even"):
        make_side_by_side(
            tmp_path / "source.mp4",
            tmp_path / "final.mp4",
            tmp_path / "paired.mp4",
            width=959,
            height=383,
        )
