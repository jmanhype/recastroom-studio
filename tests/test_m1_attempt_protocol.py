# SPDX-License-Identifier: MIT
"""Real SQLite/process/flock/media/HTTP proofs; injected faults explicitly UNIT only."""
from __future__ import annotations

from dataclasses import replace
import io
import json
import multiprocessing as mp
from pathlib import Path
import sqlite3
import subprocess

import pytest

from openjutsu.attempt_service import AttemptService
from openjutsu.managed_adapters import CPUManagedAdapter
from openjutsu.m1_types import AttemptEvent, AttemptState as S, ExecutionMode as M, Fence, RemoteState
from openjutsu.workspace_store import AttemptConflictError, ValidationError, WorkspaceStore
from openjutsu.workspace_store import AssetIntegrityError, NotFoundError
from test_m1_resolution import _workspace, _resolve, _raw_pixels
from tools.foundation_runtime import FFMPEG, FFPROBE, FoundationServer, free_loopback_port


@pytest.fixture
def prepared(tmp_path):
    store, scene, *character = _workspace(tmp_path)
    return store, _resolve(store, scene, tuple(character))


def _authorize_process(root, op, key, queue):
    store = WorkspaceStore(Path(root))
    attempt, created = store._authorize_attempt(op, key, M.DRY_RUN, None)
    queue.put((attempt.id, created))


def _contend_lock(root, queue):
    store = WorkspaceStore(Path(root))
    try:
        with store.worker_lock("contender"):
            queue.put("acquired")
    except AttemptConflictError:
        queue.put("busy")


def _crash_boundary(root, boundary, queue):
    import os
    store = WorkspaceStore(Path(root))
    with store.worker_lock("crashing"):
        fence = store.claim_attempt("crashing")
        _transition(store, fence, S.PREPARED, "ready")
        _transition(store, fence, S.READY, "submitting")
        if boundary != "submitting":
            attempt = store._lookup_attempt(fence.attempt_id)
            op = store.get_operation(attempt.project_id, attempt.operation_id)
            adapter = CPUManagedAdapter(store)
            bound = adapter.bind(op, fence)
            if boundary == "receipt":
                adapter.submit(bound, attempt.client_request_id)
        queue.put(fence.epoch)
        queue.close()
        queue.join_thread()
        os._exit(0)


def _transition(store, fence, state, target):
    return store.transition_attempt(fence, state, AttemptEvent(target, "{}"))


def test_two_process_authorization_and_payload_conflict(prepared):
    store, op = prepared
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    children = [ctx.Process(target=_authorize_process, args=(str(store.root), op, "same", queue)) for _ in range(2)]
    for child in children:
        child.start()
    results = [queue.get(timeout=30) for _ in children]
    for child in children:
        child.join(30)
        assert child.exitcode == 0
    assert len({item[0] for item in results}) == 1
    assert sorted(item[1] for item in results) == [False, True]
    attempt = store.get_attempt(op.project_id, results[0][0])
    with pytest.raises(AttemptConflictError):
        store.authorize_attempt(op, "same", M.SDK, None)
    challenger = store.authorize_attempt(op, "new-key", M.DRY_RUN, attempt.id)
    assert challenger.id != attempt.id
    assert AttemptService(store).reconcile(attempt.id) == attempt
    other = store.create_project("other")
    with pytest.raises(NotFoundError, match="not found"):
        store.get_attempt(other.project_id, attempt.id)
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 2


def test_lifetime_flock_and_stale_epoch(prepared):
    store, op = prepared
    attempt = store.authorize_attempt(op, "lock", M.DRY_RUN, None)
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    with pytest.raises(AttemptConflictError):
        store.claim_attempt("owner")
    with store.worker_lock("owner") as epoch:
        fence = store.claim_attempt("owner")
        assert fence.epoch == epoch
        child = ctx.Process(target=_contend_lock, args=(str(store.root), queue))
        child.start()
        assert queue.get(timeout=30) == "busy"
        child.join(30)
        assert child.exitcode == 0
        with pytest.raises(AttemptConflictError):
            _transition(store, replace(fence, owner_id="forged"), S.PREPARED, "ready")
        assert store.claim_attempt("owner") is None
    with store.worker_lock("next") as epoch2:
        fresh = store.claim_attempt("next")
        assert epoch2 > epoch
        with pytest.raises(AttemptConflictError):
            _transition(store, fence, S.PREPARED, "ready")
        assert _transition(store, fresh, S.PREPARED, "ready").state == S.READY
        with pytest.raises(AttemptConflictError):
            _transition(store, fresh, S.PREPARED, "ready")
    assert store.get_attempt(op.project_id, attempt.id).revision == 2


def test_real_cpu_binding_receipt_download_and_restart(prepared):
    store, op = prepared
    attempt = store.authorize_attempt(op, "cpu", M.DRY_RUN, None)
    with store.worker_lock("first"):
        fence = store.claim_attempt("first")
        adapter = CPUManagedAdapter(store)
        assert adapter.preflight(op).ready
        with pytest.raises(AttemptConflictError):
            adapter.bind(op, fence)
        _transition(store, fence, S.PREPARED, "ready")
        _transition(store, fence, S.READY, "submitting")
        bound = adapter.bind(op, fence)
        assert not bound.charge_bearing
        assert bound.binding_sha256 != json.loads(op.canonical_json)["graph"]["resolved_semantic_sha256"]
        receipt = adapter.submit(bound, "cpu")
        assert store.get_attempt(op.project_id, attempt.id).provider_id == receipt.provider_id
        assert adapter.poll(receipt) == RemoteState.COMPLETED
        assert not adapter.cancel(receipt).confirmed
        assert store.record_receipt(fence, receipt).state == S.SUBMITTED
        with pytest.raises(AttemptConflictError):
            adapter.submit(bound, "cpu")
    store = WorkspaceStore(store.root)
    with store.worker_lock("recovery"):
        fence = store.claim_attempt("recovery")
        adapter = CPUManagedAdapter(store)
        adapter.resume(fence)
        assert adapter.poll(receipt) == RemoteState.COMPLETED
        _transition(store, fence, S.SUBMITTED, "downloading")
        output = adapter.download(receipt)
        assert adapter.download(receipt) == output
        assert output.receipt == receipt and output.frame_count == 8
        source = store.get_scene_revision(op.project_id, op.scene_revision_id).source
        assert _raw_pixels(store.resolve_asset(output.asset_id).path, 0, 8) == _raw_pixels(
            store.resolve_asset(source.asset_id).path, 8, 16)
        assert _transition(store, fence, S.DOWNLOADING, "completed").state == S.COMPLETED
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM provider_receipts").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'").fetchone()[0] == 1


@pytest.mark.parametrize("boundary", ["submitting", "bound", "receipt"])
def test_real_process_crash_never_rebinds_or_resubmits(prepared, boundary):
    store, op = prepared
    attempt = store.authorize_attempt(op, "crash", M.DRY_RUN, None)
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    child = ctx.Process(target=_crash_boundary, args=(str(store.root), boundary, queue))
    child.start()
    old_epoch = queue.get(timeout=30)
    child.join(30)
    assert child.exitcode == 0
    with store.worker_lock("restart") as epoch:
        assert epoch > old_epoch
        fence = store.claim_attempt("restart")
        recovered = store.get_attempt(op.project_id, attempt.id)
        assert recovered.state == (S.SUBMITTED if boundary == "receipt" else S.RECONCILE_NEEDED)
        adapter = CPUManagedAdapter(store)
        with pytest.raises(AttemptConflictError):
            adapter.bind(op, fence)
        if boundary == "receipt":
            adapter.resume(fence)
            assert adapter.poll(store._receipt(recovered)) == RemoteState.COMPLETED
        else:
            with pytest.raises(AttemptConflictError, match="LOOKUP_PENDING"):
                adapter.resume(fence)
        assert AttemptService(store).reconcile(attempt.id) == recovered


@pytest.mark.parametrize("stage", ["binding", "receipt"])
@pytest.mark.parametrize("fault", [TimeoutError, ValueError, KeyboardInterrupt])
def test_UNIT_boundary_fault_matrix_not_provider_proof(prepared, monkeypatch, stage, fault):
    store, op = prepared
    attempt = store.authorize_attempt(op, "fault", M.DRY_RUN, None)
    with store.worker_lock("unit"):
        fence = store.claim_attempt("unit")
        _transition(store, fence, S.PREPARED, "ready")
        _transition(store, fence, S.READY, "submitting")
        adapter = CPUManagedAdapter(store)
        original = store.stage_asset
        def fail(*args, **kwargs):
            raise fault("UNIT injected boundary interruption; not live transport")
        if stage == "receipt":
            bound = adapter.bind(op, fence)
        monkeypatch.setattr(store, "stage_asset", fail)
        with pytest.raises(fault):
            adapter.bind(op, fence) if stage == "binding" else adapter.submit(bound, "fault")
        monkeypatch.setattr(store, "stage_asset", original)
        assert store.get_attempt(op.project_id, attempt.id).state == S.RECONCILE_NEEDED
        with pytest.raises(AttemptConflictError):
            adapter.bind(op, fence)


def test_cancel_and_unsafe_events(prepared):
    store, op = prepared
    attempt = store.authorize_attempt(op, "cancel", M.DRY_RUN, None)
    with store.worker_lock("worker"):
        fence = store.claim_attempt("worker")
        _transition(store, fence, S.PREPARED, "ready")
        # The competing HTTP side records intent but cannot steal this lock.
        service = AttemptService(WorkspaceStore(store.root))
        assert service.request_cancel(attempt.id).state == S.READY
        with pytest.raises(AttemptConflictError, match="CANCEL_PENDING"):
            _transition(store, fence, S.READY, "submitting")
        with pytest.raises(ValidationError):
            store.transition_attempt(fence, S.READY, AttemptEvent("submitting", '{"unsafe":"value"}'))
        assert store.apply_cancel_intent(fence).state == S.PROVIDER_CONFIRMED_CANCELLED
    queued = store.authorize_attempt(op, "queued", M.DRY_RUN, None)
    assert AttemptService(store).request_cancel(queued.id).state == S.PROVIDER_CONFIRMED_CANCELLED


def test_frozen_binding_drift_and_receipt_ownership(prepared):
    store, op = prepared
    attempt = store.authorize_attempt(op, "integrity", M.DRY_RUN, None)
    with store.worker_lock("integrity"):
        fence = store.claim_attempt("integrity")
        _transition(store, fence, S.PREPARED, "ready")
        _transition(store, fence, S.READY, "submitting")
        adapter = CPUManagedAdapter(store)
        bound = adapter.bind(op, fence)
        with pytest.raises(ValidationError):
            adapter._bound(replace(bound, binding_asset_id=store.get_preparation_binding(op.project_id, op.id).binding_asset_id))
        receipt = adapter.submit(bound, attempt.client_request_id)
        with pytest.raises(ValidationError):
            store.record_receipt(fence, replace(receipt, request_key="different"))
        with pytest.raises(AttemptConflictError):
            store.record_receipt(fence, replace(receipt, provider_id="different"))
        assert AttemptService(WorkspaceStore(store.root)).request_cancel(attempt.id).state == S.SUBMITTED
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
        assert adapter.cancel(receipt).supported is False
        with pytest.raises(ValidationError):
            _transition(store, fence, S.CANCEL_REQUESTED, "provider_confirmed_cancelled")
        with pytest.raises(ValidationError):
            store.transition_attempt(fence, S.CANCEL_REQUESTED,
                AttemptEvent("provider_confirmed_cancelled", '{"supported":1,"confirmed":1}'))
    assert store.get_attempt(op.project_id, attempt.id).state == S.CANCEL_REQUESTED
    fresh = store.authorize_attempt(op, "drift", M.DRY_RUN, None)
    preparation = store.get_preparation_binding(op.project_id, op.id)
    content = json.loads(store.resolve_asset(preparation.binding_asset_id).path.read_bytes())
    graph = store.resolve_asset(content["graph"]["asset_id"]).path
    graph.write_bytes(graph.read_bytes() + b" ")
    with store.worker_lock("drift"):
        # Earlier pending cancellation is still claimed first, never re-submitted.
        store.claim_attempt("drift")
        fence = store.claim_attempt("drift")
        assert fence.attempt_id == fresh.id
        _transition(store, fence, S.PREPARED, "ready")
        _transition(store, fence, S.READY, "submitting")
        with pytest.raises(AssetIntegrityError):
            CPUManagedAdapter(store).bind(op, fence)
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM provider_receipts").fetchone()[0] == 1


def test_owner_blocked_modes_do_not_enter_cpu_boundary(prepared):
    store, op = prepared
    for mode in (M.COMFY, M.SDK, M.RETAINED_REPLAY):
        store.authorize_attempt(op, mode.value, mode, None)
    with store.worker_lock("blocked"):
        for _ in range(3):
            fence = store.claim_attempt("blocked")
            _transition(store, fence, S.PREPARED, "ready")
            _transition(store, fence, S.READY, "submitting")
            with pytest.raises(AttemptConflictError, match="OWNER_BLOCKED"):
                CPUManagedAdapter(store).bind(op, fence)
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM provider_receipts").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='bind_started'").fetchone()[0] == 0


def test_real_http_authorization_safe_errors_and_no_reauthorization(prepared, tmp_path):
    store, op = prepared
    # S3 producer-only fixture isolation; S4 proves the default consuming lifespan.
    server = FoundationServer(free_loopback_port(), store.root, tmp_path / "http.log", test_lifespan="off")
    try:
        server.start()
        import requests
        from concurrent.futures import ThreadPoolExecutor
        url = server.base_url + f"/api/projects/{op.project_id}/attempts"
        payload = {"operation_id": op.id, "client_request_id": "http", "mode": "dry_run"}
        first = requests.post(url, json=payload, timeout=10)
        assert first.status_code == 201, first.text
        assert requests.post(url, json=payload, timeout=10).status_code == 200
        assert requests.post(url, json={**payload, "mode": "sdk"}, timeout=10).status_code == 409
        attempt = first.json()
        assert requests.post(url + f"/{attempt['id']}/reconcile", timeout=10).status_code == 200
        assert len(requests.get(url, timeout=10).json()) == 1
        cancel = requests.post(url + f"/{attempt['id']}/cancel", timeout=10)
        assert cancel.json()["state"] == "provider_confirmed_cancelled"
        bad = requests.post(url, json={**payload, "operation_id": "missing"}, timeout=10)
        assert bad.status_code == 404 and str(store.root) not in bad.text
        assert requests.post(url, json={**payload, "path": "/private"}, timeout=10).status_code == 422
        with ThreadPoolExecutor(max_workers=2) as pool:
            replies = list(pool.map(lambda _: requests.post(url, json={**payload, "client_request_id": "race"}, timeout=10), range(2)))
        assert sorted(reply.status_code for reply in replies) == [200, 201]
        assert replies[0].json()["id"] == replies[1].json()["id"]
    finally:
        server.stop()


def _submitted(store, op, key):
    attempt = store.authorize_attempt(op, key, M.DRY_RUN, None)
    fence = store.claim_attempt("outcome")
    assert fence.attempt_id == attempt.id
    _transition(store, fence, S.PREPARED, "ready")
    _transition(store, fence, S.READY, "submitting")
    adapter = CPUManagedAdapter(store)
    receipt = adapter.submit(adapter.bind(op, fence), key)
    return attempt, fence, adapter, receipt


def _observed(store, fence, state, target, payload):
    assert store._lookup_attempt(fence.attempt_id).state == state
    return store.transition_attempt(fence, state, AttemptEvent(target, json.dumps(payload)))


@pytest.mark.parametrize("state", [S.DOWNLOADING, S.RECONCILE_NEEDED, S.CANCEL_REQUESTED])
@pytest.mark.parametrize("check", ["bytes", "hash", "frames", "pts", "pixels"])
def test_real_invalid_output_terminal_not_uncertainty(prepared, tmp_path, state, check):
    store, op = prepared
    with store.worker_lock("outcome"):
        attempt, fence, adapter, receipt = _submitted(store, op, "invalid")
        _transition(store, fence, S.SUBMITTED, "downloading")
        good = adapter.download(receipt)
        source = store.resolve_asset(good.asset_id).path
        assert good.frame_count == 8 and len(_raw_pixels(source, 0, 8)) > 0
        if check == "bytes":
            data = b"not decodable video"
            broken = tmp_path / "invalid.mkv"
            broken.write_bytes(data)
            assert subprocess.run([str(FFPROBE), "-v", "error", str(broken)], capture_output=True).returncode != 0
        elif check == "hash":
            data = source.read_bytes() + b"changed-byte-stream"
        else:
            broken = tmp_path / "invalid.mkv"
            vf = {"frames": "trim=end_frame=7", "pts": "setpts=2*PTS", "pixels": "negate"}[check]
            subprocess.run([str(FFMPEG), "-nostdin", "-v", "error", "-i", str(source), "-vf", vf,
                "-fps_mode", "passthrough", "-c:v", "ffv1", str(broken)], check=True, capture_output=True)
            info = json.loads(subprocess.run([str(FFPROBE), "-v", "error", "-show_frames", "-of", "json",
                str(broken)], check=True, capture_output=True).stdout)["frames"]
            if check == "frames":
                assert len(info) == 7 != good.frame_count
            elif check == "pts":
                assert float(info[1]["pts_time"]) > 1 / 24 + 0.01
            else:
                assert len(info) == 8 and _raw_pixels(broken, 0, 8) != _raw_pixels(source, 0, 8)
            data = broken.read_bytes()
        bad = store.stage_asset(op.project_id, "rejected.mkv", io.BytesIO(data), role="attempt_output", protected=True)
        assert bad.sha256 != good.sha256
        if state == S.CANCEL_REQUESTED:
            store._record_intent(attempt.id, "cancel_intent")
            assert store.apply_cancel_intent(fence).state == state
        elif state == S.RECONCILE_NEEDED:
            _transition(store, fence, S.DOWNLOADING, state.value)
        payload = {"reason": "output_" + check, "receipt_sha256": receipt.receipt_sha256,
                   "asset_id": bad.asset_id, "sha256": bad.sha256}
        # Each negative reaches the intended state with a real receipt and asset.
        with pytest.raises(ValidationError, match="FAILURE_RECEIPT_MISMATCH"):
            _observed(store, fence, state, "failed", {**payload, "receipt_sha256": "0" * 64})
        with pytest.raises(ValidationError, match="asset role, ownership, or hash"):
            _observed(store, fence, state, "failed", {**payload, "sha256": good.sha256})
        with pytest.raises(ValidationError, match="INVALID_FAILURE_EVENT"):
            _observed(store, fence, state, "failed", {**payload, "unsafe": "/private/path"})
        assert _observed(store, fence, state, "failed", payload).state == S.FAILED
        with pytest.raises(AttemptConflictError):
            adapter.bind(op, fence)
        with pytest.raises(AttemptConflictError):
            adapter.download(receipt)
        with store._connect() as db:
            assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'").fetchone()[0] == 1
    reopened = WorkspaceStore(store.root)
    with reopened.worker_lock("restart"):
        assert reopened.claim_attempt("restart") is None
    assert reopened.get_attempt(op.project_id, attempt.id).state == S.FAILED


@pytest.mark.parametrize("state", [S.SUBMITTED, S.RUNNING, S.DOWNLOADING, S.RECONCILE_NEEDED, S.CANCEL_REQUESTED])
def test_receipted_remote_failure_observation_and_fences(prepared, state):
    """Real store protocol observation, NOT a CPU/provider reporting failure proof."""
    store, op = prepared
    with store.worker_lock("outcome"):
        attempt, fence, adapter, receipt = _submitted(store, op, "remote-failure")
        if state != S.SUBMITTED:
            _transition(store, fence, S.SUBMITTED, state.value)
        payload = {"reason": "remote_failed", "receipt_sha256": receipt.receipt_sha256}
        assert store._lookup_attempt(attempt.id).state == state
        with pytest.raises(AttemptConflictError, match="STALE_FENCE"):
            _observed(store, replace(fence, epoch=fence.epoch + 1), state, "failed", payload)
        with pytest.raises(ValidationError, match="INVALID_FAILURE_EVENT"):
            _observed(store, fence, state, "failed", {})
        with pytest.raises(ValidationError, match="INVALID_FAILURE_EVENT"):
            _observed(store, fence, state, "failed", {**payload, "reason": "timeout"})
        assert _observed(store, fence, state, "failed", payload).state == S.FAILED


@pytest.mark.parametrize("download_first", [False, True])
def test_cancel_completion_and_durable_consumption_restart(prepared, download_first):
    store, op = prepared
    with store.worker_lock("outcome"):
        attempt, fence, adapter, receipt = _submitted(store, op, "cancel-race")
        if download_first:
            _transition(store, fence, S.SUBMITTED, "downloading")
            adapter.download(receipt)
        store._record_intent(attempt.id, "cancel_intent")
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
        assert adapter.cancel(receipt).supported is False
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
    # Real new process verifies durable consumption, not just instance memory.
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    child = ctx.Process(target=_resume_cancel_completion, args=(str(store.root), download_first, queue))
    child.start()
    assert queue.get(timeout=30) == "completed"
    child.join(30)
    assert child.exitcode == 0
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='cancel_intent_consumed'").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'").fetchone()[0] == 1


def _resume_cancel_completion(root, download_first, queue):
    store = WorkspaceStore(Path(root))
    with store.worker_lock("restart"):
        fence = store.claim_attempt("restart")
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
        attempt = store._lookup_attempt(fence.attempt_id)
        receipt = store._receipt(attempt)
        adapter = CPUManagedAdapter(store)
        adapter.resume(fence)
        assert adapter.poll(receipt) == RemoteState.COMPLETED
        if not download_first:
            with pytest.raises(ValidationError, match="INVALID_COMPLETION_OBSERVATION"):
                _transition(store, fence, S.CANCEL_REQUESTED, "downloading")
            _observed(store, fence, S.CANCEL_REQUESTED, "downloading",
                {"remote_state": "completed", "receipt_sha256": receipt.receipt_sha256})
            assert store.apply_cancel_intent(fence).state == S.DOWNLOADING
            adapter.download(receipt)
        state = S.CANCEL_REQUESTED if download_first else S.DOWNLOADING
        queue.put(_transition(store, fence, state, "completed").state.value)


def test_unknown_no_id_cannot_become_known_terminal(prepared):
    store, op = prepared
    attempt = store.authorize_attempt(op, "unknown", M.DRY_RUN, None)
    with store.worker_lock("unknown"):
        fence = store.claim_attempt("unknown")
        _transition(store, fence, S.PREPARED, "ready")
        _transition(store, fence, S.READY, "submitting")
        _transition(store, fence, S.SUBMITTING, "reconcile_needed")
        for state in (S.RECONCILE_NEEDED, S.CANCEL_REQUESTED):
            assert store._lookup_attempt(attempt.id).state == state
            with pytest.raises(NotFoundError, match="LOOKUP_PENDING"):
                _observed(store, fence, state, "failed", {"reason": "remote_failed", "receipt_sha256": "0" * 64})
            with pytest.raises(AttemptConflictError, match="OUTPUT_REQUIRED"):
                _transition(store, fence, state, "completed")
            with pytest.raises(AttemptConflictError, match="RECEIPT_REQUIRED"):
                _transition(store, fence, state, "downloading")
            if state == S.RECONCILE_NEEDED:
                store._record_intent(attempt.id, "cancel_intent")
                store.apply_cancel_intent(fence)
        with pytest.raises(NotFoundError, match="LOOKUP_PENDING"):
            _observed(store, fence, S.CANCEL_REQUESTED, "provider_confirmed_cancelled", {"supported": True, "confirmed": True})
        assert store._lookup_attempt(attempt.id).state == S.CANCEL_REQUESTED


def test_consumed_cancel_does_not_loop_but_new_request_is_honored(prepared):
    store, op = prepared
    with store.worker_lock("outcome"):
        attempt, fence, adapter, receipt = _submitted(store, op, "intent-sequence")
        store._record_intent(attempt.id, "cancel_intent")
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
        _transition(store, fence, S.CANCEL_REQUESTED, "reconcile_needed")
    store = WorkspaceStore(store.root)
    with store.worker_lock("restarted"):
        fence = store.claim_attempt("restarted")
        assert store.apply_cancel_intent(fence).state == S.RECONCILE_NEEDED
        _transition(store, fence, S.RECONCILE_NEEDED, "running")
        assert store.apply_cancel_intent(fence).state == S.RUNNING
        store._record_intent(attempt.id, "cancel_intent")
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
        with store._connect() as db:
            assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='cancel_intent_consumed'").fetchone()[0] == 2


def test_terminal_output_guards_authenticate_receipt_bytes_and_ownership(prepared):
    store, op = prepared
    with store.worker_lock("outcome"):
        attempt, fence, adapter, receipt = _submitted(store, op, "terminal-guards")
        _transition(store, fence, S.SUBMITTED, "downloading")
        with pytest.raises(AttemptConflictError, match="OUTPUT_REQUIRED"):
            _observed(store, fence, S.DOWNLOADING, "completed", {})
        output = adapter.download(receipt)
        other = store.create_project("other")
        candidates = [store.stage_asset(project, "candidate.mkv", io.BytesIO(b"invalid"), role=role, protected=protected)
            for project, role, protected in [(other.project_id, "attempt_output", True),
                (op.project_id, "source", True), (op.project_id, "attempt_output", False)]]
        for asset in candidates:
            with pytest.raises(ValidationError, match="asset role, ownership, or hash"):
                _observed(store, fence, S.DOWNLOADING, "failed", {"reason": "output_bytes",
                    "receipt_sha256": receipt.receipt_sha256, "asset_id": asset.asset_id, "sha256": asset.sha256})
        store._record_intent(attempt.id, "cancel_intent")
        store.apply_cancel_intent(fence)
        assert store._lookup_attempt(attempt.id).state == S.CANCEL_REQUESTED
        protected = store.resolve_asset(output.asset_id).path
        original = protected.read_bytes()
        protected.write_bytes(b"tampered")
        with pytest.raises(AssetIntegrityError):
            _observed(store, fence, S.CANCEL_REQUESTED, "completed", {})
        protected.write_bytes(original)
        receipt_path = store.resolve_asset(receipt.receipt_asset_id).path
        original_receipt = receipt_path.read_bytes()
        receipt_path.write_bytes(b"tampered")
        with pytest.raises(AssetIntegrityError):
            _observed(store, fence, S.CANCEL_REQUESTED, "completed", {})
        receipt_path.write_bytes(original_receipt)
        assert _observed(store, fence, S.CANCEL_REQUESTED, "completed", {}).state == S.COMPLETED
