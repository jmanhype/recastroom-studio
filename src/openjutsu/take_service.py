# SPDX-License-Identifier: MIT
"""Typed take registration over the active workspace store."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any, BinaryIO
import uuid

from .m1_types import (
    Fence, OutputEvidence, ReplayReceipt, ReviewRecord, ReviewVerdict,
    SelectionRecord, TakeRecord, Timebase,
    WindowMap,
)
from .pipeline import _effective_workflow
from .recipe_service import WORKFLOW_PATH
from .workspace_store import AttemptConflictError, ValidationError, WorkspaceStore


class TakeService:
    """Register protected output without creating a second lineage authority."""

    def __init__(self, store: WorkspaceStore) -> None:
        if not isinstance(store, WorkspaceStore):
            raise TypeError("active WorkspaceStore required")
        self._store = store

    def register_output(self, attempt_id: str, evidence: OutputEvidence) -> TakeRecord:
        identity = self._store._worker_identity
        if identity is None:
            raise AttemptConflictError("WORKER_LOCK_REQUIRED")
        attempt = self._store._lookup_attempt(attempt_id)
        with self._store._connect() as db:
            claim = db.execute(
                "SELECT payload_json FROM attempt_events WHERE attempt_id=? AND kind='claimed' "
                "ORDER BY sequence DESC LIMIT 1", (attempt.id,)
            ).fetchone()
        if claim is None or json.loads(claim[0]) != {"owner_id": identity[0], "epoch": identity[1]}:
            raise AttemptConflictError("STALE_FENCE")
        return self._store.register_take(Fence(attempt.id, identity[0], identity[1]), evidence)

    @staticmethod
    def _probe(path: Path) -> tuple[int, Timebase, int, Fraction]:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
             "-show_entries", "stream=nb_read_frames,time_base,start_time:"
             "frame=pts,duration", "-of", "json", str(path)],
            check=True, capture_output=True, text=True, timeout=30,
        )
        stream = json.loads(result.stdout)["streams"][0]
        count = int(stream["nb_read_frames"])
        frames = json.loads(result.stdout).get("frames", [])
        if len(frames) != count:
            raise ValidationError("decoded frame metadata count does not match measured frames")
        try:
            ticks = Fraction(str(stream["time_base"]))
            first_pts = int(frames[0]["pts"])
            duration = int(frames[0]["duration"])
            if duration <= 0 or any(int(frame.get("duration", 0)) != duration for frame in frames):
                raise ValidationError("decoded frame durations are irregular")
            if any(int(frame.get("pts", -1)) != first_pts + index * duration
                   for index, frame in enumerate(frames)):
                raise ValidationError("decoded frame PTS sequence is irregular")
            if "start_time" in stream:
                started = Fraction(str(stream["start_time"]))
                # ffprobe prints start_time to six fractional digits; permit only
                # that display rounding, never a different decoded PTS origin.
                if abs(started - first_pts * ticks) > Fraction(1, 2_000_000):
                    raise ValidationError("decoded stream start time does not match first PTS")
            period = duration * ticks
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
            raise ValidationError("decoded frame timing metadata is malformed") from error
        return count, Timebase(period.numerator, period.denominator), first_pts, ticks

    @staticmethod
    def _validated_window(window: Any) -> Any:
        """Validate typed decoder geometry without normalizing or repairing it."""
        if not isinstance(window, WindowMap):
            raise ValidationError("replay window must be a typed WindowMap")
        if (window.decoder_keep.start < 0
                or window.decoder_keep.end > window.expected_decoder_frames):
            raise ValidationError("typed replay decoder window geometry is invalid")
        return window

    @staticmethod
    def _validated_current_cpu_window(
        store: WorkspaceStore, shot: Any, window: WindowMap, *, pin: Any = None
    ) -> None:
        """Revalidate the only qualified M1 CPU mapping from its existing authority."""
        from .recipe_service import OFFLINE_PIN
        from .scene_service import SceneService
        if pin is not None and pin != OFFLINE_PIN:
            raise ValidationError(
                "EVIDENCE_UNAVAILABLE: no authenticated qualified window mapping "
                "supports this replay"
            )
        qualified = SceneService(store).validate_window(shot, OFFLINE_PIN)
        if qualified != window:
            raise ValidationError(
                "EVIDENCE_UNAVAILABLE: no authenticated qualified window mapping "
                "supports this replay"
            )

    def _candidate_bindings(
        self, project_id: str, receipt: ReplayReceipt
    ) -> list[tuple[Any, str]]:
        if not isinstance(receipt, ReplayReceipt):
            raise ValidationError("replay receipt must be a typed ReplayReceipt")
        candidates: list[tuple[Any, str]] = []
        with self._store._connect() as db:
            rows = db.execute(
                """SELECT p.* FROM preparation_bindings p JOIN operations o USING(operation_id)
                   WHERE o.project_id=? AND o.scene_revision_id=? AND o.shot_id=?
                   ORDER BY o.operation_id""",
                (project_id, receipt.scene_revision_id, receipt.shot_id),
            ).fetchall()
            scene_row = db.execute(
                "SELECT project_id,source_asset_id FROM scene_revisions WHERE scene_revision_id=?",
                (receipt.scene_revision_id,),
            ).fetchone()
        if scene_row is None or scene_row["project_id"] != project_id:
            raise ValidationError("replay receipt scene does not match the project")
        if not rows:
            raise ValidationError(
                "EVIDENCE_UNAVAILABLE: no authenticated M1 historical-input verifier is available"
            )
        for row in rows:
            operation = self._store.get_operation(project_id, row["operation_id"])
            manifest = json.loads(operation.canonical_json)
            receipt_subset = (
                operation.window == receipt.window,
                operation.pin.recipe_id == receipt.recipe_id,
                operation.pin.version == receipt.recipe_version,
                operation.pin.raw_graph_sha256 == receipt.raw_graph_sha256,
                manifest["source"]["sha256"] == receipt.source_sha256,
                manifest["source"]["proxy_sha256"] == receipt.input_sha256,
                manifest["graph"]["raw_sha256"] == receipt.raw_graph_sha256,
                manifest["graph"]["resolved_semantic_sha256"] == receipt.resolved_graph_sha256,
            )
            if not all(receipt_subset):
                # Prepared variants outside the receipt's pinned byte/window subset
                # are unrelated history, not evidence that this receipt is ambiguous.
                continue
            current_scene = self._store.get_scene_revision(project_id, receipt.scene_revision_id)
            current_shot = next(
                (item for item in current_scene.shots if item.id == operation.shot_id), None
            )
            if current_shot is None:
                raise ValidationError("EVIDENCE_UNAVAILABLE: replay shot lacks scene authority")
            self._validated_current_cpu_window(
                self._store, current_shot, receipt.window, pin=operation.pin
            )
            self._store._revalidate_binding(row)
            source_bytes = self._store.resolve_asset(str(row["source_asset_id"])).path.read_bytes()
            input_bytes = self._store.resolve_asset(str(row["cpu_input_asset_id"])).path.read_bytes()
            graph_payload = json.loads(
                self._store.resolve_asset(str(row["graph_asset_id"])).path.read_bytes()
            )
            graph_bytes = self._store.resolve_asset(str(row["graph_asset_id"])).path.read_bytes()
            raw_bytes = WORKFLOW_PATH.read_bytes()
            actual_semantic = hashlib.sha256(json.dumps(
                _effective_workflow(graph_payload), sort_keys=True, separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")).hexdigest()
            checks = (
                hashlib.sha256(source_bytes).hexdigest() == receipt.source_sha256,
                hashlib.sha256(input_bytes).hexdigest() == receipt.input_sha256,
                hashlib.sha256(raw_bytes).hexdigest() == receipt.raw_graph_sha256,
                actual_semantic == receipt.resolved_graph_sha256,
                actual_semantic == manifest["graph"]["resolved_semantic_sha256"],
                hashlib.sha256(graph_bytes).hexdigest() == str(row["graph_sha256"]),
                operation.window == receipt.window,
                operation.pin.recipe_id == receipt.recipe_id,
                operation.pin.version == receipt.recipe_version,
                operation.pin.raw_graph_sha256 == receipt.raw_graph_sha256,
                manifest["source"]["sha256"] == receipt.source_sha256,
                manifest["source"]["proxy_sha256"] == receipt.input_sha256,
            )
            if not all(checks):
                raise ValidationError(
                    "EVIDENCE_AMBIGUOUS: trusted operation provenance does not match the receipt"
                )
            source_path = self._store.resolve_asset(str(row["source_asset_id"])).path
            input_path = self._store.resolve_asset(str(row["cpu_input_asset_id"])).path
            source_count, source_time, source_pts, _source_ticks = self._probe(source_path)
            input_count, input_time, input_pts, input_ticks = self._probe(input_path)
            expected_input_start = receipt.window.render_range.start * Fraction(
                input_time.num, input_time.den
            )
            if (source_pts != 0
                    or input_pts * input_ticks != expected_input_start
                    or source_count != self._store.get_scene_revision(
                    project_id, receipt.scene_revision_id).source.frame_count
                    or source_time != receipt.window.source_timebase
                    or input_count != receipt.window.expected_decoder_frames
                    or input_time != receipt.window.render_timebase):
                raise ValidationError("trusted decoder window, timing, or frame count mismatch")
            self._validated_window(receipt.window)
            # public_json is the normalized semantic projection: concrete IDs,
            # staging paths, job IDs, timestamps, and output prefixes are excluded.
            candidates.append((row, operation.canonical_json.rstrip() + "\n"))
        return candidates

    def import_replay(
        self, project_id: str, receipt: ReplayReceipt, content: BinaryIO
    ) -> TakeRecord:
        """Import verified retained bytes without execution or provider provenance."""
        if not callable(getattr(content, "read", None)):
            raise ValidationError("replay content must be a binary file object")
        candidates = self._candidate_bindings(project_id, receipt)
        self._validated_window(receipt.window)
        semantic_classes = {candidate[1] for candidate in candidates}
        if len(semantic_classes) != 1:
            raise ValidationError("EVIDENCE_AMBIGUOUS: operations have distinct effective provenance")
        output = content.read()
        if not isinstance(output, bytes) or not output:
            raise ValidationError("replay output content is required")
        content.seek(0)
        digest = hashlib.sha256(output).hexdigest()
        if digest != receipt.output_sha256:
            raise ValidationError("replay output byte hash mismatch")
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(prefix="replay-", suffix=".nut", delete=False) as temporary:
                temporary.write(output)
                temporary_name = temporary.name
            count, timebase, first_pts, stream_ticks = self._probe(Path(temporary_name))
            expected_start = receipt.window.render_range.start * Fraction(
                timebase.num, timebase.den
            )
            if (count != receipt.window.expected_decoder_frames
                    or timebase != receipt.window.render_timebase
                    or first_pts * stream_ticks != expected_start):
                raise ValidationError("replay output decoder frame count or timing mismatch")
        finally:
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)
        operation_id = min(str(row["operation_id"]) for row, _class in candidates)
        return self._store._atomic_replay_import(
            project_id, receipt, content, frame_count=count, timebase=timebase,
            operation_id=operation_id,
        )

    def import_unqualified(
        self,
        project_id: str,
        shot_id: str,
        historical_metadata: None,
        content: BinaryIO,
    ) -> TakeRecord:
        """Import explicitly unattached bytes; only literal None metadata is accepted."""
        if historical_metadata is not None:
            raise ValidationError("historical_metadata must be literal None")
        if not callable(getattr(content, "read", None)):
            raise ValidationError("unqualified content must be a binary file object")
        candidate = content.read()
        if not isinstance(candidate, bytes) or not candidate:
            raise ValidationError("unqualified media content is required")
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(prefix="unqualified-", suffix=".nut", delete=False) as temporary:
                temporary.write(candidate)
                temporary_name = temporary.name
            frame_count, timebase, _first_pts, _stream_ticks = self._probe(Path(temporary_name))
        finally:
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)
        content.seek(0)
        return self._store._atomic_unqualified_import(
            project_id, shot_id, content, frame_count=frame_count, timebase=timebase
        )

    def review(
        self, take_id: str, verdict: ReviewVerdict, note: str
    ) -> ReviewRecord:
        record = ReviewRecord("review-" + uuid.uuid4().hex, take_id, verdict, note)
        return self._store.append_review(record)

    def select(
        self,
        project_id: str,
        scene_revision_id: str,
        shot_id: str,
        take_id: str | None,
        expected_revision: int,
    ) -> SelectionRecord:
        return self._store.select_take(
            project_id, scene_revision_id, shot_id, take_id, expected_revision
        )
