# SPDX-License-Identifier: MIT
"""Frozen edit validation and authoritative CPU export assembly."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .media import _ManagedPlan, _MediaSlice, _assemble_plan, _video_facts
from .m1_types import (
    AudioPolicy, EditItem, EditRevision, ExportRecord, FrameRange, RecipePin,
    SceneRevision, ShotSpec, WindowMap,
)
from .take_service import TakeService
from .workspace_store import ValidationError, WorkspaceStore


class EditServiceError(ValueError):
    """An edit request is outside the frozen managed contract."""


class MissingRenderTakeError(EditServiceError):
    """A render item was submitted without its mandatory retained take."""


class TimelineNotContiguousError(EditServiceError):
    """Edit output ranges do not form one contiguous timeline from zero."""


class SourceRangeMismatchError(EditServiceError):
    """An edit range is outside its authoritative frozen shot or scene."""


class DecoderKeepMismatchError(EditServiceError):
    """Decoder retention does not remove synthetic padding at the exact source interval."""


class TakeScopeMismatchError(EditServiceError):
    """A selected take belongs to a different project, scene, or shot."""


class SourceStreamCopyUnsupportedError(EditServiceError):
    """The requested edit cannot preserve audio by an exact source stream copy."""


class EditService:
    def __init__(self, store: WorkspaceStore) -> None:
        if not isinstance(store, WorkspaceStore):
            raise ValidationError("edit service requires the active WorkspaceStore")
        self._store = store

    def _scene_and_items(
        self, project_id: str, scene_revision_id: str, items: tuple[EditItem, ...]
    ) -> tuple[SceneRevision, tuple[EditItem, ...]]:
        if not isinstance(items, tuple) or not items:
            raise ValidationError("items must be a non-empty tuple")
        scene = self._store.get_scene_revision(project_id, scene_revision_id)
        partition_end = 0
        seen_shots: set[str] = set()
        for shot in scene.shots:
            if shot.id in seen_shots or shot.source_range.start != partition_end:
                raise SourceRangeMismatchError("frozen scene shots do not exactly partition the source")
            seen_shots.add(shot.id)
            partition_end = shot.source_range.end
        if partition_end != scene.source.frame_count:
            raise SourceRangeMismatchError("frozen scene shots do not exactly partition the source")
        cursor = 0
        for item in items:
            if not isinstance(item, EditItem):
                raise ValidationError("each edit item must be a typed EditItem")
            shot = next((entry for entry in scene.shots if entry.id == item.shot_id), None)
            if shot is None:
                raise SourceRangeMismatchError(f"edit shot {item.shot_id} is outside the frozen scene")
            if (item.source_range.start < shot.source_range.start
                    or item.source_range.end > shot.source_range.end):
                raise SourceRangeMismatchError(
                    f"edit item {item.shot_id} source range is outside its frozen shot"
                )
            length = item.source_range.end - item.source_range.start
            timeline_length = item.timeline_range.end - item.timeline_range.start
            if item.timeline_range.start != cursor or timeline_length != length:
                raise TimelineNotContiguousError(
                    "edit timeline must be contiguous once from zero and match item length"
                )
            if shot.kind == "render" and item.take_id is None:
                raise MissingRenderTakeError(f"render item {item.shot_id} requires a take")
            if shot.kind == "pass_through" and item.take_id is not None:
                raise TakeScopeMismatchError("explicit pass-through cannot select a take")
            if item.decoder_keep is not None and shot.kind == "pass_through":
                raise DecoderKeepMismatchError("pass-through cannot select decoder padding")
            cursor = item.timeline_range.end
        return scene, items

    def create_revision(
        self,
        project_id: str,
        scene_revision_id: str,
        items: tuple[EditItem, ...],
        audio: AudioPolicy,
    ) -> EditRevision:
        scene, items = self._scene_and_items(project_id, scene_revision_id, items)
        if not isinstance(audio, AudioPolicy):
            raise ValidationError("audio policy is unsupported")
        if audio is AudioPolicy.SOURCE_STREAM_COPY and (
                len(items) != 1 or items[0].source_range != FrameRange(0, scene.source.frame_count)
                or items[0].timeline_range != FrameRange(0, scene.source.frame_count)
                or items[0].take_id is not None
                or next(entry for entry in scene.shots if entry.id == items[0].shot_id).kind != "pass_through"):
            raise SourceStreamCopyUnsupportedError(
                "source_stream_copy requires one unchanged full-source explicit pass-through item"
            )
        for item in items:
            shot = next(entry for entry in scene.shots if entry.id == item.shot_id)
            if item.take_id is None:
                continue
            take = self._store.get_take(project_id, item.take_id)
            if (take.project_id, take.scene_revision_id, take.shot_id) != (
                    project_id, scene_revision_id, item.shot_id):
                raise TakeScopeMismatchError(
                    "selected take does not match the enclosing project, scene, and shot"
                )
        candidate = EditRevision(
            "pending", project_id, scene_revision_id, items, audio, scene.source.timebase
        )
        return self._store.save_edit_revision(candidate)

    def _validate_current_authority(
        self, shot: ShotSpec, window: WindowMap, pin: RecipePin
    ) -> None:
        """Use the accepted c5nr gate without manufacturing a new attestation."""
        TakeService._validated_current_cpu_window(
            self._store, shot, window, pin=pin
        )

    def _validated_source(self, scene: SceneRevision, project_id: str) -> Path:
        resolved = self._store.resolve_asset(scene.source.asset_id)
        if (resolved.record.project_id != project_id
                or not resolved.record.protected
                or resolved.record.role != "source"
                or resolved.record.sha256 != scene.source.sha256):
            raise ValidationError("protected source asset scope or hash drifted")
        facts = _video_facts(resolved.path)
        if facts[:3] != (scene.source.frame_count, scene.source.timebase, 0):
            raise ValidationError("measured source frame count, PTS, or timebase drifted")
        return resolved.path

    def _stream_copy_plan(
        self, scene: SceneRevision, revision: EditRevision, source_path: Path
    ) -> _ManagedPlan:
        item = revision.items[0] if len(revision.items) == 1 else None
        if (item is None or item.shot_id != scene.shots[0].id
                or item.source_range != FrameRange(0, scene.source.frame_count)
                or item.timeline_range != FrameRange(0, scene.source.frame_count)
                or item.take_id is not None or scene.shots[0].kind != "pass_through"):
            raise SourceStreamCopyUnsupportedError(
                "source_stream_copy requires one unchanged full-source explicit pass-through item"
            )
        return _ManagedPlan(scene, source_path, (), ())

    def _media_plan(self, revision: EditRevision) -> _ManagedPlan:
        scene, _items = self._scene_and_items(
            revision.project_id, revision.scene_revision_id, revision.items
        )
        if not isinstance(revision.audio, AudioPolicy):
            raise ValidationError("audio policy is unsupported")
        if revision.timebase != scene.source.timebase:
            raise ValidationError("edit timebase does not match the frozen source")
        source_path = self._validated_source(scene, revision.project_id)
        slices: list[_MediaSlice] = []
        authorities: list[dict[str, Any]] = []
        cursor = 0
        if revision.audio is AudioPolicy.SOURCE_STREAM_COPY:
            return self._stream_copy_plan(scene, revision, source_path)
        for item in revision.items:
            shot = next(entry for entry in scene.shots if entry.id == item.shot_id)
            if shot.kind == "pass_through":
                if item.decoder_keep is not None:
                    raise DecoderKeepMismatchError("pass-through decoder_keep must be null")
                slices.append(_MediaSlice(
                    source_path, scene.source.asset_id, scene.source.sha256,
                    "pass_through", item.source_range.start, item.source_range.end,
                ))
            else:
                if item.take_id is None:
                    raise MissingRenderTakeError("render item requires a selected take")
                take = self._store.get_take(revision.project_id, item.take_id)
                window, pin = self._store._qualified_replay_carrier(
                    revision.project_id, revision.scene_revision_id, item.shot_id, item.take_id
                )
                self._validate_current_authority(shot, window, pin)
                if (window.source_range != shot.source_range
                        or window.source_timebase != scene.source.timebase
                        or window.timeline_timebase != revision.timebase
                        or take.output.timebase != revision.timebase):
                    raise ValidationError("qualified replay window does not match the frozen shot")
                offset = item.source_range.start - shot.source_range.start
                if item.decoder_keep is None:
                    start = window.decoder_keep.start + offset
                    end = start + item.source_range.end - item.source_range.start
                else:
                    start, end = item.decoder_keep.start, item.decoder_keep.end
                expected_end = window.decoder_keep.start + offset + item.source_range.end - item.source_range.start
                if (end - start != item.timeline_range.end - item.timeline_range.start
                        or start < window.decoder_keep.start
                        or end > window.decoder_keep.end or end != expected_end):
                    raise DecoderKeepMismatchError(
                        "decoder keep must be the exact source interval after synthetic padding removal"
                    )
                output = self._store.resolve_asset(take.output.asset_id)
                candidate = _video_facts(output.path)
                if (take.output.frame_count != window.expected_decoder_frames
                        or candidate[0] != window.expected_decoder_frames
                        or candidate[1] != window.render_timebase
                        or candidate[2] != window.render_range.start):
                    raise ValidationError("replay take decoder frame count drifted")
                slices.append(_MediaSlice(
                    output.path, take.output.asset_id, take.output.sha256,
                    "retained_replay", start, end,
                ))
                authorities.append({
                    "shot_id": item.shot_id, "qualification_id": window.qualification_id,
                    "qualification_scope": (
                        "qualified_zero_pad_offline_cpu; not n_minus_one, nonzero_pad, "
                        "general_h3, or promoted_historical_keeper"
                    ),
                    "recipe_id": pin.recipe_id, "recipe_version": pin.version,
                    "raw_graph_sha256": pin.raw_graph_sha256,
                    "padding_removed": window.pad_left + window.pad_right,
                    "decoder_keep": {"start": start, "end": end},
                })
            cursor = item.timeline_range.end
        if cursor <= 0:
            raise TimelineNotContiguousError("edit timeline is empty")
        return _ManagedPlan(scene, source_path, tuple(slices), tuple(authorities))

    def export_revision(self, revision_id: str) -> ExportRecord:
        revision = self._store.get_edit_revision_by_id(revision_id)
        plan = self._media_plan(revision)
        evidence, checks = _assemble_plan(self._store, revision, plan)
        record = ExportRecord(
            "pending", revision.id, "completed", evidence.asset_id, evidence.sha256,
            json.dumps(checks, sort_keys=True, separators=(",", ":")),
        )
        return self._store.complete_export(record)
