# SPDX-License-Identifier: MIT
"""Real export assembly, carrier, HTTP, and UI proof for M1 edits."""
from __future__ import annotations

import hashlib
import io
import json
from math import isqrt
import struct
from dataclasses import replace
from pathlib import Path
import subprocess
import sqlite3

import pytest

from app.m1_api import create_m1_router
from openjutsu.edit_service import (
    DecoderKeepMismatchError, EditService, MissingRenderTakeError,
    SourceRangeMismatchError, SourceStreamCopyUnsupportedError, TakeScopeMismatchError,
    TimelineNotContiguousError,
)
from openjutsu.m1_types import (
    AudioPolicy, EditItem, FrameRange, ReplayReceipt, ReviewVerdict, ShotSpec, Timebase,
    WindowMap,
)
from openjutsu.m1_types import ExecutionMode
from openjutsu.media import assemble_edit
from openjutsu.recipe_service import OFFLINE_PIN, RecipeService, UnsupportedRecipeError
from openjutsu.scene_service import SceneService
from openjutsu.take_service import TakeService
from openjutsu.workspace_store import ValidationError, WorkspaceStore
from test_m1_resolution import _resolve, _workspace
from test_m1_takes import _replay_fixture
from test_m1_worker import _worker
from tools.foundation_runtime import FFMPEG, FFPROBE


def _json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run(arguments: list[object]) -> bytes:
    result = subprocess.run(
        [str(item) for item in arguments], check=True, capture_output=True, timeout=30
    )
    return result.stdout


def _pixels(path: Path, start: int, end: int) -> bytes:
    return _run([
        FFMPEG, "-nostdin", "-loglevel", "error", "-i", str(path),
        "-vf", f"trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS",
        "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1",
    ])


def _audio(path: Path, start: int = 0, end: int | None = None) -> bytes:
    arguments = [
        FFMPEG, "-nostdin", "-loglevel", "error", "-i", str(path),
        "-map", "0:a:0", "-vn",
    ]
    if end is not None:
        arguments.extend(["-af", f"atrim=start_sample={start}:end_sample={end}"])
    arguments.extend(["-f", "s16le", "-acodec", "pcm_s16le", "pipe:1"])
    return _run(arguments)


def _assert_signed_audio(expected: bytes, actual: bytes, channels: int) -> None:
    expected_samples = struct.unpack(f"<{len(expected) // 2}h", expected)
    actual_samples = struct.unpack(f"<{len(actual) // 2}h", actual)
    assert len(expected_samples) % channels == 0
    assert len(actual_samples) <= len(expected_samples) + 4096 * channels
    candidates = []
    for delay in range(
        0, min(4096 * channels, len(actual_samples) - len(expected_samples)) + 1,
        1024 * channels,
    ):
        differences = [abs(left - right) for left, right in zip(
            expected_samples, actual_samples[delay:]
        )]
        candidates.append((sum(differences) / len(differences), max(differences),
                           sum(value > 512 for value in differences) / len(differences), delay))
    mean, maximum, outliers, _delay = min(candidates)
    assert mean <= 48 and maximum <= 4096 and outliers <= 0.01


def _source_workspace(
    root: Path, *, audio: str | None, rate: int = 48_000, codec: str = "libx264",
    suffix: str = ".mp4", frame_rate: str = "24", duration: str = "0.5",
):
    store = WorkspaceStore(root / "workspace")
    project = store.create_project("Edit audio")
    media_path = root / f"source{suffix}"
    arguments: list[object] = [
        FFMPEG, "-nostdin", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"testsrc2=size=64x64:rate={frame_rate}",
    ]
    if audio is not None:
        source = (
            f"sine=frequency=440:sample_rate={rate}"
            if audio == "tone"
            else f"anullsrc=channel_layout=mono:sample_rate={rate}"
        )
        arguments.extend([
            "-f", "lavfi", "-i",
            source,
        ])
    if audio is None:
        arguments.extend(["-map", "0:v:0", "-c:v", codec, "-pix_fmt", "yuv420p"])
    else:
        arguments.extend([
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", codec,
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", str(rate),
        ])
    arguments.extend(["-t", duration])
    arguments.append(media_path)
    _run(arguments)
    staged = store.stage_asset(
        project.project_id, media_path.name, io.BytesIO(media_path.read_bytes()),
        role="source", protected=True,
    )
    probe = SceneService(store, ffprobe=str(FFPROBE)).probe_source(staged.asset_id)
    scene = SceneService(store, ffprobe=str(FFPROBE)).confirm_shots(
        project.project_id, staged.asset_id,
        (ShotSpec("source", FrameRange(0, probe.frame_count), "pass_through"),),
    )
    return store, scene


def _export_fixture(root: Path):
    store, operation, _duplicate, dry_take, receipt = _replay_fixture(root)
    replay = TakeService(store).import_replay(
        operation.project_id, receipt,
        io.BytesIO(store.resolve_asset(dry_take.output.asset_id).path.read_bytes()),
    )
    scene = store.get_scene_revision(operation.project_id, operation.scene_revision_id)
    return store, scene, replay


def _trimmed_reorder(store: WorkspaceStore, scene, replay) -> tuple[EditItem, ...]:
    return (
        EditItem("tail", None, FrameRange(16, 24), None, FrameRange(0, 8)),
        EditItem("second", replay.id, FrameRange(10, 14), FrameRange(2, 6), FrameRange(8, 12)),
    )


def _replay_in_new_scene(store: WorkspaceStore, scene, replay):
    current = store.get_operation(scene.project_id, replay.operation_id or "")
    replay_scene = store.save_scene_revision(replace(
        scene, id="pending", revision=2,
    ))
    operation = _resolve(
        store, replay_scene.id, current.character_version, shot_id="second"
    )
    store.authorize_attempt(
        operation, f"frozen-{operation.id}", ExecutionMode.DRY_RUN, None
    )
    with store.worker_lock(f"frozen-{operation.id}"):
        assert _worker(store)
    with store._connect() as db:
        take_id = db.execute(
            "SELECT take_id FROM takes WHERE operation_id=?", (operation.id,)
        ).fetchone()[0]
    source_take = store.get_take(operation.project_id, take_id)
    manifest = json.loads(operation.canonical_json)
    receipt = ReplayReceipt(
        operation.scene_revision_id, operation.shot_id,
        manifest["source"]["sha256"], manifest["source"]["proxy_sha256"],
        operation.pin.recipe_id, operation.pin.version,
        operation.pin.raw_graph_sha256,
        manifest["graph"]["resolved_semantic_sha256"],
        source_take.output.sha256, operation.window, ReviewVerdict.KEEPER,
    )
    replay_take = TakeService(store).import_replay(
        operation.project_id, receipt,
        io.BytesIO(store.resolve_asset(source_take.output.asset_id).path.read_bytes()),
    )
    return replay_scene, replay_take


def _assert_video(store: WorkspaceStore, scene, replay, export_path: Path) -> None:
    count, timebase, first_pts, _ticks = TakeService._probe(export_path)
    assert (count, timebase, first_pts) == (12, Timebase(1, 24), 0)
    actual = _pixels(export_path, 0, count)
    source = store.resolve_asset(scene.source.asset_id).path
    candidate = store.resolve_asset(replay.output.asset_id).path
    expected = (
        _pixels(source, 16, 24) + _pixels(candidate, 2, 6)
    )
    assert len(actual) == len(expected)
    frame_bytes = len(expected) // count
    for frame in range(count):
        left = actual[frame * frame_bytes:(frame + 1) * frame_bytes]
        right = expected[frame * frame_bytes:(frame + 1) * frame_bytes]
        mean = sum(abs(a - b) for a, b in zip(left, right)) / frame_bytes
        outliers = sum(abs(a - b) > 32 for a, b in zip(left, right)) / frame_bytes
        assert mean < 5 and outliers < 0.01, frame


def test_exact_trim_reorder_edit_map_audio_and_frozen_scope(tmp_path: Path) -> None:
    store, scene, replay = _export_fixture(tmp_path)
    service = EditService(store)
    revision = service.create_revision(
        scene.project_id, scene.id, _trimmed_reorder(store, scene, replay),
        AudioPolicy.SOURCE_EDIT_MAP,
    )
    exported = service.export_revision(revision.id)
    assert exported.state == "completed" and exported.sha256
    output = store.resolve_asset(str(exported.asset_id))
    assert hashlib.sha256(output.path.read_bytes()).hexdigest() == exported.sha256
    _assert_video(store, scene, replay, output.path)
    source_path = store.resolve_asset(scene.source.asset_id).path
    expected_audio = _audio(source_path, 32000, 48000) + _audio(source_path, 20000, 28000)
    actual_audio = _run([
        FFMPEG, "-nostdin", "-loglevel", "error", "-i", str(output.path),
        "-map", "0:a:0", "-vn", "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1",
    ])
    assert len(expected_audio) == 48_000
    _assert_signed_audio(expected_audio, actual_audio, 1)
    checks = json.loads(exported.checks_json)
    assert checks["edit_map"]["items"][1]["source_range"] == {"start": 10, "end": 14}
    assert checks["audio"]["policy"] == "source_edit_map"
    assert checks["authority"][0]["qualification_id"].startswith("qual-cpu-openjutsu-cpu-routing")
    assert checks["authority"][0]["qualification_scope"] == (
        "qualified_zero_pad_offline_cpu; not n_minus_one, nonzero_pad, "
        "general_h3, or promoted_historical_keeper"
    )
    assert checks["ffmpeg"]["version"] and checks["ffmpeg"]["options"]["video_codec"] == "libx264"
    assert checks["integrity"]["output_sha256"] == exported.sha256

    TakeService(store).select(scene.project_id, scene.id, "second", None, 0)
    assert store.get_export(scene.project_id, exported.id).sha256 == exported.sha256
    frozen_items = store.get_edit_revision(scene.project_id, revision.id).items
    frozen_bytes = output.path.read_bytes()
    r2, replay_r2 = _replay_in_new_scene(store, scene, replay)
    with pytest.raises(TakeScopeMismatchError, match="take does not match"):
        service.create_revision(
            scene.project_id, r2.id, (EditItem(
                "second", replay.id, FrameRange(8, 16), None, FrameRange(0, 8)
            ),), AudioPolicy.MUTE,
        )
    with pytest.raises(TakeScopeMismatchError, match="take does not match"):
        service.create_revision(
            scene.project_id, scene.id, (EditItem(
                "second", replay_r2.id, FrameRange(8, 16), None, FrameRange(0, 8)
            ),), AudioPolicy.MUTE,
        )
    assert store.get_edit_revision(scene.project_id, revision.id).items == frozen_items
    assert store.get_export(scene.project_id, exported.id).sha256 == exported.sha256
    assert store.resolve_asset(str(exported.asset_id)).path.read_bytes() == frozen_bytes


def test_audio_policies_and_stream_copy_are_measured_not_assumed(tmp_path: Path) -> None:
    store, scene, replay = _export_fixture(tmp_path)
    service = EditService(store)
    full = (EditItem("first", None, FrameRange(0, 24), None, FrameRange(0, 24)),)
    full_scene = store.save_scene_revision(replace(scene, id="pending", revision=2, shots=(
        ShotSpec("first", FrameRange(0, 24), "pass_through"),
    )))
    copied = service.create_revision(
        scene.project_id, full_scene.id, full, AudioPolicy.SOURCE_STREAM_COPY
    )
    copied_export = service.export_revision(copied.id)
    copied_path = store.resolve_asset(str(copied_export.asset_id)).path
    assert TakeService._probe(copied_path)[:3] == (24, scene.source.timebase, 0)
    copied_checks = json.loads(copied_export.checks_json)
    assert copied_checks["stream_copy"]["packet_match"] is True
    assert copied_checks["stream_copy"]["source_packets"] == copied_checks["stream_copy"]["output_packets"]
    assert copied_checks["measurements"]["decoded_audio_match"] is True
    assert copied_checks["audio"]["source"] == copied_checks["audio"]["output"]

    with pytest.raises(SourceStreamCopyUnsupportedError, match="source_stream_copy"):
        service.create_revision(
            scene.project_id, full_scene.id, (EditItem(
                "first", None, FrameRange(0, 12), None, FrameRange(0, 12)
            ),), AudioPolicy.SOURCE_STREAM_COPY,
        )
    with pytest.raises(SourceStreamCopyUnsupportedError, match="source_stream_copy"):
        service.create_revision(
            scene.project_id, full_scene.id, (EditItem(
                "first", None, FrameRange(0, 24), None, FrameRange(0, 24),
            ), EditItem(
                "first", None, FrameRange(0, 24), None, FrameRange(24, 48),
            )), AudioPolicy.SOURCE_STREAM_COPY,
        )
    incompatible_store, incompatible_scene = _source_workspace(
        tmp_path / "incompatible", audio=None, codec="mpeg4"
    )
    incompatible_revision = EditService(incompatible_store).create_revision(
        incompatible_scene.project_id, incompatible_scene.id, (EditItem(
            "source", None, FrameRange(0, 12), None, FrameRange(0, 12),
        ),), AudioPolicy.SOURCE_STREAM_COPY,
    )
    with pytest.raises(ValidationError, match="codec or mux"):
        EditService(incompatible_store).export_revision(incompatible_revision.id)

    muted = service.create_revision(
        scene.project_id, scene.id, (EditItem(
            "second", replay.id, FrameRange(8, 16), None, FrameRange(0, 8)
        ),), AudioPolicy.MUTE,
    )
    muted_export = service.export_revision(muted.id)
    muted_path = store.resolve_asset(str(muted_export.asset_id)).path
    assert _run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries",
                 "stream=codec_type", "-of", "csv=p=0", muted_path]) == b""


def test_named_edit_failures_leave_no_export(tmp_path: Path) -> None:
    store, scene, replay = _export_fixture(tmp_path)
    service = EditService(store)
    missing = (EditItem("second", None, FrameRange(8, 16), None, FrameRange(0, 8)),)
    with pytest.raises(MissingRenderTakeError, match="render item second requires a take"):
        service.create_revision(scene.project_id, scene.id, missing, AudioPolicy.MUTE)
    bad_timelines = (
        ((EditItem("second", replay.id, FrameRange(8, 16), None, FrameRange(1, 9)),), "timeline"),
        ((EditItem("tail", None, FrameRange(16, 24), None, FrameRange(0, 8)),
          EditItem("second", replay.id, FrameRange(8, 16), None, FrameRange(9, 17))), "timeline"),
        ((EditItem("tail", None, FrameRange(16, 24), None, FrameRange(0, 8)),
          EditItem("second", replay.id, FrameRange(8, 16), None, FrameRange(7, 15))), "timeline"),
        ((EditItem("second", replay.id, FrameRange(8, 16), None, FrameRange(0, 7)),), "timeline"),
    )
    for items, detail in bad_timelines:
        with pytest.raises(TimelineNotContiguousError, match=detail):
            service.create_revision(scene.project_id, scene.id, items, AudioPolicy.MUTE)
    for start, end in ((-1, 4), (4, 4)):
        with pytest.raises(ValueError, match="frame"):
            FrameRange(start, end)
    failures = (
        (EditItem("second", replay.id, FrameRange(9, 17), None, FrameRange(0, 8)), "source range"),
        (EditItem("absent", replay.id, FrameRange(0, 8), None, FrameRange(0, 8)), "outside the frozen scene"),
        (EditItem("tail", replay.id, FrameRange(16, 24), None, FrameRange(0, 8)), "explicit pass-through"),
    )
    for item, detail in failures:
        with pytest.raises((SourceRangeMismatchError, TakeScopeMismatchError), match=detail):
            service.create_revision(scene.project_id, scene.id, (item,), AudioPolicy.MUTE)
    decoder_failures = (
        EditItem("second", replay.id, FrameRange(10, 14), FrameRange(3, 7), FrameRange(0, 4)),
        EditItem("second", replay.id, FrameRange(10, 14), FrameRange(2, 7), FrameRange(0, 4)),
        EditItem("second", replay.id, FrameRange(10, 14), FrameRange(1, 5), FrameRange(0, 4)),
    )
    for item in decoder_failures:
        invalid_decoder = service.create_revision(
            scene.project_id, scene.id, (item,), AudioPolicy.MUTE
        )
        with pytest.raises(DecoderKeepMismatchError, match="exact source interval"):
            service.export_revision(invalid_decoder.id)
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM exports").fetchone()[0] == 0


def test_qualified_zero_pad_accepts_exact_seven_frame_trim(tmp_path: Path) -> None:
    store, scene, replay = _export_fixture(tmp_path)
    service = EditService(store)
    revision = service.create_revision(
        scene.project_id, scene.id, (EditItem(
            "second", replay.id, FrameRange(8, 15), FrameRange(0, 7), FrameRange(0, 7),
        ),), AudioPolicy.MUTE,
    )
    exported = service.export_revision(revision.id)
    output = store.resolve_asset(str(exported.asset_id)).path
    assert TakeService._probe(output)[:3] == (7, Timebase(1, 24), 0)
    actual = _pixels(output, 0, 7)
    expected = _pixels(store.resolve_asset(replay.output.asset_id).path, 0, 7)
    assert len(actual) == len(expected)
    frame_bytes = len(expected) // 7
    for frame in range(7):
        left = actual[frame * frame_bytes:(frame + 1) * frame_bytes]
        right = expected[frame * frame_bytes:(frame + 1) * frame_bytes]
        differences = [abs(a - b) for a, b in zip(left, right)]
        assert sum(differences) / len(differences) < 5
        assert sum(value > 32 for value in differences) / len(differences) < 0.01
    assert _run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries",
                 "stream=codec_type", "-of", "csv=p=0", output]) == b""
    checks = json.loads(exported.checks_json)
    assert checks["measurements"]["output_frames"] == 7
    assert checks["authority"][0]["padding_removed"] == 0
    assert checks["authority"][0]["qualification_scope"] == (
        "qualified_zero_pad_offline_cpu; not n_minus_one, nonzero_pad, "
        "general_h3, or promoted_historical_keeper"
    )


def test_real_padded_cpu_input_remains_unqualified_and_cannot_export(tmp_path: Path) -> None:
    """A real padded decode cannot mint authority; its positive remains unavailable."""
    store, scene, replay = _export_fixture(tmp_path)
    service = EditService(store)
    window, pin = store._qualified_replay_carrier(
        scene.project_id, scene.id, "second", replay.id
    )
    accepted_path = store.resolve_asset(replay.output.asset_id).path
    accepted_frames = _pixels(accepted_path, 0, window.expected_decoder_frames)
    assert window.pad_left == window.pad_right == 0
    assert len(accepted_frames) % (window.expected_decoder_frames * 3) == 0

    frame_bytes = len(accepted_frames) // window.expected_decoder_frames
    frame_side = isqrt(frame_bytes // 3)
    assert frame_side * frame_side * 3 == frame_bytes
    synthetic_frame = bytes((32, 64, 128)) * (frame_bytes // 3)
    synthetic_left = synthetic_frame * 2
    synthetic_right = bytes((160, 96, 48)) * (frame_bytes // 3)
    padded_raw = tmp_path / "padded.raw"
    padded_raw.write_bytes(
        synthetic_left + accepted_frames + synthetic_right
    )
    padded_path = tmp_path / "padded.nut"
    _run([
        FFMPEG, "-nostdin", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pix_fmt", "bgr24", "-s", f"{frame_side}x{frame_side}", "-framerate", "24",
        "-i", str(padded_raw),
        "-map", "0:v:0", "-c:v", "ffv1", "-level", "3", "-g", "1",
        "-pix_fmt", "yuv420p", str(padded_path),
    ])
    assert TakeService._probe(padded_path)[:3] == (
        11, Timebase(1, 24), 0,
    )

    hypothetical = WindowMap(
        window.source_range, window.source_timebase, FrameRange(0, 11),
        window.render_timebase, 2, 1, 11, FrameRange(2, 10),
        window.timeline_range, window.timeline_timebase,
        "unqualified-hypothetical-nonzero-pad",
    )
    operation = store.get_operation(scene.project_id, replay.operation_id or "")
    manifest = json.loads(operation.canonical_json)
    padded_receipt = ReplayReceipt(
        scene.id, "second", manifest["source"]["sha256"],
        manifest["source"]["proxy_sha256"], pin.recipe_id, pin.version,
        pin.raw_graph_sha256, manifest["graph"]["resolved_semantic_sha256"],
        hashlib.sha256(padded_path.read_bytes()).hexdigest(), hypothetical, None,
    )
    with store._connect() as db:
        before = tuple(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in (
            "takes", "qualified_replay_receipts", "exports",
        ))
    with pytest.raises(ValidationError, match=r"EVIDENCE_(UNAVAILABLE|AMBIGUOUS)"):
        TakeService(store).import_replay(
            scene.project_id, padded_receipt, io.BytesIO(padded_path.read_bytes())
        )
    with pytest.raises(ValidationError, match="EVIDENCE_UNAVAILABLE"):
        service._validate_current_authority(scene.shots[1], hypothetical, pin)
    with store._connect() as db:
        after = tuple(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in (
            "takes", "qualified_replay_receipts", "exports",
        ))
    assert after == before and after[2] == 0


def test_edit_map_measures_full_silence_no_audio_and_sample_boundary(tmp_path: Path) -> None:
    full_store, full_scene = _source_workspace(tmp_path / "full", audio="tone")
    full_service = EditService(full_store)
    full_revision = full_service.create_revision(
        full_scene.project_id, full_scene.id, (EditItem(
            "source", None, FrameRange(0, 12), None, FrameRange(0, 12),
        ),), AudioPolicy.SOURCE_EDIT_MAP,
    )
    full_export = full_service.export_revision(full_revision.id)
    full_output = full_store.resolve_asset(str(full_export.asset_id)).path
    full_source = full_store.resolve_asset(full_scene.source.asset_id).path
    _assert_signed_audio(_audio(full_source), _audio(full_output), 1)

    silent_store, silent_scene = _source_workspace(
        tmp_path / "silence", audio="silence", rate=44_100
    )
    silent_service = EditService(silent_store)
    silent_revision = silent_service.create_revision(
        silent_scene.project_id, silent_scene.id, (EditItem(
            "source", None, FrameRange(5, 11), None, FrameRange(0, 6),
        ),), AudioPolicy.SOURCE_EDIT_MAP,
    )
    silent_export = silent_service.export_revision(silent_revision.id)
    silent_output = silent_store.resolve_asset(str(silent_export.asset_id)).path
    silent_source = silent_store.resolve_asset(silent_scene.source.asset_id).path
    expected_silence = _audio(silent_source, 9_188, 20_213)
    assert len(expected_silence) == 22_050
    _assert_signed_audio(expected_silence, _audio(silent_output), 1)
    silent_checks = json.loads(silent_export.checks_json)
    assert silent_checks["audio"]["content"]["expected_samples"] == 11_025

    quiet_store, quiet_scene = _source_workspace(tmp_path / "quiet", audio=None)
    quiet_service = EditService(quiet_store)
    quiet_revision = quiet_service.create_revision(
        quiet_scene.project_id, quiet_scene.id, (EditItem(
            "source", None, FrameRange(8, 12), None, FrameRange(0, 4),
        ),), AudioPolicy.SOURCE_EDIT_MAP,
    )
    quiet_export = quiet_service.export_revision(quiet_revision.id)
    quiet_output = quiet_store.resolve_asset(str(quiet_export.asset_id)).path
    assert _run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries",
                 "stream=codec_type", "-of", "csv=p=0", quiet_output]) == b""


def test_adjacent_fractional_frames_use_absolute_sample_boundaries(tmp_path: Path) -> None:
    store, scene = _source_workspace(
        tmp_path / "fractional", audio="tone", rate=44_100,
        frame_rate="30000/1001", duration="0.5",
    )
    assert scene.source.frame_count == 15
    assert scene.source.timebase == Timebase(1001, 30_000)
    assert scene.source.cfr is True
    service = EditService(store)
    items = tuple(
        EditItem(
            "source", None, FrameRange(frame, frame + 1), None,
            FrameRange(frame, frame + 1),
        )
        for frame in range(15)
    )
    revision = service.create_revision(
        scene.project_id, scene.id, items, AudioPolicy.SOURCE_EDIT_MAP,
    )
    exported = service.export_revision(revision.id)
    output = store.resolve_asset(str(exported.asset_id)).path
    assert TakeService._probe(output)[:3] == (15, Timebase(1001, 30_000), 0)

    source = store.resolve_asset(scene.source.asset_id).path
    expected = _audio(source, 0, 22_072)
    assert len(expected) == 22_072 * 2
    _assert_signed_audio(expected, _audio(output), 1)
    checks = json.loads(exported.checks_json)
    assert checks["audio"]["boundary_policy"] == (
        "nearest_absolute_source_sample_half_up"
    )
    assert checks["audio"]["reference_intervals"][1:3] == [
        {"item": 1, "source_start_sample": 1_471, "source_end_sample": 2_943},
        {"item": 2, "source_start_sample": 2_943, "source_end_sample": 4_414},
    ]
    assert checks["audio"]["content"]["expected_samples"] == 22_072


def test_carrier_authority_and_unpinned_window_fail_closed(tmp_path: Path) -> None:
    store, scene, replay = _export_fixture(tmp_path)
    window, pin = store._qualified_replay_carrier(
        scene.project_id, scene.id, "second", replay.id
    )
    linked = store.get_operation(scene.project_id, replay.operation_id or "")
    assert window == _resolve(
        store, scene.id, linked.character_version, shot_id="second"
    ).window
    assert pin == OFFLINE_PIN
    assert window.source_range == FrameRange(8, 16)
    assert window.pad_left == window.pad_right == 0
    assert window.expected_decoder_frames == 8
    with pytest.raises(ValidationError, match="carrier"):
        store._qualified_replay_carrier(scene.project_id, scene.id, "tail", replay.id)
    with pytest.raises(ValidationError, match="carrier"):
        store._qualified_replay_carrier(scene.project_id, scene.id, "second", "take-absent")
    with store._connect() as db:
        original = db.execute(
            "SELECT window_json,output_sha256,operation_id "
            "FROM qualified_replay_receipts WHERE take_id=?", (replay.id,)
        ).fetchone()
        db.execute("DROP TRIGGER qualified_replay_receipts_v4_immutable_update")
        db.commit()
    try:
        with store._connect() as db:
            db.execute(
                "UPDATE qualified_replay_receipts SET window_json=? WHERE take_id=?",
                ("{", replay.id),
            )
            db.commit()
        with pytest.raises(ValidationError, match="carrier is malformed"):
            store._qualified_replay_carrier(scene.project_id, scene.id, "second", replay.id)
        with store._connect() as db:
            db.execute(
                "UPDATE qualified_replay_receipts SET output_sha256=? WHERE take_id=?",
                ("0" * 64, replay.id),
            )
            db.commit()
        with pytest.raises(ValidationError, match="output asset hash"):
            store._qualified_replay_carrier(scene.project_id, scene.id, "second", replay.id)
        with store._connect() as db:
            db.execute(
                "UPDATE qualified_replay_receipts SET operation_id=NULL WHERE take_id=?",
                (replay.id,),
            )
            db.commit()
        with pytest.raises(ValidationError, match="non-null linked operation"):
            store._qualified_replay_carrier(scene.project_id, scene.id, "second", replay.id)
    finally:
        with store._connect() as db:
            db.execute(
                "UPDATE qualified_replay_receipts SET window_json=?,output_sha256=?,operation_id=? "
                "WHERE take_id=?",
                (original["window_json"], original["output_sha256"],
                 original["operation_id"], replay.id),
            )
            db.commit()
            db.execute("""CREATE TRIGGER qualified_replay_receipts_v4_immutable_update
                BEFORE UPDATE ON qualified_replay_receipts
                BEGIN SELECT RAISE(ABORT, 'qualified replay receipt is immutable'); END""")
    h3 = replace(pin, profile_id="h3_gpu")
    with pytest.raises(ValidationError, match="EVIDENCE_UNAVAILABLE"):
        EditService(store)._validate_current_authority(scene.shots[1], window, h3)

    n_minus_one = store.save_scene_revision(replace(scene, id="pending", revision=2, shots=(
        ShotSpec("short", FrameRange(0, 23), "render"),
        ShotSpec("tail", FrameRange(23, 24), "pass_through"),
    )))
    character = store.get_operation(scene.project_id, replay.operation_id or "").character_version
    with pytest.raises(UnsupportedRecipeError, match="finite"):
        RecipeService(store).resolve(
            scene.project_id, n_minus_one.id, "short", pin, character, 117,
            rights_attested=True,
        )
    with pytest.raises(TakeScopeMismatchError, match="take does not match"):
        EditService(store).create_revision(
            scene.project_id, n_minus_one.id, (EditItem(
                "short", replay.id, FrameRange(0, 23), None, FrameRange(0, 23),
            ),), AudioPolicy.MUTE,
        )
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM exports").fetchone()[0] == 0


def test_http_edit_export_download_and_ui_wiring(tmp_path: Path) -> None:
    store, scene, replay = _export_fixture(tmp_path)
    from fastapi.testclient import TestClient
    import app.main as main
    from openjutsu.config import load_settings
    saved = (main.SETTINGS, main.PROJECT_STORE, main.app.state.workspace_store)
    main.SETTINGS = load_settings({
        "OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(store.root),
        "OPENJUTSU_FFPROBE": str(FFPROBE),
    })
    try:
        with TestClient(main.app) as client:
            payload = {
                "scene_revision_id": scene.id,
                "items": [{
                    "shot_id": item.shot_id, "take_id": item.take_id,
                    "source_range": {"start": item.source_range.start, "end": item.source_range.end},
                    "decoder_keep": None if item.decoder_keep is None else {
                        "start": item.decoder_keep.start, "end": item.decoder_keep.end},
                    "timeline_range": {"start": item.timeline_range.start, "end": item.timeline_range.end},
                } for item in _trimmed_reorder(store, scene, replay)],
                "audio": "source_edit_map",
                "timebase": {"num": 1, "den": 24},
            }
            created = client.post(f"/api/projects/{scene.project_id}/edit-revisions", json=payload)
            assert created.status_code == 201, created.text
            revision = created.json()
            exported = client.post(f"/edit-revisions/{revision['id']}/exports")
            assert exported.status_code == 200, exported.text
            record = exported.json()
            fetched = client.get(f"/exports/{record['id']}")
            assert fetched.status_code == 200 and fetched.json() == record
            download = client.get(f"/exports/{record['id']}/artifact")
            assert download.status_code == 200
            assert download.headers["content-type"].startswith("video/mp4")
            assert hashlib.sha256(download.content).hexdigest() == record["sha256"]
            assert len(download.content) > 1000
            script = client.get("/m1.js").text
            assert all(token in script for token in (
                "m1-export-list", "m1-create-edit", "m1-export", "m1-export-download",
                "/edit-revisions/", "/artifact",
            ))
    finally:
        main.SETTINGS, main.PROJECT_STORE, main.app.state.workspace_store = saved
