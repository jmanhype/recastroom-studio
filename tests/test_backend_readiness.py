# SPDX-License-Identifier: MIT
"""Fail-closed legacy renderer readiness coverage.

Transport behavior is exercised through a clearly labelled loopback HTTP
protocol fixture. No external renderer or GPU is contacted.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastapi.testclient import TestClient
import pytest
import requests

from openjutsu import readiness


VALID_SYSTEM_STATS = {
    "system": {"comfyui_version": "fixture", "python_version": "fixture"},
    "devices": [{"name": "loopback-fixture-device"}],
}


class LoopbackComfyProtocolFixture:
    """Small real-HTTP fixture that models only ComfyUI readiness responses."""

    def __init__(self, mode: str, delay: float = 0.0) -> None:
        self.mode = mode
        self.delay = delay
        self.requests: list[tuple[str, str]] = []
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def _record(self) -> None:
                fixture.requests.append((self.command, self.path))

            def _respond(self, status: int, body: bytes, content_type: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                self._record()
                if fixture.delay:
                    threading.Event().wait(fixture.delay)
                if self.path != "/system_stats":
                    self._respond(404, b"not found", "text/plain")
                elif fixture.mode == "valid":
                    self._respond(200, json.dumps(VALID_SYSTEM_STATS).encode(), "application/json")
                elif fixture.mode == "schema":
                    payload = {"system": [], "devices": {}}
                    self._respond(200, json.dumps(payload).encode(), "application/json")
                elif fixture.mode == "noncomfy":
                    self._respond(200, b'{"message":"not comfy"}', "application/json")
                elif fixture.mode == "malformed":
                    self._respond(200, b'{"system":', "application/json")
                elif fixture.mode == "http_error":
                    self._respond(503, b"renderer unavailable", "text/plain")
                elif fixture.mode == "redirect":
                    self.send_response(302)
                    self.send_header("Location", "/other")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                else:
                    self._respond(500, b"fixture mode error", "text/plain")

            def do_POST(self) -> None:
                self._record()
                self._respond(405, b"readiness is read-only", "text/plain")

            def log_message(self, format: str, *args: object) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> "LoopbackComfyProtocolFixture":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"


@contextmanager
def loopback_protocol(mode: str, delay: float = 0.0):
    fixture = LoopbackComfyProtocolFixture(mode, delay).start()
    try:
        yield fixture
    finally:
        fixture.stop()


@contextmanager
def closed_loopback_url():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.close()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        pass


@contextmanager
def configured_app(tmp_path: Path, backend: str, comfy_url: str = "http://127.0.0.1:9"):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = replace(
        main.SETTINGS,
        backend=backend,
        comfy_url=comfy_url,
        data_dir=tmp_path,
    )
    main.JOB_STATUS.clear()
    main.JOB_LOCKS.clear()
    try:
        yield main
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)


def prepared_job(tmp_path: Path, job_id: str = "a123456789ab") -> Path:
    job_dir = tmp_path / "jobs" / job_id
    job_dir.mkdir(parents=True)
    (job_dir / "job.json").write_text('{"job_id": "fixture"}\n', encoding="utf-8")
    (job_dir / "workflow.json").write_text('{"fixture": true}\n', encoding="utf-8")
    return job_dir


def assert_health_contract(payload: dict) -> None:
    assert payload["ok"] is True
    assert payload["workflow"] == "openjutsu_h3_lipsync_local.json"
    assert payload["workflow_exists"] is True
    assert payload["backend"] == "legacy"


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        ("schema", "renderer_schema_mismatch"),
        ("noncomfy", "renderer_schema_mismatch"),
        ("malformed", "renderer_malformed_response"),
        ("http_error", "renderer_http_error"),
        ("redirect", "renderer_redirect"),
    ],
)
def test_health_reports_sanitized_legacy_protocol_failures(tmp_path, mode, code):
    with loopback_protocol(mode) as fixture:
        with configured_app(tmp_path, "legacy", fixture.url) as main:
            with TestClient(main.app) as client:
                response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert_health_contract(payload)
    assert payload["renderer_ready"] is False
    assert payload["renderer"]["checked"] is True
    assert payload["renderer"]["code"] == code
    assert payload["renderer"]["message"]
    assert fixture.requests == [("GET", "/system_stats")]


def test_health_reports_offline_refusal_without_mutation_or_render_post(tmp_path):
    with closed_loopback_url() as url:
        with configured_app(tmp_path, "legacy", url) as main:
            job_dir = prepared_job(tmp_path)
            before = {path.name: path.read_bytes() for path in job_dir.iterdir()}
            with TestClient(main.app) as client:
                health = client.get("/api/health")
                run = client.post(f"/api/jobs/{job_dir.name}/run")

    assert health.status_code == 200
    assert health.json()["renderer"]["code"] == "renderer_unreachable"
    assert run.status_code == 503
    assert run.json()["detail"]["code"] == "renderer_unreachable"
    assert "unreachable" in run.json()["detail"]["message"]
    assert {path.name: path.read_bytes() for path in job_dir.iterdir()} == before
    assert not (job_dir / "status.json").exists()


def test_health_times_out_through_real_loopback_http(tmp_path, monkeypatch):
    monkeypatch.setattr(readiness, "LEGACY_READINESS_TIMEOUT", (0.1, 0.1))
    with loopback_protocol("valid", delay=0.35) as fixture:
        with configured_app(tmp_path, "legacy", fixture.url) as main:
            with TestClient(main.app) as client:
                response = client.get("/api/health")

    payload = response.json()
    assert payload["renderer_ready"] is False
    assert payload["renderer"]["code"] == "renderer_timeout"
    assert fixture.requests == [("GET", "/system_stats")]


def test_exception_details_are_sanitized(tmp_path, monkeypatch):
    def leaking_transport(*args: object, **kwargs: object) -> requests.Response:
        raise requests.ConnectionError("http://user:private-detail-marker@127.0.0.1:9/system_stats")

    monkeypatch.setattr(readiness, "_loopback_safe_get", leaking_transport)
    with configured_app(tmp_path, "legacy", "http://127.0.0.1:9") as main:
        with TestClient(main.app) as client:
            response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["renderer"]["code"] == "renderer_unreachable"
    assert "private-detail-marker" not in response.text
    assert "/system_stats" not in response.text


def test_legacy_run_uses_a_fresh_successful_check_for_recovery(tmp_path, monkeypatch):
    calls: list[str] = []

    def runner(job_id: str) -> None:
        calls.append(job_id)

    monkeypatch.setattr(main := __import__("app.main", fromlist=["main"]), "_run_legacy_job", runner)
    with loopback_protocol("http_error") as fixture:
        with configured_app(tmp_path, "legacy", fixture.url) as current_main:
            job_dir = prepared_job(tmp_path)
            with TestClient(current_main.app) as client:
                disconnected = client.get("/api/health")
                assert disconnected.json()["renderer_ready"] is False
                fixture.mode = "valid"
                recovered = client.post(f"/api/jobs/{job_dir.name}/run")
                queued_memory = dict(current_main.JOB_STATUS)

    assert recovered.status_code == 200
    assert recovered.json()["state"] == "queued"
    assert calls == [job_dir.name]
    assert fixture.requests == [("GET", "/system_stats"), ("GET", "/system_stats")]
    assert queued_memory[job_dir.name]["state"] == "queued"


@pytest.mark.parametrize("job_id", ["bad-id", "b123456789ab"], ids=["invalid", "missing"])
def test_missing_and_invalid_jobs_retain_404_before_readiness(tmp_path, job_id):
    with loopback_protocol("http_error") as fixture:
        with configured_app(tmp_path, "legacy", fixture.url) as main:
            with TestClient(main.app) as client:
                response = client.post(f"/api/jobs/{job_id}/run")

    assert response.status_code == 404
    assert fixture.requests == []


def test_active_jobs_retain_409_before_readiness(tmp_path):
    with loopback_protocol("http_error") as fixture:
        with configured_app(tmp_path, "legacy", fixture.url) as main:
            job_dir = prepared_job(tmp_path)
            main.JOB_STATUS[job_dir.name] = {"state": "generating"}
            with TestClient(main.app) as client:
                response = client.post(f"/api/jobs/{job_dir.name}/run")

    assert response.status_code == 409
    assert response.json()["detail"] == "Job is already generating"
    assert fixture.requests == []
    assert not (job_dir / "status.json").exists()


def test_dry_run_and_sdk_semantics_remain_unchanged(tmp_path, monkeypatch):
    dry_calls: list[str] = []
    sdk_calls: list[str] = []
    monkeypatch.setattr(
        __import__("app.main", fromlist=["main"]),
        "_run_dry_run_job",
        lambda job_id: dry_calls.append(job_id),
    )
    monkeypatch.setattr(
        __import__("app.main", fromlist=["main"]),
        "_run_sdk_job",
        lambda job_id: sdk_calls.append(job_id),
    )

    for backend, calls in (("dry_run", dry_calls), ("sdk", sdk_calls)):
        with configured_app(tmp_path, backend, "http://127.0.0.1:9") as main:
            job_dir = prepared_job(tmp_path, f"b123456789{backend[:2]}")
            with TestClient(main.app) as client:
                health = client.get("/api/health")
                run = client.post(f"/api/jobs/{job_dir.name}/run")
            queued_memory = dict(main.JOB_STATUS)

        assert health.json()["backend"] == backend
        assert health.json()["renderer"]["checked"] is (backend == "dry_run")
        if backend == "sdk":
            assert health.json()["renderer_ready"] is False
            assert health.json()["renderer"]["code"] == "sdk_unchecked"
        assert run.status_code == 200
        assert calls == [job_dir.name]
        assert queued_memory[job_dir.name]["state"] == "queued"


def test_ui_guard_preserves_prepared_state_and_requires_fresh_check():
    source = (Path(__file__).resolve().parents[1] / "app/web/studio.js").read_text(encoding="utf-8")

    assert "renderer_ready === true" in source
    assert "Prepared files and permissions are preserved." in source
    assert "const verifiedHealth = await checkHealth();" in source
    assert "RUN BLOCKED" in source
    assert "before queueing or uploading" in source
    assert "Check connection again" in (Path(__file__).resolve().parents[1] / "app/web/index.html").read_text(encoding="utf-8")


def test_ui_distinguishes_proven_legacy_guard_from_unknown_503():
    source = (Path(__file__).resolve().parents[1] / "app/web/studio.js").read_text(encoding="utf-8")

    assert "return Array.isArray(detail) ? errorText(detail) : publicMessage(detail);" in source
    assert "detail.code.startsWith('renderer_')" in source
    assert "if (error.provesNoSubmission)" in source
    assert "$('health-retry').hidden = false;" in source
    assert "renderer disconnected" in source
    assert "No run request was sent." in source
    assert "Run not submitted:" in source
    assert "The server refused the run before queueing or uploading." in source
