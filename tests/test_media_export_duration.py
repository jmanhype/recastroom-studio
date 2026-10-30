# SPDX-License-Identifier: MIT
"""Real CPU regressions for legacy export duration boundaries."""
from array import array
from fractions import Fraction
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from openjutsu.media import make_side_by_side, restore_source_audio


AAC_FRAME_SECONDS = 1024 / 48000


@pytest.fixture(autouse=True)
def _require_ffmpeg_tools() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.fail("ffmpeg and ffprobe are required for local media regression tests")


def _make_media(
    destination: Path,
    *,
    frames: int,
    video_duration: float,
    audio_duration: float | None,
    color: str,
    frequency: int,
) -> None:
    video_only = destination.with_name(f"{destination.stem}-video-only{destination.suffix}")
    command = [
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
        f"color=c={color}:s=160x96:r=24:d={video_duration}",
    ]
    command.extend([
        "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", str(video_only),
    ])
    subprocess.run(command, check=True)
    if audio_duration is None:
        video_only.replace(destination)
        return
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(video_only), "-f", "lavfi", "-i",
        f"sine=frequency={frequency}:sample_rate=48000:d={audio_duration}",
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "320k", "-ar", "48000", str(destination),
    ], check=True)


def _probe(path: Path) -> dict[str, object]:
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=codec_type,duration,nb_read_frames,sample_aspect_ratio,width,height,"
        "time_base:frame=pts,duration:format=duration",
        "-of", "json", str(path),
    ], text=True)
    payload = json.loads(result)
    assert isinstance(payload, dict)
    return payload


def _video_measurements(path: Path) -> tuple[int, Fraction, dict[str, object], float]:
    payload = _probe(path)
    streams = payload["streams"]
    assert isinstance(streams, list) and len(streams) == 1
    stream = streams[0]
    assert isinstance(stream, dict) and stream["codec_type"] == "video"
    frames = payload["frames"]
    assert isinstance(frames, list)
    count = int(stream["nb_read_frames"])
    assert count == len(frames)
    ticks = Fraction(str(stream["time_base"]))
    durations = [int(frame["duration"]) for frame in frames]
    pts = [int(frame["pts"]) for frame in frames]
    assert len(set(durations)) == 1 and durations[0] > 0
    assert pts == [pts[0] + index * durations[0] for index in range(count)]
    return count, count * durations[0] * ticks, stream, float(payload["format"]["duration"])


def _audio_stream(path: Path) -> dict[str, object]:
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_streams", "-of", "json",
        str(path),
    ], text=True)
    payload = json.loads(result)
    streams = payload["streams"]
    assert isinstance(streams, list) and len(streams) == 1
    stream = streams[0]
    assert isinstance(stream, dict)
    return stream


def _decoded_audio(path: Path) -> array:
    result = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ar", "48000", "-f", "f32le", "-",
    ])
    samples = array("f")
    samples.frombytes(result)
    return samples


def _assert_audio_interval(path: Path, expected: Fraction) -> None:
    audio = _audio_stream(path)
    assert int(audio["sample_rate"]) == 48000
    assert abs(float(audio["duration"]) - float(expected)) <= AAC_FRAME_SECONDS
    samples = _decoded_audio(path)
    assert abs(len(samples) / 48000 - float(expected)) <= AAC_FRAME_SECONDS


def _assert_bounded_video(path: Path, expected_count: int, expected: Fraction) -> None:
    count, duration, stream, container = _video_measurements(path)
    assert count == expected_count
    assert duration == expected
    assert abs(float(stream["duration"]) - float(expected)) <= AAC_FRAME_SECONDS
    assert abs(container - float(expected)) <= AAC_FRAME_SECONDS
    assert stream["sample_aspect_ratio"] == "1:1"


@pytest.mark.parametrize(
    ("requested_frames", "expected_frames", "expected_duration"),
    [(None, 90, Fraction(15, 4)), (48, 48, Fraction(2)), (120, 90, Fraction(15, 4))],
)
def test_restore_bounds_to_decoded_generated_video_interval(
    tmp_path: Path,
    requested_frames: int | None,
    expected_frames: int,
    expected_duration: Fraction,
) -> None:
    generated = tmp_path / "generated-with-inflated-container.mp4"
    source = tmp_path / "long-source.mp4"
    destination = tmp_path / "final.mp4"
    _make_media(
        generated, frames=90, video_duration=10, audio_duration=10,
        color="green", frequency=880,
    )
    _make_media(
        source, frames=240, video_duration=10, audio_duration=10,
        color="blue", frequency=440,
    )
    inflated_count, inflated_duration, _stream, inflated_container = _video_measurements(generated)
    assert (inflated_count, inflated_duration, inflated_container) == (90, Fraction(15, 4), 10.0)

    restore_source_audio(generated, source, destination, frame_count=requested_frames)

    _assert_bounded_video(destination, expected_frames, expected_duration)
    _assert_audio_interval(destination, expected_duration)


def test_restore_pads_short_audio_without_losing_generated_frames(tmp_path: Path) -> None:
    generated = tmp_path / "generated.mp4"
    source = tmp_path / "short-audio-source.mp4"
    destination = tmp_path / "final.mp4"
    _make_media(generated, frames=90, video_duration=3.75, audio_duration=None, color="green", frequency=880)
    _make_media(source, frames=240, video_duration=10, audio_duration=1, color="blue", frequency=440)

    restore_source_audio(generated, source, destination)

    _assert_bounded_video(destination, 90, Fraction(15, 4))
    _assert_audio_interval(destination, Fraction(15, 4))
    samples = _decoded_audio(destination)
    assert max(abs(sample) for sample in samples[48100:]) <= 1e-3


def test_restore_fails_explicitly_when_source_has_no_audio(tmp_path: Path) -> None:
    generated = tmp_path / "generated.mp4"
    source = tmp_path / "silent-source.mp4"
    destination = tmp_path / "final.mp4"
    _make_media(generated, frames=90, video_duration=3.75, audio_duration=None, color="green", frequency=880)
    _make_media(source, frames=240, video_duration=10, audio_duration=None, color="blue", frequency=440)

    with pytest.raises(subprocess.CalledProcessError):
        restore_source_audio(generated, source, destination)
    assert not destination.exists() or destination.stat().st_size == 0


def _rgb_frame(path: Path, width: int, height: int) -> bytes:
    result = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    assert len(result) == width * height * 3
    return result


def test_comparison_is_bounded_to_final_interval_and_preserves_layout_audio(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "generated-with-inflated-container.mp4"
    source = tmp_path / "long-source.mp4"
    final = tmp_path / "final.mp4"
    comparison = tmp_path / "comparison.mp4"
    _make_media(
        generated, frames=90, video_duration=10, audio_duration=10,
        color="green", frequency=880,
    )
    _make_media(
        source, frames=240, video_duration=10, audio_duration=10,
        color="red", frequency=440,
    )
    restore_source_audio(generated, source, final)

    make_side_by_side(source, final, comparison)

    count, duration, stream, container = _video_measurements(comparison)
    assert (count, duration) == (90, Fraction(15, 4))
    assert (stream["width"], stream["height"], stream["sample_aspect_ratio"]) == (1920, 384, "1:1")
    assert abs(container - 3.75) <= AAC_FRAME_SECONDS
    _assert_audio_interval(comparison, Fraction(15, 4))
    assert max(abs(sample) for sample in _decoded_audio(comparison)[:48000]) > 1e-2
    frame = _rgb_frame(comparison, 1920, 384)

    def pixel(x: int, y: int = 192) -> tuple[int, int, int]:
        offset = (y * 1920 + x) * 3
        return frame[offset], frame[offset + 1], frame[offset + 2]

    assert pixel(5) == (0, 0, 0)
    assert max(abs(channel - expected) for channel, expected in zip(pixel(480), (255, 0, 0))) <= 16
    assert pixel(955) == (0, 0, 0)
    assert pixel(965) == (0, 0, 0)
    assert max(abs(channel - expected) for channel, expected in zip(pixel(1440), (0, 128, 0))) <= 16
    assert pixel(1915) == (0, 0, 0)


def test_comparison_rejects_source_video_shorter_than_final(tmp_path: Path) -> None:
    generated = tmp_path / "generated.mp4"
    source = tmp_path / "short-source.mp4"
    final = tmp_path / "final.mp4"
    comparison = tmp_path / "comparison.mp4"
    _make_media(generated, frames=90, video_duration=3.75, audio_duration=None, color="green", frequency=880)
    _make_media(source, frames=48, video_duration=10, audio_duration=10, color="red", frequency=440)
    restore_source_audio(generated, source, final)

    with pytest.raises(ValueError, match="source video is shorter than final video"):
        make_side_by_side(source, final, comparison)
    assert not comparison.exists()
