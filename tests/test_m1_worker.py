# SPDX-License-Identifier: MIT
"""Real worker, process, HTTP, SQLite, and media proofs for OJ-40ny."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

from app.main import app
from openjutsu.attempt_service import AttemptService
from openjutsu.attempt_worker import cpu_adapters, run_once
from openjutsu.managed_adapters import CPUManagedAdapter
from openjutsu.m1_types import (
    AttemptEvent, AttemptState as S, BoundSubmission, CancelResult, ExecutionMode as M,
    FrameRange, OutputEvidence, Readiness, Receipt, RemoteState, ResolvedOperation, ShotSpec,
)
from openjutsu.recipe_service import CPU_CLIP_SHA256, OFFLINE_SOURCE_SHA256
from openjutsu.scene_service import SceneService
from openjutsu.take_service import TakeService
from openjutsu.workspace_store import WorkspaceStore, WorkspaceStoreError
from test_m1_resolution import _raw_pixels, _resolve, _workspace
from test_m1_scenes import _client
from tools.foundation_runtime import FFPROBE, FoundationServer, free_loopback_port, generate_media


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)
TMPDIR = os.environ.get("TMPDIR", "/tmp")


@pytest.fixture
def prepared(tmp_path: Path):
    store, scene_id, *character = _workspace(tmp_path)
    return store, _resolve(store, scene_id, tuple(character))


def _worker(store: WorkspaceStore) -> bool:
    return run_once(store, cpu_adapters(store))


def _count(store: WorkspaceStore, sql: str) -> int:
    with store._connect() as db:
        return int(db.execute(sql).fetchone()[0])


def _transition(store: WorkspaceStore, fence, state: S, target: S):
    return store.transition_attempt(fence, state, AttemptEvent(target.value, "{}"))


def _crash_submitted(root: str, operation, key: str, queue) -> None:
    store = WorkspaceStore(Path(root))
    with store.worker_lock("crash-worker"):
        fence = store.claim_attempt("crash-worker")
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        adapter = CPUManagedAdapter(store)
        receipt = adapter.submit(adapter.bind(operation, fence), key)
        queue.put(receipt.receipt_sha256)
        queue.close(); queue.join_thread()
        os._exit(0)


def test_worker_registers_qualified_full_and_extracted_cpu_takes(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    source_scene = store.get_scene_revision(store.list_projects()[0].project_id, scene_id)
    full_scene = SceneService(store, ffprobe=str(FFPROBE)).confirm_shots(
        source_scene.project_id, source_scene.source.asset_id,
        (ShotSpec("full", FrameRange(0, 24), "render"),),
    )
    operations = {
        "full": _resolve(store, full_scene.id, tuple(character), shot_id="full"),
        "extract": _resolve(store, scene_id, tuple(character), shot_id="second"),
    }
    for label, operation in operations.items():
        store.authorize_attempt(operation, f"worker-{label}", M.DRY_RUN, None)
    with store.worker_lock("lifetime-owner"):
        assert all(run_once(store, cpu_adapters(store)) for _ in operations)
    for label, operation in operations.items():
        attempt = next(item for item in store.list_attempts(operation.project_id)
                       if item.operation_id == operation.id)
        assert attempt.state == S.COMPLETED and attempt.operation_id == operation.id
        with store._connect() as db:
            take_id, output_id = db.execute(
                "SELECT take_id,output_asset_id FROM takes WHERE attempt_id=?", (attempt.id,)
            ).fetchone()
            submit_count, receipt_count = db.execute(
                "SELECT (SELECT COUNT(*) FROM attempt_events WHERE attempt_id=? AND kind='submit_started'),"
                "(SELECT COUNT(*) FROM provider_receipts WHERE attempt_id=?)", (attempt.id, attempt.id)
            ).fetchone()
        take = store.get_take(operation.project_id, take_id)
        assert submit_count == receipt_count == 1
        assert take.scene_revision_id == operation.scene_revision_id
        assert take.shot_id == operation.shot_id and take.attempt_id == attempt.id
        assert take.operation_id == operation.id and take.origin == "dry_run" and take.qualified is True
        assert take.output.asset_id == output_id and take.output.receipt is not None
        manifest = json.loads(operation.canonical_json)
        assert manifest["recipe"]["non_inference"] is True and manifest["recipe"]["h3_qualified"] is False
        start, end = operation.window.source_range.start, operation.window.source_range.end
        source = store.resolve_asset(source_scene.source.asset_id).path
        output = store.resolve_asset(output_id).path
        assert _raw_pixels(output, 0, end - start) == _raw_pixels(source, start, end)
        assert take.output.sha256 == (OFFLINE_SOURCE_SHA256 if label == "full" else CPU_CLIP_SHA256[(start, end)])
    assert _worker(store) is False
    with store._connect() as db:
        claims = [json.loads(row[0]) for row in db.execute(
            "SELECT payload_json FROM attempt_events WHERE kind='claimed' ORDER BY sequence"
        )]
    assert len({(item["owner_id"], item["epoch"]) for item in claims}) == 1


def test_module_cli_is_excluded_by_lifetime_flock_then_recovers_once(prepared, tmp_path: Path) -> None:
    store, operation = prepared
    attempt = store.authorize_attempt(operation, "module", M.DRY_RUN, None)
    environment = {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin", "HOME": "/Users/speed",
        "TMPDIR": TMPDIR, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}",
        "GIT_ALLOW_PROTOCOL": "__recastroom_local_only__",
    }
    with store.worker_lock("external-owner"):
        blocked = subprocess.run(
            [str(PYTHON), "-m", "openjutsu.attempt_worker", str(store.root)],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30, check=True,
        )
        assert blocked.returncode == 0
        assert store.get_attempt(operation.project_id, attempt.id).state == S.PREPARED
        assert _count(store, "SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'") == 0
    subprocess.run(
        [str(PYTHON), "-m", "openjutsu.attempt_worker", str(store.root)],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30, check=True,
    )
    assert store.get_attempt(operation.project_id, attempt.id).state == S.COMPLETED
    assert _count(store, "SELECT COUNT(*) FROM provider_receipts") == 1
    assert _count(store, "SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'") == 1


def test_two_real_web_instances_share_one_lifetime_worker(prepared) -> None:
    store, operation = prepared
    attempt = store.authorize_attempt(operation, "web", M.DRY_RUN, None)
    servers = []
    try:
        with store.worker_lock("sole-holder"):
            for index in range(2):
                server = FoundationServer(free_loopback_port(), store.root,
                                          store.root / f"web-{index}.log")
                server.start()
                servers.append(server)
            deadline = time.monotonic() + 0.6
            while time.monotonic() < deadline:
                time.sleep(0.05)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if store.get_attempt(operation.project_id, attempt.id).state == S.COMPLETED:
                break
            time.sleep(0.05)
        assert store.get_attempt(operation.project_id, attempt.id).state == S.COMPLETED
        assert _count(store, "SELECT COUNT(*) FROM provider_receipts") == 1
        assert _count(store, "SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'") == 1
    finally:
        for server in servers:
            server.stop()


def test_web_incumbent_owns_idle_lifetime_and_cli_takes_over_after_death(prepared,
                                                                         tmp_path: Path) -> None:
    store, operation = prepared
    server = FoundationServer(free_loopback_port(), store.root, tmp_path / "incumbent.log")
    environment = {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin", "HOME": "/Users/speed",
        "TMPDIR": TMPDIR, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}",
        "GIT_ALLOW_PROTOCOL": "__recastroom_local_only__",
    }
    try:
        server.start()
        assert _count(store, "SELECT COUNT(*) FROM worker_epochs") == 0
        import requests
        first = requests.post(
            f"{server.base_url}/api/projects/{operation.project_id}/attempts",
            json={"operation_id": operation.id, "client_request_id": "incumbent",
                  "mode": "dry_run", "challenger_of": None}, timeout=10,
        )
        assert first.status_code == 201, first.text
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with store._connect() as db:
                incumbent = db.execute(
                    "SELECT epoch FROM worker_epochs WHERE owner_id='app-worker' AND released_at IS NULL"
                ).fetchone()
            if incumbent is not None:
                break
            time.sleep(0.05)
        assert incumbent is not None
        subprocess.run([str(PYTHON), "-m", "openjutsu.attempt_worker", str(store.root)],
                       cwd=ROOT, env=environment, capture_output=True, text=True,
                       timeout=30, check=True)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            attempts = requests.get(
                f"{server.base_url}/api/projects/{operation.project_id}/attempts", timeout=10
            ).json()
            if attempts and attempts[0]["state"] == "completed":
                break
            time.sleep(0.05)
        assert attempts[0]["state"] == "completed"
        consecutive = store.authorize_attempt(operation, "consecutive", M.DRY_RUN, None)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if store.get_attempt(operation.project_id, consecutive.id).state == S.COMPLETED:
                break
            time.sleep(0.05)
        assert store.get_attempt(operation.project_id, consecutive.id).state == S.COMPLETED
        assert _count(store, "SELECT COUNT(*) FROM worker_epochs") == 1
    finally:
        server.stop()
    second = store.authorize_attempt(operation, "takeover", M.DRY_RUN, None)
    subprocess.run([str(PYTHON), "-m", "openjutsu.attempt_worker", str(store.root)],
                   cwd=ROOT, env=environment, capture_output=True, text=True,
                   timeout=30, check=True)
    assert store.get_attempt(operation.project_id, second.id).state == S.COMPLETED
    with store._connect() as db:
        owners = {row[0] for row in db.execute(
            "SELECT DISTINCT owner_id FROM worker_epochs ORDER BY epoch"
        )}
        assert db.execute("SELECT COUNT(*) FROM provider_receipts").fetchone()[0] == 3
    assert owners == {"app-worker", "cli-worker"}


def test_known_receipt_restart_downloads_same_output_and_registers_once(prepared) -> None:
    store, operation = prepared
    import multiprocessing as mp
    attempt = store.authorize_attempt(operation, "restart", M.DRY_RUN, None)
    context = mp.get_context("spawn")
    queue = context.Queue()
    child = context.Process(target=_crash_submitted, args=(str(store.root), operation, "restart", queue))
    child.start(); receipt_hash = queue.get(timeout=30); child.join(30)
    assert child.exitcode == 0
    assert _worker(store) is True
    final = store.get_attempt(operation.project_id, attempt.id)
    assert final.state == S.COMPLETED and final.provider_id == f"cpu-{attempt.id}"
    with store._connect() as db:
        receipt, output_payload, take = db.execute(
            "SELECT r.receipt_sha256,o.payload_json,t.take_id FROM provider_receipts r "
            "JOIN attempt_events o ON o.attempt_id=r.attempt_id AND o.kind='output' "
            "JOIN takes t ON t.attempt_id=r.attempt_id WHERE r.attempt_id=?", (attempt.id,)
        ).fetchone()
        events = [row[0] for row in db.execute(
            "SELECT kind FROM attempt_events WHERE attempt_id=? ORDER BY sequence", (attempt.id,)
        )]
    assert receipt == receipt_hash and take.startswith("take-")
    assert events.count("submit_started") == 1 and events.count("bind_started") == 1
    output = json.loads(output_payload)["asset_id"]
    assert store.resolve_asset(output).record.protected


def test_UNIT_poll_uncertainty_never_becomes_confirmed_failure(prepared, monkeypatch) -> None:
    store, operation = prepared
    attempt = store.authorize_attempt(operation, "uncertain", M.DRY_RUN, None)
    with store.worker_lock("unit"):
        fence = store.claim_attempt("unit")
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        adapter = CPUManagedAdapter(store)
        adapter.submit(adapter.bind(operation, fence), "uncertain")
    monkeypatch.setattr(CPUManagedAdapter, "poll", lambda self, receipt: RemoteState.RUNNING)
    assert _worker(store) is True
    assert store.get_attempt(operation.project_id, attempt.id).state == S.SUBMITTED
    monkeypatch.setattr(CPUManagedAdapter, "poll", lambda self, receipt: RemoteState.UNKNOWN)
    assert _worker(store) is True
    assert store.get_attempt(operation.project_id, attempt.id).state == S.RECONCILE_NEEDED
    with store._connect() as db:
        before = db.execute("SELECT COUNT(*) FROM worker_epochs").fetchone()[0]
        assert _worker(store) is False
        after = db.execute("SELECT COUNT(*) FROM worker_epochs").fetchone()[0]
        assert before == after
        assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE attempt_id=? AND kind='failed'",
                          (attempt.id,)).fetchone()[0] == 0


def test_UNIT_strict_six_method_adapters_recover_without_private_extensions(prepared) -> None:
    store, operation = prepared

    class StrictSixAdapter:
        def __init__(self, configured_store: WorkspaceStore, evidence: OutputEvidence,
                     receipt: Receipt, remote: RemoteState, confirmed: bool) -> None:
            self.store, self.evidence = configured_store, evidence
            self.receipt, self.remote, self.confirmed = receipt, remote, confirmed

        def preflight(self, op: ResolvedOperation) -> Readiness:
            return Readiness(True, "UNIT", "strict six-method adapter")

        def bind(self, op: ResolvedOperation, fence) -> BoundSubmission:
            raise AssertionError("recovery must not bind")

        def submit(self, bound: BoundSubmission, request_key: str) -> Receipt:
            raise AssertionError("recovery must not submit")

        def poll(self, receipt: Receipt) -> RemoteState:
            return self.remote

        def download(self, receipt: Receipt) -> OutputEvidence:
            return self.evidence

        def cancel(self, receipt: Receipt) -> CancelResult:
            return CancelResult(self.confirmed, self.confirmed, "UNIT configured cancellation")

    recovery = store.authorize_attempt(operation, "strict-recovery", M.DRY_RUN, None)
    with store.worker_lock("cpu-setup"):
        fence = store.claim_attempt("cpu-setup")
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        cpu = CPUManagedAdapter(store)
        receipt = cpu.submit(cpu.bind(operation, fence), "strict-recovery")
        _transition(store, fence, S.SUBMITTED, S.DOWNLOADING)
        evidence = cpu.download(receipt)
    adapter = StrictSixAdapter(store, evidence, receipt, RemoteState.COMPLETED, False)
    assert run_once(store, {M.DRY_RUN: adapter}) is True
    assert store.get_attempt(operation.project_id, recovery.id).state == S.COMPLETED

    cancelled = store.authorize_attempt(operation, "strict-cancel", M.DRY_RUN, None)
    with store.worker_lock("cancel-setup"):
        fence = store.claim_attempt("cancel-setup")
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        cpu = CPUManagedAdapter(store)
        receipt = cpu.submit(cpu.bind(operation, fence), "strict-cancel")
        store._record_intent(cancelled.id, "cancel_intent")
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
    adapter = StrictSixAdapter(store, evidence, receipt, RemoteState.RUNNING, True)
    assert run_once(store, {M.DRY_RUN: adapter}) is True
    assert store.get_attempt(operation.project_id, cancelled.id).state == S.PROVIDER_CONFIRMED_CANCELLED


def test_pause_and_no_id_recovery_do_not_poison_unrelated_work(prepared, monkeypatch) -> None:
    store, operation = prepared
    older = store.authorize_attempt(operation, "older-fresh", M.DRY_RUN, None)
    newer = store.authorize_attempt(operation, "newer-prior", M.DRY_RUN, None)
    with store.worker_lock("prior"):
        assert store.claim_attempt("prior").attempt_id == older.id
        fence = store.claim_attempt("prior")
        assert fence.attempt_id == newer.id
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        prior_adapter = CPUManagedAdapter(store)
        prior_adapter.submit(prior_adapter.bind(operation, fence), "newer-prior")
    monkeypatch.setattr(CPUManagedAdapter, "poll", lambda self, receipt: RemoteState.UNKNOWN)
    assert run_once(store, cpu_adapters(store)) is True
    assert store.get_attempt(operation.project_id, newer.id).state == S.RECONCILE_NEEDED
    with store.worker_lock("after-pause") as epoch:
        fence = store.claim_attempt("after-pause")
        assert fence is not None and fence.attempt_id == older.id and fence.epoch == epoch
    monkeypatch.undo()
    assert run_once(store, cpu_adapters(store)) is True
    assert store.get_attempt(operation.project_id, older.id).state == S.COMPLETED
    no_id = store.authorize_attempt(operation, "no-id", M.DRY_RUN, None)
    with store.worker_lock("uncertain"):
        fence = store.claim_attempt("uncertain")
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        _transition(store, fence, S.SUBMITTING, S.RECONCILE_NEEDED)
        store._record_intent(no_id.id, "cancel_intent")
        assert store.apply_cancel_intent(fence).state == S.CANCEL_REQUESTED
    unrelated = store.authorize_attempt(operation, "unrelated", M.DRY_RUN, None)
    assert run_once(store, cpu_adapters(store)) is True
    assert store.get_attempt(operation.project_id, no_id.id).state == S.CANCEL_REQUESTED
    assert store.get_attempt(operation.project_id, unrelated.id).state == S.COMPLETED
    with store._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM provider_receipts WHERE attempt_id=?",
                          (no_id.id,)).fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'").fetchone()[0] == 3
def test_take_registration_and_completion_are_atomic(prepared) -> None:
    store, operation = prepared
    attempt = store.authorize_attempt(operation, "atomic", M.DRY_RUN, None)
    with store.worker_lock("atomic"):
        fence = store.claim_attempt("atomic")
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        adapter = CPUManagedAdapter(store)
        receipt = adapter.submit(adapter.bind(operation, fence), "atomic")
        _transition(store, fence, S.SUBMITTED, S.DOWNLOADING)
        evidence = adapter.download(receipt)
        with sqlite3.connect(store.db_path) as db:
            db.execute("""CREATE TRIGGER reject_completion BEFORE UPDATE ON attempts
                WHEN NEW.state='completed' BEGIN SELECT RAISE(ROLLBACK, 'injected'); END""")
            db.commit()
        with pytest.raises(WorkspaceStoreError):
            TakeService(store).register_output(attempt.id, evidence)
        assert _count(store, "SELECT COUNT(*) FROM takes") == 0
        assert store.get_attempt(operation.project_id, attempt.id).state == S.DOWNLOADING
        with sqlite3.connect(store.db_path) as db:
            db.execute("DROP TRIGGER reject_completion"); db.commit()
        take = TakeService(store).register_output(attempt.id, evidence)
        assert take.output == evidence
        assert store.get_attempt(operation.project_id, attempt.id).state == S.COMPLETED
        assert _count(store, "SELECT COUNT(*) FROM takes") == 1


def test_managed_legacy_guard_uses_db_projection_and_never_legacy_runner(prepared, tmp_path: Path) -> None:
    store, operation = prepared
    attempt = store.authorize_attempt(operation, "legacy-guard", M.DRY_RUN, None)
    with store.worker_lock("guard"):
        for _main, client in _client(store.root):
            legacy = client.post(f"/api/jobs/{operation.managed_job_id}/run")
            assert legacy.status_code == 409
            body = legacy.json()["detail"]
            assert body["code"] == "MANAGED_ATTEMPT_REQUIRES_EXPLICIT_AUTHORIZATION"
            assert body["attempts_url"] == f"/api/projects/{operation.project_id}/attempts"
            status = client.get(f"/api/jobs/{operation.managed_job_id}/status")
            assert status.status_code == 200 and status.json()["managed"] is True
            assert status.json()["attempt_id"] == attempt.id
            assert status.json()["attempt_state"] == "prepared"
            assert not (store.root / "jobs" / operation.managed_job_id).exists()
            assert not (store.root / "jobs" / operation.managed_job_id / "status.json").exists()


def test_worker_starts_after_isolated_active_store_initializes(tmp_path: Path) -> None:
    for _main, client in _client(tmp_path):
        assert not (tmp_path / "workspace.sqlite3").exists()
        project = client.post("/api/projects", json={"name": "Active worker"}).json()
        media = generate_media(tmp_path / "media")
        character = client.post(
            "/api/characters",
            data={"project_id": project["project_id"], "name": "Active performer", "description": ""},
            files={
                "reference_1": (media["primary"].name, media["primary"].read_bytes(), "image/png"),
                "reference_2": (media["secondary"].name, media["secondary"].read_bytes(), "image/png"),
            },
        ).json()["character"]
        timing = client.post(
            f"/api/projects/{project['project_id']}/sources",
            files={"file": (media["source"].name, media["source"].read_bytes(), "video/mp4")},
        ).json()
        scene = client.post(
            f"/api/projects/{project['project_id']}/scenes",
            json={"source_asset_id": timing["asset_id"], "shots": [
                {"id": "pass", "source_range": {"start": 0, "end": 8}, "kind": "pass_through"},
                {"id": "render", "source_range": {"start": 8, "end": 16}, "kind": "render"},
                {"id": "tail", "source_range": {"start": 16, "end": 24}, "kind": "pass_through"},
            ]},
        ).json()
        pin = client.get(f"/api/projects/{project['project_id']}/recipes").json()["profiles"][0]["pin"]
        operation = client.post(
            f"/api/projects/{project['project_id']}/operations/resolve",
            json={"scene_revision_id": scene["id"], "shot_id": "render", "pin": pin,
                  "character_version": [character["character_id"], character["version"]],
                  "seed": 117, "rights_attested": True},
        ).json()
        attempt = client.post(
            f"/api/projects/{project['project_id']}/attempts",
            json={"operation_id": operation["id"], "client_request_id": "active-worker",
                  "mode": "dry_run", "challenger_of": None},
        ).json()
        deadline = time.monotonic() + 15
        state = None
        while time.monotonic() < deadline:
            attempts = client.get(f"/api/projects/{project['project_id']}/attempts").json()
            state = next(item["state"] for item in attempts if item["id"] == attempt["id"])
            if state == "completed":
                break
            time.sleep(0.05)
        assert state == "completed"
        with sqlite3.connect(tmp_path / "workspace.sqlite3") as db:
            assert db.execute("SELECT COUNT(*) FROM takes").fetchone()[0] == 1
            assert db.execute("SELECT COUNT(*) FROM attempt_events WHERE kind='submit_started'").fetchone()[0] == 1


def test_production_view_explicit_cpu_authorization_and_honest_preview_boundary() -> None:
    script = (ROOT / "app/web/m1.js").read_text(encoding="utf-8")
    subprocess.run(["node", "--check", str(ROOT / "app/web/m1.js")], check=True,
                   capture_output=True, text=True)
    assert "/api/projects/${encodeURIComponent(workspace.projectId)}/attempts" in script
    assert "mode: 'dry_run'" in script and "CPU dry_run" in script
    assert "OWNER_BLOCKED" in script and "client_request_id: authorizedRequestKey" in script
    assert "authorizedRequestKey = `m1-${resolvedOperation.fingerprint}`" in script
    assert "cannot enqueue another attempt" in script
    for state in ("prepared", "ready", "submitted", "running", "cancel_requested",
                  "provider_confirmed_cancelled"):
        assert state in script
    assert "no refund is claimed" in script
    assert "Browser playback is not provided" in script
    assert "Request reconciliation" in script and "/reconcile`" in script
    assert "Select attempt controls" in script
    assert "/run" not in script and "URL.createObjectURL" not in script


def test_UNIT_six_method_fresh_submission_is_receipt_first_and_output_durable(prepared):
    store, operation = prepared
    attempt = store.authorize_attempt(operation, "six-fresh", M.DRY_RUN, None)
    calls = []

    class ConfiguredAdapter:
        def preflight(self, op):
            calls.append("preflight")
            return Readiness(True, "UNIT", "six-method configured transport")

        def bind(self, op, fence):
            calls.append("bind")
            assert fence.attempt_id == attempt.id
            asset = store.stage_asset(op.project_id, "unit-binding.json", io.BytesIO(b"{}"),
                                      role="attempt_binding", protected=True)
            return BoundSubmission(op.id, asset.asset_id, asset.sha256, False)

        def submit(self, bound, request_key):
            calls.append("submit")
            body = dict(attempt_id=attempt.id, provider_id="unit-six", request_key=request_key,
                        adapter_version=operation.pin.adapter_version,
                        endpoint_fingerprint=operation.pin.endpoint_fingerprint)
            asset = store.stage_asset(operation.project_id, "unit-receipt.json",
                io.BytesIO(json.dumps(body).encode()), role="provider_receipt", protected=True)
            return Receipt(**body, receipt_asset_id=asset.asset_id, receipt_sha256=asset.sha256)

        def poll(self, receipt):
            calls.append("poll")
            assert store._receipt(store._lookup_attempt(attempt.id)) == receipt
            return RemoteState.COMPLETED

        def download(self, receipt):
            calls.append("download")
            from openjutsu.attempt_worker import _verify_inputs
            cpu = _verify_inputs(store, operation)["cpu_input"]
            source = store.resolve_asset(cpu["asset_id"])
            with source.path.open("rb") as content:
                asset = store.stage_asset(operation.project_id, source.record.filename, content,
                                          role="attempt_output", protected=True)
            return OutputEvidence(asset.asset_id, asset.sha256,
                                  operation.window.expected_decoder_frames,
                                  operation.window.render_timebase, receipt)

        def cancel(self, receipt):
            calls.append("cancel")
            raise AssertionError("ordinary work must not cancel")

    assert run_once(store, {M.DRY_RUN: ConfiguredAdapter()})
    assert store._lookup_attempt(attempt.id).state == S.COMPLETED
    assert calls == ["preflight", "bind", "submit", "poll", "download"]
    assert _count(store, "SELECT COUNT(*) FROM attempt_events WHERE kind='output'") == 1


def test_UNIT_unknown_downloading_pauses_persistently_without_cancel_or_download(prepared, monkeypatch):
    store, operation = prepared
    attempt = store.authorize_attempt(operation, "unknown-download", M.DRY_RUN, None)
    with store.worker_lock("seed"):
        fence = store.claim_attempt("seed")
        _transition(store, fence, S.PREPARED, S.READY)
        _transition(store, fence, S.READY, S.SUBMITTING)
        adapter = CPUManagedAdapter(store)
        adapter.submit(adapter.bind(operation, fence), attempt.client_request_id)
        _transition(store, fence, S.SUBMITTED, S.DOWNLOADING)
        assert store.claim_attempt("seed") is None
    monkeypatch.setattr(CPUManagedAdapter, "poll", lambda *args: RemoteState.UNKNOWN)
    forbidden_calls = []
    def forbidden(*args):
        forbidden_calls.append(True)
        raise AssertionError("UNKNOWN recovery must neither download nor cancel")
    monkeypatch.setattr(CPUManagedAdapter, "download", forbidden)
    monkeypatch.setattr(CPUManagedAdapter, "cancel", forbidden)
    assert _worker(store)
    assert store._lookup_attempt(attempt.id).state == S.RECONCILE_NEEDED
    assert not _worker(WorkspaceStore(store.root))
    assert not forbidden_calls
    unrelated = store.authorize_attempt(operation, "independent-unknown", M.DRY_RUN, None)
    assert _worker(store)
    assert store._lookup_attempt(unrelated.id).state == S.RECONCILE_NEEDED
    assert _count(store, "SELECT COUNT(*) FROM attempt_events WHERE kind='reconcile_paused'") == 2
    assert not _worker(WorkspaceStore(store.root))
    from openjutsu.attempt_worker import _pause_reconcile
    with pytest.raises(WorkspaceStoreError):
        _pause_reconcile(store, fence, store._lookup_attempt(attempt.id))


def test_UNIT_lost_submit_and_no_id_cancel_leave_independent_work_runnable(prepared, monkeypatch):
    store, operation = prepared
    uncertain = store.authorize_attempt(operation, "lost-submit", M.DRY_RUN, None)
    def lost(*args):
        raise RuntimeError("UNIT lost response")
    monkeypatch.setattr(CPUManagedAdapter, "submit", lost)
    with store.worker_lock("lifetime"):
        assert _worker(store)
        assert store._lookup_attempt(uncertain.id).state == S.RECONCILE_NEEDED
        store._record_intent(uncertain.id, "cancel_intent")
        assert _worker(store)
        assert store._lookup_attempt(uncertain.id).state == S.CANCEL_REQUESTED
        monkeypatch.undo()
        unrelated = store.authorize_attempt(operation, "after-loss", M.DRY_RUN, None)
        assert _worker(store)
        assert store._lookup_attempt(unrelated.id).state == S.COMPLETED
        assert not _worker(store)
