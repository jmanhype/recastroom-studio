# SPDX-License-Identifier: MIT
"""Fenced CPU-only managed adapter. No provider/GPU transport is enabled.

CPU bind/upload/submit cost is zero; the conservative SUBMITTING boundary still
precedes bind. H3/Comfy/SDK are OWNER_BLOCKED, not fake successful transports.
Output is exact retained CPU input, not H3 generation or a qualified creative take.
"""
from __future__ import annotations

import io
import json
from typing import Mapping, Protocol
from functools import wraps

from .m1_types import (AttemptEvent, AttemptState, BoundSubmission, CancelResult, ExecutionMode, Fence,
    OutputEvidence, Readiness, Receipt, RemoteState, ResolvedOperation, Timebase)
from .recipe_service import OFFLINE_PIN, OFFLINE_SOURCE_SHA256, OFFLINE_REFERENCE_SHA256
from .workspace_store import AssetIntegrityError, AttemptConflictError, ValidationError, WorkspaceStore


class ManagedAdapter(Protocol):
    """Split transport boundaries; implementations never submit inside poll/download."""
    def preflight(self, op: ResolvedOperation) -> Readiness: ...
    def bind(self, op: ResolvedOperation, fence: Fence) -> BoundSubmission: ...
    def submit(self, bound: BoundSubmission, request_key: str) -> Receipt: ...
    def poll(self, receipt: Receipt) -> RemoteState: ...
    def download(self, receipt: Receipt) -> OutputEvidence: ...
    def cancel(self, receipt: Receipt) -> CancelResult: ...


AdapterRegistry = Mapping[ExecutionMode, ManagedAdapter]


def _uncertain_boundary(method):
    """A failed boundary never grants retry permission, including process interruption."""
    @wraps(method)
    def invoke(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except BaseException:
            if self._fence is not None:
                attempt = self._store._lookup_attempt(self._fence.attempt_id)
                if attempt.state == AttemptState.SUBMITTING:
                    self._store.transition_attempt(self._fence, attempt.state, AttemptEvent("reconcile_needed", "{}"))
            raise
    return invoke


class CPUManagedAdapter:
    """One attempt per adapter instance; retain its fence only inside worker_lock."""

    def __init__(self, store: WorkspaceStore) -> None:
        self._store = store
        self._fence: Fence | None = None

    def preflight(self, op: ResolvedOperation) -> Readiness:
        if op.pin != OFFLINE_PIN:
            return Readiness(False, "OWNER_BLOCKED", "Provider qualification requires owner approval.")
        current = self._store.get_operation(op.project_id, op.id)
        manifest = json.loads(op.canonical_json)
        if (current != op or manifest["source"]["sha256"] != OFFLINE_SOURCE_SHA256
                or tuple(manifest["character"]["reference_hashes"]) != OFFLINE_REFERENCE_SHA256
                or (op.window.source_range.start, op.window.source_range.end) not in
                {(0, 24), (0, 8), (8, 16), (16, 24)}):
            raise ValidationError("CPU_PROFILE_MISMATCH")
        return Readiness(True, "CPU_NON_INFERENCE", "Zero cost; CPU source routing only, not H3 generation.")

    def _guard(self, fence: Fence, state: AttemptState, *, cancel_blocks: bool = False) -> None:
        with self._store._transaction() as db:
            attempt = self._store._fenced(db, fence, state)
            if attempt.mode != ExecutionMode.DRY_RUN:
                raise AttemptConflictError("OWNER_BLOCKED")
            if cancel_blocks and db.execute("SELECT 1 FROM attempt_events WHERE attempt_id=? AND kind='cancel_intent'",
                                           (attempt.id,)).fetchone():
                raise AttemptConflictError("CANCEL_PENDING")

    def _mark_once(self, kind: str) -> None:
        fence = self._fence
        if fence is None:
            raise AttemptConflictError("BIND_REQUIRED")
        self._guard(fence, AttemptState.SUBMITTING, cancel_blocks=True)
        with self._store._transaction() as db:
            self._store._fenced(db, fence, AttemptState.SUBMITTING)
            if db.execute("SELECT 1 FROM attempt_events WHERE attempt_id=? AND kind='cancel_intent'",
                          (fence.attempt_id,)).fetchone():
                raise AttemptConflictError("CANCEL_PENDING")
            if db.execute("SELECT 1 FROM attempt_events WHERE attempt_id=? AND kind=?",
                          (fence.attempt_id, kind)).fetchone():
                raise AttemptConflictError("OUTCOME_UNKNOWN_RECONCILE_REQUIRED")
            self._store._event(db, fence.attempt_id, kind, {})

    @_uncertain_boundary
    def bind(self, op: ResolvedOperation, fence: Fence) -> BoundSubmission:
        # This exact accepted producer interface is the FIRST binding operation.
        scene = self._store.get_scene_revision(op.project_id, op.scene_revision_id)
        character = self._store.get_character_version(*op.character_version)
        prepared = self._store.verify_preparation_binding(op.project_id, op.id, op.fingerprint,
            source_asset_id=scene.source.asset_id, reference_asset_ids=tuple(character.reference_asset_ids))
        if not self.preflight(op).ready:
            raise AttemptConflictError("OWNER_BLOCKED")
        self._guard(fence, AttemptState.SUBMITTING, cancel_blocks=True)
        attempt = self._store.get_attempt(op.project_id, fence.attempt_id)
        if attempt.operation_id != op.id:
            raise AttemptConflictError("BINDING_OWNERSHIP_MISMATCH")
        self._fence = fence
        self._mark_once("bind_started")
        envelope = json.loads(self._store.resolve_asset(prepared.binding_asset_id).path.read_bytes())
        # No substitutions in the CPU lane. Exact concrete graph bytes remain
        # protected independently of the normalized semantic graph digest.
        content = {"attempt_id": attempt.id, "preparation": json.loads(prepared.to_json()),
                   "envelope": envelope, "binding_cost": "zero", "upload_cost": "zero"}
        staged = self._store.stage_asset(op.project_id, "attempt-binding.json",
            io.BytesIO(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()),
            role="attempt_binding", protected=True)
        bound = BoundSubmission(op.id, staged.asset_id, staged.sha256, False)
        with self._store._transaction() as db:
            self._store._fenced(db, fence, AttemptState.SUBMITTING)
            self._store._event(db, attempt.id, "bound", json.loads(bound.to_json()))
        return bound

    def _bound(self, bound: BoundSubmission) -> dict:
        if self._fence is None:
            raise AttemptConflictError("BIND_REQUIRED")
        attempt = self._store._lookup_attempt(self._fence.attempt_id)
        self._store._protected_binding_asset(attempt.project_id, bound.binding_asset_id,
                                            bound.binding_sha256, {"attempt_binding"})
        with self._store._connect() as db:
            row = db.execute("SELECT payload_json FROM attempt_events WHERE attempt_id=? AND kind='bound'",
                             (attempt.id,)).fetchone()
        if row is None or BoundSubmission.from_json(row[0]) != bound:
            raise ValidationError("IMMUTABLE_BINDING_MISMATCH")
        content = json.loads(self._store.resolve_asset(bound.binding_asset_id).path.read_bytes())
        op = self._store.get_operation(attempt.project_id, attempt.operation_id)
        scene = self._store.get_scene_revision(op.project_id, op.scene_revision_id)
        character = self._store.get_character_version(*op.character_version)
        preparation = self._store.verify_preparation_binding(op.project_id, op.id, op.fingerprint,
            source_asset_id=scene.source.asset_id, reference_asset_ids=tuple(character.reference_asset_ids))
        envelope = json.loads(self._store.resolve_asset(preparation.binding_asset_id).path.read_bytes())
        if content != {"attempt_id": attempt.id, "preparation": json.loads(preparation.to_json()),
                       "envelope": envelope, "binding_cost": "zero", "upload_cost": "zero"}:
            raise ValidationError("CONCRETE_BINDING_MISMATCH")
        return envelope

    @_uncertain_boundary
    def submit(self, bound: BoundSubmission, request_key: str) -> Receipt:
        self._bound(bound)
        attempt = self._store._lookup_attempt(self._fence.attempt_id)
        if request_key != attempt.client_request_id:
            raise ValidationError("REQUEST_KEY_MISMATCH")
        self._mark_once("submit_started")
        op = self._store.get_operation(attempt.project_id, attempt.operation_id)
        provider_id = "cpu-" + attempt.id
        body = {"attempt_id": attempt.id, "provider_id": provider_id, "request_key": request_key,
                "adapter_version": op.pin.adapter_version, "endpoint_fingerprint": op.pin.endpoint_fingerprint}
        asset = self._store.stage_asset(attempt.project_id, "cpu-receipt.json",
            io.BytesIO(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()),
            role="provider_receipt", protected=True)
        receipt = Receipt(attempt.id, provider_id, request_key, op.pin.adapter_version,
                          op.pin.endpoint_fingerprint, asset.asset_id, asset.sha256)
        self._store.record_receipt(self._fence, receipt)  # before any waiting/poll
        return receipt

    def _check_receipt(self, receipt: Receipt) -> None:
        attempt = self._store._lookup_attempt(receipt.attempt_id)
        if self._fence is None or self._fence.attempt_id != attempt.id:
            raise AttemptConflictError("FENCE_REQUIRED")
        self._guard(self._fence, attempt.state)
        if attempt.mode != ExecutionMode.DRY_RUN or self._store._receipt(attempt) != receipt:
            raise ValidationError("IMMUTABLE_RECEIPT_MISMATCH")

    def poll(self, receipt: Receipt) -> RemoteState:
        self._check_receipt(receipt)
        return RemoteState.COMPLETED  # local routing, no generation or network call

    def download(self, receipt: Receipt) -> OutputEvidence:
        self._check_receipt(receipt)
        if self._fence is None or self._fence.attempt_id != receipt.attempt_id:
            raise AttemptConflictError("FENCE_REQUIRED")
        self._guard(self._fence, AttemptState.DOWNLOADING)
        attempt = self._store._lookup_attempt(receipt.attempt_id)
        with self._store._connect() as db:
            row = db.execute("SELECT payload_json FROM attempt_events WHERE attempt_id=? AND kind='bound'",
                             (attempt.id,)).fetchone()
            output = db.execute("SELECT payload_json FROM attempt_events WHERE attempt_id=? AND kind='output'",
                                (attempt.id,)).fetchone()
        if output:
            evidence = OutputEvidence.from_json(output[0])
            self._store._protected_binding_asset(attempt.project_id, evidence.asset_id, evidence.sha256, {"attempt_output"})
            return evidence
        envelope = self._bound(BoundSubmission.from_json(row[0]))
        source = self._store.resolve_asset(envelope["cpu_input"]["asset_id"])
        with source.path.open("rb") as content:
            staged = self._store.stage_asset(attempt.project_id, source.record.filename, content,
                                            role="attempt_output", protected=True)
        if staged.sha256 != envelope["cpu_input"]["sha256"]:
            raise AssetIntegrityError("CPU_OUTPUT_BYTES_CHANGED")
        op = self._store.get_operation(attempt.project_id, attempt.operation_id)
        evidence = OutputEvidence(staged.asset_id, staged.sha256, op.window.expected_decoder_frames,
                                  Timebase(1, 24), receipt)
        with self._store._transaction() as db:
            self._store._fenced(db, self._fence, AttemptState.DOWNLOADING)
            self._store._event(db, attempt.id, "output", json.loads(evidence.to_json()))
        return evidence

    def resume(self, fence: Fence) -> None:
        """Attach a fresh local fence to recovery; NEVER bind or submit again."""
        attempt = self._store._lookup_attempt(fence.attempt_id)
        self._guard(fence, attempt.state)
        if attempt.provider_id is None:
            raise AttemptConflictError("RECEIPT_LOOKUP_PENDING")
        self._fence = fence

    def cancel(self, receipt: Receipt) -> CancelResult:
        self._check_receipt(receipt)
        return CancelResult(False, False, "CPU routing already completed; no provider cancellation or refund.")
