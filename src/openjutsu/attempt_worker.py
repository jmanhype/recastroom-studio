# SPDX-License-Identifier: MIT
"""The sole managed worker for durable attempts; no provider transport is enabled."""
from __future__ import annotations

from fractions import Fraction
from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from typing import Sequence
import uuid

from .managed_adapters import AdapterRegistry, CPUManagedAdapter, ManagedAdapter
from .m1_types import (
    AttemptEvent, AttemptRecord, AttemptState, ExecutionMode, Fence, OutputEvidence,
    Receipt, RemoteState, ResolvedOperation,
)
from .take_service import TakeService
from .workspace_store import AttemptConflictError, WorkspaceStore
from tools.foundation_runtime import FFMPEG, FFPROBE


_TOOL_ENV = {"PATH": str(FFMPEG.parent)}


def cpu_adapters(store: WorkspaceStore) -> AdapterRegistry:
    return {ExecutionMode.DRY_RUN: CPUManagedAdapter(store)}


def _pending(store: WorkspaceStore) -> bool:
    for project in store.list_projects():
        for attempt in store.list_attempts(project.project_id):
            with store._connect() as db:
                controls = dict(db.execute("SELECT kind, MAX(sequence) FROM attempt_events "
                    "WHERE attempt_id=? AND kind IN ('cancel_intent','reconcile_intent','reconcile_paused') "
                    "GROUP BY kind", (attempt.id,)).fetchall())
            paused = controls.get("reconcile_paused", -1)
            if paused >= 0 and paused >= max(controls.get("cancel_intent", -1),
                                             controls.get("reconcile_intent", -1)):
                continue
            if attempt.provider_id is None and (attempt.state == AttemptState.CANCEL_REQUESTED or
                    (attempt.state == AttemptState.RECONCILE_NEEDED and
                     controls.get("cancel_intent", -1) <= paused)):
                continue
            if attempt.state in {AttemptState.PREPARED, AttemptState.READY, AttemptState.SUBMITTING,
                                 AttemptState.SUBMITTED, AttemptState.RUNNING,
                                 AttemptState.DOWNLOADING, AttemptState.CANCEL_REQUESTED}:
                return True
            if attempt.state == AttemptState.RECONCILE_NEEDED:
                return True
    return False


def _transition(store: WorkspaceStore, fence: Fence, state: AttemptState,
                target: AttemptState, payload: dict[str, object] | None = None) -> AttemptRecord:
    return store.transition_attempt(fence, state, AttemptEvent(
        target.value, json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))))


def _run_tool(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(FFMPEG) if arguments[0] == "ffmpeg" else str(FFPROBE), *arguments[1:]],
        check=True, capture_output=True, text=True, timeout=30, env=_TOOL_ENV)


def _run_raw(arguments: Sequence[str]) -> bytes:
    return subprocess.run([str(FFMPEG) if arguments[0] == "ffmpeg" else str(FFPROBE), *arguments[1:]],
        check=True, capture_output=True, timeout=30, env=_TOOL_ENV).stdout


def _raw_pixels(path: Path, start: int, end: int) -> bytes:
    expression = f"select='between(n\\,{start}\\,{end - 1})'"
    return _run_raw([
        "ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-vf", expression,
        "-fps_mode", "passthrough", "-map", "0:v:0", "-f", "rawvideo",
        "-pix_fmt", "bgr24", "pipe:1",
    ])


def _verify_inputs(store: WorkspaceStore, operation: ResolvedOperation) -> dict[str, object]:
    scene = store.get_scene_revision(operation.project_id, operation.scene_revision_id)
    character = store.get_character_version(*operation.character_version)
    binding = store.verify_preparation_binding(
        operation.project_id, operation.id, operation.fingerprint,
        source_asset_id=scene.source.asset_id,
        reference_asset_ids=tuple(character.reference_asset_ids),
    )
    envelope = json.loads(store.resolve_asset(binding.binding_asset_id).path.read_bytes())
    cpu = envelope.get("cpu_input")
    ranges = (operation.window.source_range.start, operation.window.source_range.end,
              operation.window.render_range.start, operation.window.render_range.end)
    if (not isinstance(cpu, dict) or cpu.get("original_range") != list(ranges[:2])
            or cpu.get("render_range") != list(ranges[2:])):
        raise ValueError("authenticated CPU input range mismatch")
    return envelope


def _validate_output(store: WorkspaceStore, operation: ResolvedOperation,
                     evidence: OutputEvidence, envelope: dict[str, object]) -> str | None:
    cpu = envelope["cpu_input"]
    concrete = store.resolve_asset(str(cpu["asset_id"])).record
    if evidence.sha256 != concrete.sha256:
        return "output_hash"
    output = store.resolve_asset(evidence.asset_id).path
    source = store.resolve_asset(store.get_scene_revision(
        operation.project_id, operation.scene_revision_id).source.asset_id).path
    start, end = operation.window.source_range.start, operation.window.source_range.end
    try:
        probe = json.loads(_run_tool([
            "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries", "stream=nb_read_frames,time_base,width,height:frame=pts_time,duration",
            "-of", "json", str(output),
        ]).stdout)
        stream = probe["streams"][0]
        frames = probe["frames"]
        count = end - start
        expected_bytes = int(stream["width"]) * int(stream["height"]) * 3 * count
        rendered = _raw_pixels(output, 0, count)
        original = _raw_pixels(source, start, end)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
        return "output_bytes"
    if len(frames) != count or int(stream["nb_read_frames"]) != count or len(rendered) != expected_bytes:
        return "output_frames"
    period = Fraction(1, 24)
    for index, frame in enumerate(frames):
        try:
            if (abs(float(frame["pts_time"]) - index * period) > 1 / 1000
                    or abs(float(frame["duration"]) * Fraction(str(stream["time_base"])) - period) > Fraction(1, 1000)):
                return "output_pts"
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            return "output_bytes"
    if hashlib.sha256(rendered).digest() != hashlib.sha256(original).digest():
        return "output_pixels"
    return None


def _reject_output(store: WorkspaceStore, fence: Fence, state: AttemptState,
                   receipt: Receipt, evidence: OutputEvidence, reason: str) -> None:
    payload: dict[str, object] = {"reason": reason, "receipt_sha256": receipt.receipt_sha256}
    if reason.startswith("output_"):
        payload.update(asset_id=evidence.asset_id, sha256=evidence.sha256)
    _transition(store, fence, state, AttemptState.FAILED, payload)


def _observe_remote(store: WorkspaceStore, fence: Fence, adapter: ManagedAdapter,
                    attempt: AttemptRecord, receipt: Receipt) -> AttemptRecord:
    remote = adapter.poll(receipt)
    if remote == RemoteState.COMPLETED:
        state = attempt.state
        if state == AttemptState.SUBMITTED:
            state = _transition(store, fence, state, AttemptState.RUNNING).state
        if state == AttemptState.RUNNING:
            state = _transition(store, fence, state, AttemptState.DOWNLOADING).state
        if state in {AttemptState.RECONCILE_NEEDED}:
            state = _transition(store, fence, state, AttemptState.DOWNLOADING).state
        if state == AttemptState.CANCEL_REQUESTED:
            state = _transition(store, fence, state, AttemptState.DOWNLOADING,
                {"remote_state": "completed", "receipt_sha256": receipt.receipt_sha256}).state
            store.apply_cancel_intent(fence)
        return store._lookup_attempt(attempt.id)
    if remote == RemoteState.FAILED:
        return _transition(store, fence, attempt.state, AttemptState.FAILED,
            {"reason": "remote_failed", "receipt_sha256": receipt.receipt_sha256})
    if remote == RemoteState.CANCELLED and attempt.state == AttemptState.CANCEL_REQUESTED:
        cancellation = adapter.cancel(receipt)
        if cancellation.supported and cancellation.confirmed and attempt.state == AttemptState.CANCEL_REQUESTED:
            return _transition(store, fence, attempt.state,
                AttemptState.PROVIDER_CONFIRMED_CANCELLED, {"supported": True, "confirmed": True})
    if remote == RemoteState.UNKNOWN or remote == RemoteState.CANCELLED or attempt.state == AttemptState.DOWNLOADING:
        paused = attempt
        if attempt.state in {AttemptState.SUBMITTED, AttemptState.RUNNING, AttemptState.DOWNLOADING}:
            paused = _transition(store, fence, attempt.state, AttemptState.RECONCILE_NEEDED)
        _pause_reconcile(store, fence, paused)
        return paused
    return attempt


def _pause_reconcile(store: WorkspaceStore, fence: Fence, attempt: AttemptRecord) -> None:
    with store._transaction() as db:
        store._fenced(db, fence, attempt.state)
        store._event(db, attempt.id, "reconcile_paused", {})


def _advance(store: WorkspaceStore, adapters: AdapterRegistry, owner: str, epoch: int) -> bool:
    fence = store._next_attempt(owner, continuation=True)
    if fence is None or fence.epoch != epoch:
        return False
    try:
        return _advance_claimed(store, adapters, fence)
    except Exception:
        # An interrupted boundary is uncertainty, never retry permission. Keep
        # independent work runnable, but a stale fence must still fail closed.
        attempt = store._lookup_attempt(fence.attempt_id)
        if attempt.state in {AttemptState.PREPARED, AttemptState.READY}:
            _transition(store, fence, attempt.state, AttemptState.FAILED)
        else:
            if attempt.state in {AttemptState.SUBMITTING, AttemptState.SUBMITTED,
                                 AttemptState.RUNNING, AttemptState.DOWNLOADING}:
                attempt = _transition(store, fence, attempt.state, AttemptState.RECONCILE_NEEDED)
            _pause_reconcile(store, fence, attempt)
        return True


def _advance_claimed(store: WorkspaceStore, adapters: AdapterRegistry, fence: Fence) -> bool:
    attempt = store.apply_cancel_intent(fence)
    if attempt.state in {AttemptState.COMPLETED, AttemptState.FAILED,
                         AttemptState.PROVIDER_CONFIRMED_CANCELLED}:
        return True
    if attempt.state in {AttemptState.RECONCILE_NEEDED, AttemptState.CANCEL_REQUESTED}:
        if attempt.provider_id is None:
            _pause_reconcile(store, fence, attempt)
            return True
        receipt = store._receipt(attempt)
        operation = store.get_operation(attempt.project_id, attempt.operation_id)
        adapter = adapters[attempt.mode]
        if not adapter.preflight(operation).ready:
            _pause_reconcile(store, fence, attempt)
            return True
        _verify_inputs(store, operation)
        if isinstance(adapter, CPUManagedAdapter):
            adapter.resume(fence)
        if attempt.state == AttemptState.CANCEL_REQUESTED:
            cancellation = adapter.cancel(receipt)
            if cancellation.supported and cancellation.confirmed:
                _transition(store, fence, attempt.state,
                            AttemptState.PROVIDER_CONFIRMED_CANCELLED,
                            {"supported": True, "confirmed": True})
                return True
        attempt = _observe_remote(store, fence, adapter, attempt, receipt)
        if attempt.state != AttemptState.DOWNLOADING:
            return True
    else:
        operation = store.get_operation(attempt.project_id, attempt.operation_id)
        adapter = adapters.get(attempt.mode)
        if adapter is None:
            if attempt.state == AttemptState.PREPARED:
                _transition(store, fence, attempt.state, AttemptState.FAILED)
            return True
        if not adapter.preflight(operation).ready:
            if attempt.state in {AttemptState.PREPARED, AttemptState.READY}:
                _transition(store, fence, attempt.state, AttemptState.FAILED)
            return True
        envelope = _verify_inputs(store, operation)
        if attempt.state == AttemptState.PREPARED:
            attempt = _transition(store, fence, attempt.state, AttemptState.READY)
        if attempt.state == AttemptState.READY:
            attempt = store.apply_cancel_intent(fence)
            if attempt.state != AttemptState.READY:
                return True
            attempt = _transition(store, fence, attempt.state, AttemptState.SUBMITTING)
        if attempt.state != AttemptState.SUBMITTING:
            receipt = store._receipt(attempt)
            if isinstance(adapter, CPUManagedAdapter):
                adapter.resume(fence)
            attempt = _observe_remote(store, fence, adapter, attempt, receipt)
            if attempt.state != AttemptState.DOWNLOADING:
                return True
        else:
            bound = adapter.bind(operation, fence)
            receipt = adapter.submit(bound, attempt.client_request_id)
            attempt = store.record_receipt(fence, receipt)
            attempt = store.apply_cancel_intent(fence)
            attempt = _observe_remote(store, fence, adapter, attempt, receipt)
            if attempt.state != AttemptState.DOWNLOADING:
                return True
    evidence = adapter.download(store._receipt(attempt))
    operation = store.get_operation(attempt.project_id, attempt.operation_id)
    envelope = _verify_inputs(store, operation)
    reason = _validate_output(store, operation, evidence, envelope)
    if reason is not None:
        _reject_output(store, fence, AttemptState.DOWNLOADING,
                       store._receipt(attempt), evidence, reason)
        return True
    with store._transaction() as db:
        store._fenced(db, fence, AttemptState.DOWNLOADING)
        previous = db.execute("SELECT payload_json FROM attempt_events WHERE attempt_id=? "
                              "AND kind='output'", (attempt.id,)).fetchone()
        if previous and OutputEvidence.from_json(previous[0]) != evidence:
            raise AttemptConflictError("IMMUTABLE_OUTPUT_CONFLICT")
        if previous is None:
            store._event(db, attempt.id, "output", json.loads(evidence.to_json()))
    if store.apply_cancel_intent(fence).state != AttemptState.DOWNLOADING:
        return True
    TakeService(store).register_output(attempt.id, evidence)
    return True


def run_once(store: WorkspaceStore, adapters: AdapterRegistry) -> bool:
    """Advance one attempt under either a caller-owned lifetime or a fresh flock."""
    if not isinstance(store, WorkspaceStore) or not isinstance(adapters, Mapping):
        raise TypeError("active WorkspaceStore and adapter registry required")
    if not _pending(store):
        return False
    identity = store._worker_identity
    if identity is not None:
        if identity[2:] != (os.getpid(), threading.get_ident()):
            raise AttemptConflictError("STALE_FENCE")
        return _advance(store, adapters, identity[0], identity[1])
    owner = "worker-" + uuid.uuid4().hex
    try:
        with store.worker_lock(owner) as epoch:
            return _advance(store, adapters, owner, epoch)
    except AttemptConflictError as error:
        if str(error) == "WORKER_BUSY":
            return False
        raise


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print("usage: python -m openjutsu.attempt_worker WORKSPACE_ROOT", file=sys.stderr)
        return 2
    store = WorkspaceStore(Path(arguments[0]))
    if not _pending(store):
        return 0
    try:
        with store.worker_lock("cli-worker"):
            while run_once(store, cpu_adapters(store)):
                continue
    except AttemptConflictError as error:
        if str(error) != "WORKER_BUSY":
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
