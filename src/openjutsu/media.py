# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import subprocess
import struct
import tempfile
from typing import Any

from .m1_types import AudioPolicy, EditRevision, OutputEvidence, SceneRevision, Timebase
from .take_service import TakeService
from .workspace_store import ValidationError, WorkspaceStore


@dataclass(frozen=True)
class _MediaSlice:
    path: Path
    asset_id: str
    sha256: str
    kind: str
    start: int
    end: int


@dataclass(frozen=True)
class _ManagedPlan:
    scene: SceneRevision
    source_path: Path
    slices: tuple[_MediaSlice, ...]
    authority: tuple[dict[str, Any], ...]


def _run_tool(arguments: list[object], *, text: bool = False) -> subprocess.CompletedProcess[Any]:
    try:
        return subprocess.run(
            [str(item) for item in arguments], check=True, capture_output=True,
            text=text, timeout=30,
        )
    except subprocess.SubprocessError as error:
        raise ValidationError("managed FFmpeg assembly failed") from error


def _ffprobe(path: Path, entries: str) -> dict[str, Any]:
    result = _run_tool([
        "ffprobe", "-v", "error", "-count_frames", "-show_entries", entries,
        "-of", "json", str(path),
    ], text=True)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValidationError("managed FFmpeg metadata is malformed") from error
    if not isinstance(payload, dict):
        raise ValidationError("managed FFmpeg metadata is malformed")
    return payload


def _video_facts(path: Path) -> tuple[int, Timebase, int, Fraction, int, int]:
    count, timebase, first_pts, ticks = TakeService._probe(path)
    payload = _ffprobe(path, "stream=width,height")
    try:
        stream = payload["streams"][0]
        return count, timebase, first_pts, ticks, int(stream["width"]), int(stream["height"])
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise ValidationError("managed video geometry is malformed") from error


def _audio_facts(path: Path) -> tuple[int, int, str] | None:
    payload = _ffprobe(path, "stream=codec_type,codec_name,sample_rate,channels")
    stream = next(
        (item for item in payload.get("streams", []) if item.get("codec_type") == "audio"), None
    )
    if stream is None:
        return None
    try:
        return int(stream["sample_rate"]), int(stream["channels"]), str(stream["codec_name"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValidationError("managed audio timing is malformed") from error


def _frames(path: Path, start: int, end: int, width: int, height: int) -> bytes:
    result = _run_tool([
        "ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path),
        "-vf", f"trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS",
        "-map", "0:v:0",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1",
    ])
    expected = (end - start) * width * height * 3
    if len(result.stdout) != expected:
        raise ValidationError("decoded edit frame count or geometry mismatch")
    return result.stdout


def _pcm(path: Path, start: int, end: int, rate: int, channels: int) -> bytes:
    result = _run_tool([
        "ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-map", "0:a:0",
        "-vn", "-af", f"atrim=start_sample={start}:end_sample={end}", "-f", "s16le",
        "-acodec", "pcm_s16le", "pipe:1",
    ])
    expected = (end - start) * channels * 2
    if len(result.stdout) != expected:
        raise ValidationError("decoded edit audio sample count mismatch")
    return result.stdout


def _pcm_all(path: Path) -> bytes:
    result = _run_tool([
        "ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path),
        "-map", "0:a:0", "-vn", "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1",
    ])
    return result.stdout


def _sample_boundary(rate: int, timebase: Timebase, frame: int) -> int:
    numerator = rate * timebase.num * frame
    return (numerator + timebase.den // 2) // timebase.den


def _ffmpeg_version() -> str:
    result = _run_tool(["ffmpeg", "-version"], text=True)
    return result.stdout.splitlines()[0]


def _stage_output(
    store: WorkspaceStore, revision: EditRevision, path: Path, count: int, timebase: Timebase
) -> OutputEvidence:
    asset = store.stage_asset(
        revision.project_id, "managed-edit-export.mp4", io.BytesIO(path.read_bytes()),
        role="edit_export", protected=True,
    )
    return OutputEvidence(asset.asset_id, asset.sha256, count, timebase, None)


def _packet_profile(path: Path) -> dict[str, Any]:
    payload = _ffprobe(
        path, "packet=codec_type,pts,dts,duration,size,flags"
    )
    packets = payload.get("packets", [])
    if not isinstance(packets, list):
        raise ValidationError("managed packet metadata is malformed")
    normalized: list[tuple[object, ...]] = []
    for packet in packets:
        if not isinstance(packet, dict):
            raise ValidationError("managed packet metadata is malformed")
        normalized.append(tuple(packet.get(key) for key in (
            "codec_type", "pts", "dts", "duration", "size", "flags"
        )))
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return {
        "video_packets": sum(row[0] == "video" for row in normalized),
        "audio_packets": sum(row[0] == "audio" for row in normalized),
        "digest": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    }


def _audio_metrics(expected: bytes, actual: bytes, channels: int) -> dict[str, Any]:
    """Measure signed PCM alignment while bounding AAC priming, never bypassing it."""
    expected_samples = struct.unpack(f"<{len(expected) // 2}h", expected)
    decoded_samples = struct.unpack(f"<{len(actual) // 2}h", actual)
    sample_count = len(expected_samples)
    maximum_delay = 4096
    candidates: list[tuple[float, int, float, int]] = []
    for delay in range(
        0, min(maximum_delay, len(decoded_samples) - sample_count) + 1, channels
    ):
        differences = [abs(left - right) for left, right in zip(
            expected_samples, decoded_samples[delay:]
        )]
        candidates.append((
            sum(differences) / len(differences), max(differences),
            sum(value > 512 for value in differences) / len(differences), delay,
        ))
    if not candidates or len(decoded_samples) > sample_count + maximum_delay:
        raise ValidationError("decoded edit audio duration or priming is outside policy")
    mean, maximum, outliers, delay = min(candidates)
    if mean > 48 or maximum > 4096 or outliers > 0.01:
        raise ValidationError("decoded edit-map audio content mismatch")
    return {
        "expected_samples": sample_count // channels,
        "measured_samples": len(decoded_samples) // channels,
        "decoded_delay_samples": delay,
        "maximum_absolute_error": maximum,
        "mean_absolute_error": mean,
        "outlier_ratio": outliers,
    }


def _video_metrics(expected: bytes, actual: bytes) -> dict[str, Any]:
    if len(expected) != len(actual) or not expected:
        raise ValidationError("decoded edit video byte count mismatch")
    differences = [abs(left - right) for left, right in zip(expected, actual)]
    mean = sum(differences) / len(differences)
    outliers = sum(value > 32 for value in differences) / len(differences)
    if mean >= 5 or outliers >= 0.01:
        raise ValidationError("decoded edit video content mismatch")
    return {"mean_absolute_error": mean, "outlier_ratio": outliers}


def _stream_copy(
    store: WorkspaceStore, revision: EditRevision, plan: _ManagedPlan
) -> tuple[OutputEvidence, dict[str, Any]]:
    source = plan.scene.source
    facts = _video_facts(plan.source_path)
    if facts[:3] != (source.frame_count, source.timebase, 0):
        raise ValidationError("source stream copy timing is not exactly reset and full-range")
    formats = _ffprobe(plan.source_path, "stream=codec_type,codec_name:format=format_name")
    video_stream = next(
        (item for item in formats.get("streams", []) if item.get("codec_type") == "video"), None
    )
    if video_stream is None:
        raise ValidationError("source stream copy video metadata is malformed")
    codec = str(video_stream.get("codec_name", ""))
    mux = str(formats.get("format", {}).get("format_name", ""))
    if "h264" not in codec or "mp4" not in mux:
        raise ValidationError("source stream copy codec or mux format is incompatible")
    source_audio = _audio_facts(plan.source_path)
    if (source_audio is None and source.has_audio) or (
            source_audio is not None and not source.has_audio):
        raise ValidationError("measured source audio presence does not match the frozen source")
    (store.root / "managed").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="managed-export-", dir=store.root / "managed") as temporary:
        destination = Path(temporary) / "edit-export.mp4"
        arguments: list[object] = [
            "ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(plan.source_path),
        ]
        arguments.extend(["-map", "0:v:0"])
        if source_audio is not None:
            arguments.extend(["-map", "0:a:0"])
        arguments.extend(["-c", "copy", "-movflags", "+faststart", str(destination)])
        _run_tool(arguments)
        output_count, output_time, output_pts, *_ = _video_facts(destination)
        output_audio = _audio_facts(destination)
        video_content = _video_metrics(
            _frames(plan.source_path, 0, source.frame_count, facts[4], facts[5]),
            _frames(destination, 0, source.frame_count, facts[4], facts[5]),
        )
        source_packets = _packet_profile(plan.source_path)
        output_packets = _packet_profile(destination)
        audio_match = source_audio is None and output_audio is None
        if source_audio is not None:
            audio_match = (
                output_audio == source_audio
                and _pcm_all(plan.source_path) == _pcm_all(destination)
            )
        if (output_count, output_time, output_pts) != (
                source.frame_count, source.timebase, 0):
            raise ValidationError(
                "source stream copy decoded video content mismatch: "
                f"actual={(output_count, output_time.num, output_time.den, output_pts)} "
                f"expected={(source.frame_count, source.timebase.num, source.timebase.den, 0)} "
                f"video_metrics={video_content}"
            )
        if source_packets != output_packets or not audio_match:
            raise ValidationError(
                "source stream copy packet or decoded content mismatch: "
                f"source_packets={source_packets} output_packets={output_packets} "
                f"audio_match={audio_match}"
            )
        evidence = _stage_output(store, revision, destination, output_count, output_time)
        item = revision.items[0]
    checks = {
        "ffmpeg": {"version": _ffmpeg_version(), "options": {"mode": "stream_copy"}},
        "edit_map": {"items": [{
            "shot_id": item.shot_id, "take_id": None,
            "source_range": {"start": item.source_range.start, "end": item.source_range.end},
            "timeline_range": {"start": item.timeline_range.start, "end": item.timeline_range.end},
        }], "timebase": {"num": source.timebase.num, "den": source.timebase.den}},
        "audio": {"policy": "source_stream_copy", "source": source_audio, "output": output_audio},
        "measurements": {"source_pts": facts[2], "output_pts": output_pts,
                         "decoded_video_content": video_content,
                         "decoded_audio_match": audio_match},
        "stream_copy": {"codec": codec, "mux": mux, "source_packets": source_packets,
                         "output_packets": output_packets,
                         "packet_match": source_packets == output_packets},
        "integrity": {"source_sha256": source.sha256, "output_sha256": evidence.sha256},
    }
    return evidence, checks


def _edit_audio_setup(
    plan: _ManagedPlan, revision: EditRevision
) -> tuple[bytearray | None, tuple[int, int, str] | None]:
    if revision.audio is not AudioPolicy.SOURCE_EDIT_MAP:
        return None, None
    facts = _audio_facts(plan.source_path)
    if not plan.scene.source.has_audio:
        if facts is not None:
            raise ValidationError("frozen source declares no audio but audio is measurable")
        return None, None
    if facts is None:
        raise ValidationError("frozen source declares audio but none is measurable")
    return bytearray(), facts


def _assemble_plan(
    store: WorkspaceStore, revision: EditRevision, plan: _ManagedPlan
) -> tuple[OutputEvidence, dict[str, Any]]:
    if revision.audio is AudioPolicy.SOURCE_STREAM_COPY:
        return _stream_copy(store, revision, plan)
    source_facts = _video_facts(plan.source_path)
    if source_facts[:3] != (
            plan.scene.source.frame_count, revision.timebase, 0):
        raise ValidationError("measured source frame count, PTS, or timebase drifted")
    width, height = source_facts[4], source_facts[5]
    (store.root / "managed").mkdir(exist_ok=True)
    video = bytearray()
    item_checks: list[dict[str, Any]] = []
    decoded_counts: list[dict[str, int]] = []
    audio_intervals: list[dict[str, int]] = []
    audio, audio_facts = _edit_audio_setup(plan, revision)
    for index, item in enumerate(plan.slices):
        if item.path != plan.source_path:
            candidate = _video_facts(item.path)
            if (candidate[4], candidate[5], candidate[1], candidate[2]) != (
                    width, height, revision.timebase, 0):
                raise ValidationError("candidate geometry, timebase, or PTS does not match the edit")
            decoded_counts.append({
                "item": index, "kind": item.kind, "candidate_frames": candidate[0],
                "candidate_timebase": {"num": candidate[1].num, "den": candidate[1].den},
                "candidate_pts": candidate[2], "decoded_start": item.start,
                "decoded_end": item.end,
            })
        else:
            decoded_counts.append({
                "item": index, "source_frames": source_facts[0], "source_pts": source_facts[2],
                "source_timebase": {"num": source_facts[1].num, "den": source_facts[1].den},
                "decoded_start": item.start, "decoded_end": item.end,
            })
        video.extend(_frames(item.path, item.start, item.end, width, height))
        edit_item = revision.items[index]
        item_checks.append({
            "shot_id": edit_item.shot_id, "take_id": edit_item.take_id,
            "kind": item.kind, "source_range": {"start": edit_item.source_range.start,
                                                 "end": edit_item.source_range.end},
            "decoder_keep": None if edit_item.decoder_keep is None else {
                "start": edit_item.decoder_keep.start, "end": edit_item.decoder_keep.end},
            "timeline_range": {"start": edit_item.timeline_range.start,
                               "end": edit_item.timeline_range.end},
            "input_sha256": item.sha256,
        })
        if audio is not None and audio_facts is not None:
            rate, channels, _codec = audio_facts
            start = _sample_boundary(rate, revision.timebase, edit_item.source_range.start)
            end = _sample_boundary(rate, revision.timebase, edit_item.source_range.end)
            if end <= start:
                raise ValidationError("edit-map audio interval contains no samples")
            audio_intervals.append({
                "item": index, "source_start_sample": start, "source_end_sample": end,
            })
            audio.extend(_pcm(plan.source_path, start, end, rate, channels))
    with tempfile.TemporaryDirectory(prefix="managed-export-", dir=store.root / "managed") as temporary:
        root = Path(temporary)
        video_path = root / "video.raw"
        video_path.write_bytes(video)
        output_path = root / "edit-export.mp4"
        arguments: list[object] = [
            "ffmpeg", "-nostdin", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}",
            "-framerate", f"{revision.timebase.den}/{revision.timebase.num}", "-i", str(video_path),
        ]
        maps = ["-map", "0:v:0"]
        if audio is not None and audio_facts is not None:
            audio_path = root / "audio.raw"
            audio_path.write_bytes(audio)
            arguments.extend([
                "-f", "s16le", "-ar", str(audio_facts[0]), "-ac", str(audio_facts[1]),
                "-i", str(audio_path),
            ])
            maps.extend(["-map", "1:a:0"])
        arguments.extend(maps)
        arguments.extend([
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
        ])
        if audio is not None and audio_facts is not None:
            arguments.extend(["-c:a", "aac", "-b:a", "192k", "-ar", str(audio_facts[0])])
        arguments.extend(["-movflags", "+faststart", str(output_path)])
        _run_tool(arguments)
        count, timebase, pts, _ticks, _width, _height = _video_facts(output_path)
        expected_count = sum(item.end - item.start for item in plan.slices)
        if (count, timebase, pts) != (expected_count, revision.timebase, 0):
            raise ValidationError(
                f"assembled edit frame count, PTS, or timebase mismatch: "
                f"actual={(count, timebase.num, timebase.den, pts)} "
                f"expected={(expected_count, revision.timebase.num, revision.timebase.den, 0)}"
            )
        decoded_output = _frames(output_path, 0, count, width, height)
        video_content = _video_metrics(bytes(video), decoded_output)
        output_audio = _audio_facts(output_path)
        if audio is None:
            if output_audio is not None:
                raise ValidationError("muted edit unexpectedly contains audio")
        elif audio_facts is not None:
            if output_audio is None:
                raise ValidationError("edit-map audio is missing from the export")
            if output_audio[:2] != audio_facts[:2]:
                raise ValidationError("edit-map output audio sample rate or channels drifted")
            audio_content = _audio_metrics(
                bytes(audio), _pcm_all(output_path), audio_facts[1]
            )
        evidence = _stage_output(store, revision, output_path, count, timebase)
    audio_check: dict[str, Any] = {"policy": revision.audio.value}
    if audio is not None and audio_facts is not None:
        audio_check.update({
            "source_sample_rate": audio_facts[0], "channels": audio_facts[1],
            "source_codec": audio_facts[2], "output_codec": output_audio,
            "delay_policy": "aac_priming_bounded_signed_pcm_alignment",
            "boundary_policy": "nearest_absolute_source_sample_half_up",
            "reference_intervals": audio_intervals, "maximum_delay_samples": 4096,
            "content": audio_content,
        })
    checks = {
        "edit_map": {"items": item_checks, "timebase": {
            "num": revision.timebase.num, "den": revision.timebase.den}},
        "audio": audio_check,
        "ffmpeg": {"version": _ffmpeg_version(), "options": {
            "video_codec": "libx264", "audio_codec": "aac" if audio is not None else None,
            "raw_intermediate_pix_fmt": "bgr24", "timestamps": "reset_per_item_concat",
        }},
        "measurements": {"decoded": decoded_counts, "output_frames": count, "output_pts": pts,
                          "output_video_content": video_content,
                          "placement": [{"item": index, "timeline_start": item.timeline_range.start,
                                           "timeline_end": item.timeline_range.end}
                                          for index, item in enumerate(revision.items)]},
        "authority": list(plan.authority),
        "integrity": {
            "source_sha256": plan.scene.source.sha256,
            "selected_sha256": [item.sha256 for item in plan.slices if item.kind == "retained_replay"],
            "output_sha256": evidence.sha256,
        },
    }
    return evidence, checks


def assemble_edit(revision: EditRevision, store: WorkspaceStore) -> OutputEvidence:
    """Assemble one already-authoritative edit into protected output bytes."""
    from .edit_service import EditService
    plan = EditService(store)._media_plan(revision)
    return _assemble_plan(store, revision, plan)[0]
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


def _video_interval(
    path: Path, ffmpeg: str, *, frame_limit: int | None = None
) -> tuple[int, Fraction]:
    """Measure an interval from decoded frames, never container or average-rate metadata."""
    probe = Path(ffmpeg).with_name("ffprobe")
    result = subprocess.run(
        [
            str(probe), "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries", "stream=nb_read_frames,time_base:frame=pts,duration",
            "-of", "json", str(path),
        ],
        check=True, capture_output=True, text=True, timeout=30,
    )
    try:
        payload = json.loads(result.stdout)
        stream = payload["streams"][0]
        frames = payload["frames"]
        measured = int(stream["nb_read_frames"])
        selected = measured if frame_limit is None else min(measured, frame_limit)
        if selected <= 0 or len(frames) != measured:
            raise ValueError("decoded video frame metadata is empty or incomplete")
        ticks = Fraction(str(stream["time_base"]))
        first_pts = int(frames[0]["pts"])
        last_frame = frames[selected - 1]
        last_end = int(last_frame["pts"]) + int(last_frame["duration"])
        return selected, (last_end - first_pts) * ticks
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError) as error:
        raise ValueError("decoded video timing metadata is malformed") from error


def restore_source_audio(
    generated: str | Path,
    source: str | Path,
    destination: str | Path,
    *,
    ffmpeg: str = "ffmpeg",
    frame_count: int | None = None,
) -> None:
    selected_frames, interval = _video_interval(
        Path(generated), ffmpeg, frame_limit=frame_count
    )
    args = [
        "-y",
        "-v",
        "error",
        "-i",
        str(generated),
        "-i",
        str(source),
        "-filter_complex",
        f"[0:v]trim=end_frame={selected_frames},setpts=PTS-STARTPTS,setsar=1[v];"
        "[1:a]aresample=48000,apad[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
    ]
    args.extend(
        [
            "-frames:v", str(selected_frames),
            "-t", f"{float(interval):.12f}",
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

    _source_frames, source_interval = _video_interval(Path(source), ffmpeg)
    final_count, final_interval = _video_interval(Path(final), ffmpeg)
    del _source_frames
    if source_interval < final_interval:
        raise ValueError(
            "source video is shorter than final video; comparison requires the full final interval"
        )

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
            f"[0:v]trim=duration={float(final_interval):.12f},"
            f"setpts=PTS-STARTPTS,{fit_tile}[left];"
            f"[1:v]trim=end_frame={final_count},setpts=PTS-STARTPTS,{fit_tile}[right];"
            "[left][right]hstack[v];[0:a]aresample=48000,apad[aud]",
            "-map",
            "[v]",
            "-map",
            "[aud]",
            "-frames:v", str(final_count),
            "-t", f"{float(final_interval):.12f}",
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
