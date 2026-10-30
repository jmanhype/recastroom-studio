# SPDX-License-Identifier: MIT
"""Exact decoded source accounting for immutable scene revisions."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import subprocess

from .m1_types import FrameRange, RecipePin, SceneRevision, ShotSpec, SourceTiming, Timebase, WindowMap
from .workspace_store import ValidationError, WorkspaceStore, WorkspaceStoreError


class SceneServiceError(Exception):
    """Scene setup failed before any execution was authorized."""


class UnsupportedSourceError(SceneServiceError):
    """The decoded source is not supported by managed milestone one."""


class SceneValidationError(SceneServiceError):
    """A caller-owned scene contract is invalid."""


class WindowQualificationUnavailableError(SceneServiceError):
    """No recipe/window qualification has been approved for managed execution."""


class WindowNotQualifiedError(WindowQualificationUnavailableError):
    """The pinned recipe does not qualify this exact source window."""


_OFFLINE_PIN = (
    "offline-source-routing",
    "cpu-dryrun-v1",
    "79fa70d6b9d3e13852e179cff6f9a3aa36637a8543c600c36517be1b4a2d1a58",
    "cpu_non_inference_routing_v1",
)
CPU_WINDOW_TABLE_VERSION = "openjutsu-cpu-routing-windows-v1-20261027"
_CPU_WINDOW_BOUNDS = ((0, 24), (0, 8), (8, 16), (16, 24))


class SceneService:
    """Probe and freeze exact source partitions through one active store."""

    def __init__(self, store: WorkspaceStore, *, ffprobe: str = "ffprobe") -> None:
        if not isinstance(store, WorkspaceStore):
            raise ValidationError("scene service requires the active WorkspaceStore")
        ffprobe_path = Path(ffprobe) if isinstance(ffprobe, str) else Path()
        if (
            not isinstance(ffprobe, str)
            or not ffprobe
            or ffprobe_path.name != "ffprobe"
            or ".." in ffprobe_path.parts
        ):
            raise ValidationError("ffprobe must be a safe executable name")
        self._store = store
        self._ffprobe = ffprobe

    def probe_source(self, asset_id: str) -> SourceTiming:
        resolved = self._store.resolve_asset(asset_id)
        record = resolved.record
        if record.role != "source" or not record.protected:
            raise SceneValidationError("asset is not a protected source")
        stream_payload = self._probe(resolved.path, ("-count_frames",))
        streams = stream_payload.get("streams", [])
        video = next((item for item in streams if item.get("codec_type") == "video"), None)
        if video is None:
            raise UnsupportedSourceError("source has no decodable video stream")
        decoded_text = video.get("nb_read_frames")
        try:
            frame_count = int(decoded_text)
        except (TypeError, ValueError) as error:
            raise UnsupportedSourceError(
                "source frame count could not be decoded; use a supported CFR MP4 or submit an explicit proxy request"
            ) from error
        if frame_count < 1:
            raise UnsupportedSourceError("source has no decoded frames")
        timebase_text = video.get("time_base")
        try:
            fraction = Fraction(str(timebase_text))
            timebase = Timebase(fraction.numerator, fraction.denominator)
        except (TypeError, ValueError, ZeroDivisionError) as error:
            raise UnsupportedSourceError("source has no positive rational timebase") from error

        frame_payload = self._probe(
            resolved.path,
            ("-select_streams", "v:0", "-show_frames", "-show_entries", "frame=media_type,pts,duration"),
        )
        frames = [item for item in frame_payload.get("frames", []) if item.get("media_type") == "video"]
        if len(frames) != frame_count:
            raise UnsupportedSourceError(
                "decoded frame metadata does not match the source frame count; refusing to normalize silently"
            )
        durations: list[int] = []
        for index, frame in enumerate(frames):
            try:
                pts = int(frame["pts"])
                duration = int(frame["duration"])
            except (KeyError, TypeError, ValueError) as error:
                raise UnsupportedSourceError(
                    f"decoded frame {index} has no integer PTS/duration; VFR sources are unsupported"
                ) from error
            if duration <= 0:
                raise UnsupportedSourceError("decoded frame duration is not positive")
            if index and pts != int(frames[index - 1]["pts"]) + durations[-1]:
                raise UnsupportedSourceError(
                    "variable-frame-rate or discontinuous source is unsupported; use an explicit normalized proxy with original-PTS mapping"
                )
            durations.append(duration)
        if len(set(durations)) != 1:
            raise UnsupportedSourceError(
                "variable-frame-rate source is unsupported; use an explicit normalized proxy with original-PTS mapping"
            )
        frame_period = Fraction(timebase.num, timebase.den) * durations[0]
        has_audio = any(item.get("codec_type") == "audio" for item in streams)
        return SourceTiming(
            asset_id=record.asset_id,
            sha256=record.sha256,
            frame_count=frame_count,
            timebase=Timebase(frame_period.numerator, frame_period.denominator),
            cfr=True,
            has_audio=has_audio,
        )

    def confirm_shots(
        self,
        project_id: str,
        source_asset_id: str,
        shots: tuple[ShotSpec, ...],
    ) -> SceneRevision:
        project = self._store.get_project(project_id)
        source = self._store.resolve_asset(source_asset_id).record
        if source.project_id != project.project_id:
            raise SceneValidationError("source asset belongs to another project")
        timing = self.probe_source(source_asset_id)
        if not isinstance(shots, tuple) or not shots:
            raise SceneValidationError("confirm at least one render or explicit pass-through shot")
        cursor = 0
        ids: set[str] = set()
        for shot in shots:
            if not isinstance(shot, ShotSpec):
                raise SceneValidationError("shots must be typed ShotSpec records")
            if shot.id in ids:
                raise SceneValidationError(f"shot ID {shot.id} is duplicated")
            ids.add(shot.id)
            if shot.source_range.start != cursor:
                raise SceneValidationError(
                    f"shot {shot.id} starts at {shot.source_range.start}; the complete partition requires {cursor}"
                )
            if shot.source_range.end <= shot.source_range.start or shot.source_range.end > timing.frame_count:
                raise SceneValidationError(
                    f"shot {shot.id} has a zero-length, negative, or out-of-range source interval"
                )
            cursor = shot.source_range.end
        if cursor != timing.frame_count:
            raise SceneValidationError(
                f"shots end at frame {cursor}; the complete partition requires {timing.frame_count}"
            )
        candidate = SceneRevision(
            id="pending",
            project_id=project.project_id,
            source=timing,
            shots=shots,
            revision=1,
        )
        return self._store.save_scene_revision(candidate)

    def validate_window(self, shot: ShotSpec, pin: RecipePin) -> WindowMap:
        if not isinstance(shot, ShotSpec) or not isinstance(pin, RecipePin):
            raise SceneValidationError("window validation requires a typed shot and recipe pin")
        pinned = (
            (pin.recipe_id, pin.version, pin.raw_graph_sha256, pin.profile_id)
            == _OFFLINE_PIN
            and pin.adapter_version == "local_cpu_router-1"
            and pin.endpoint_fingerprint
            == "c3f575f84b5c61336316eaca48172c7338476480f255322a84668c90cb5c7d7e"
        )
        bounds = (shot.source_range.start, shot.source_range.end)
        if pinned and shot.kind == "render" and bounds in _CPU_WINDOW_BOUNDS:
            start, end = bounds
            count = end - start
            timebase = Timebase(1, 24)
            return WindowMap(
                source_range=shot.source_range,
                source_timebase=timebase,
                render_range=FrameRange(0, count),
                render_timebase=timebase,
                pad_left=0,
                pad_right=0,
                expected_decoder_frames=count,
                decoder_keep=FrameRange(0, count),
                timeline_range=FrameRange(start, end),
                timeline_timebase=timebase,
                qualification_id=f"qual-cpu-{CPU_WINDOW_TABLE_VERSION}-{start}-{end}",
            )
        if pinned:
            raise WindowNotQualifiedError(
                "offline CPU routing permits only the finite reviewed full/eight-frame fixture table"
            )
        raise WindowQualificationUnavailableError(
            "no qualified recipe window is supported; H3/renderer qualification is OWNER_BLOCKED"
        )

    def _probe(self, path: Path, extra_arguments: tuple[str, ...]) -> dict[str, object]:
        command = [
            self._ffprobe,
            "-v",
            "error",
            "-show_streams",
            *extra_arguments,
            "-of",
            "json",
            str(path),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            return json.loads(result.stdout)
        except FileNotFoundError as error:
            raise SceneServiceError("ffprobe is unavailable; source timing cannot be verified") from error
        except subprocess.TimeoutExpired as error:
            raise SceneServiceError("ffprobe timed out while decoding source timing") from error
        except subprocess.CalledProcessError as error:
            raise UnsupportedSourceError(
                "source could not be decoded; use a supported CFR MP4 or an explicit normalized proxy request"
            ) from error
        except json.JSONDecodeError as error:
            raise SceneServiceError("ffprobe returned malformed timing metadata") from error
