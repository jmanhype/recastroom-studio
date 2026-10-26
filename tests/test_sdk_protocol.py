# SPDX-License-Identifier: MIT
"""UNPAID localhost protocol fixture, real comfy-sdk 0.5; NO inference."""
import json
import socket
import threading
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from openjutsu.comfy_sdk_runner import ComfySdkRunner, ComfySdkRunError

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-10-18T00:00:00Z"


@pytest.fixture
def protocol(tmp_path, monkeypatch):
    state = SimpleNamespace(calls=[], assets={}, graph=None, mode="success", name="result.mp4")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, data, status=200):
            raw = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_HEAD(self):
            state.calls.append(("HEAD", self.path))
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            state.calls.append(("POST", self.path))
            body = self.rfile.read(int(self.headers["Content-Length"]))
            if self.path == "/api/v2/assets":
                if state.mode == "upload_error":
                    return self.reply({"error": {"code": "bad_request", "message": "SECRET"}}, 400)
                msg = BytesParser(policy=default).parsebytes(
                    b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + body)
                fields = {part.get_param("name", header="content-disposition"): part.get_payload(decode=True)
                          for part in msg.iter_parts()}
                asset_id = "asset-" + str(len(state.assets))
                state.assets[asset_id] = fields
                return self.reply(dict(id=asset_id, hash=fields["expected_hash"].decode(),
                    size_bytes=len(fields["file"]), content_type=fields["content_type"].decode(),
                    file_path=fields["file_path"].decode(), created_at=STAMP, url=state.url + "/bytes",
                    url_expires_at=STAMP), 201)
            if self.path == "/api/v2/jobs":
                state.graph = json.loads(body)
                state.key = self.headers["Idempotency-Key"]
                if state.mode == "lost_response":
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                return self.reply(job("queued"), 201)
            self.reply({}, 404)

        def do_GET(self):
            state.calls.append(("GET", self.path))
            if self.path == "/api/v2/jobs/job-1":
                persisted = json.loads((tmp_path / "outputs/submission.json").read_text())
                assert persisted["job_id"] == "job-1"  # before first poll
                return self.reply(job("failed" if state.mode == "terminal_error" else "succeeded"))
            if self.path == "/api/v2/assets/generated/content":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"synthetic-output-not-real-mp4")
                return
            self.reply({}, 404)

    def output(node, name, asset):
        return dict(node_id=node, name=name, type="video", content_type="video/mp4", size_bytes=29,
                    id=asset, hash=None, url=state.url + "/bytes", url_expires_at=STAMP)

    def job(status):
        return dict(id="job-1", status=status, created_at=STAMP, started_at=None, completed_at=None,
                    expires_at=STAMP, queue_position=None, progress=None, error=None,
                    outputs=[output("comparison", "comparison.mp4", "comparison"),
                             output("751", state.name, "generated")],
                    urls={"self": "/api/v2/jobs/job-1", "events": "/events", "cancel": "/cancel"})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state.url = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("COMFY_BASE_URL", state.url)
    monkeypatch.setenv("COMFY_SDK_ASSET_BRIDGE", "openjutsu-v1")
    state.workflow = json.loads((ROOT / "workflows/openjutsu_h3_lipsync_local.json").read_text())
    state.inputs = {}
    for name, suffix in (("source", ".mp4"), ("reference_1", ".png"), ("reference_2", ".png")):
        path = tmp_path / (name + suffix)
        path.write_bytes(("synthetic-" + name).encode())
        state.inputs[name] = path
    state.output = tmp_path / "outputs"
    state.run = lambda: ComfySdkRunner(api_key="test-value-local-fixture").run_workflow(
        state.workflow, state.output, **state.inputs)
    yield state
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.mark.parametrize("ref2", [True, False])
def test_real_sdk_content_binding_resume_and_output(protocol, ref2):
    p = protocol
    if not ref2:
        p.inputs["reference_2"] = None
    canonical = json.dumps(p.workflow, sort_keys=True)
    result = p.run()
    assert result[0].read_bytes() == b"synthetic-output-not-real-mp4"
    assert canonical == json.dumps(p.workflow, sort_keys=True)
    graph = p.graph["workflow"]
    assert graph["1189"]["inputs"]["plan"] == ["openjutsu_assets", 0]
    for field, input_name in (("video", "source"), ("global_ref", "reference_1"), ("global_ref2", "reference_2")):
        if p.inputs[input_name] is None:
            assert field not in graph["openjutsu_assets"]["inputs"]
            continue
        ref = graph["openjutsu_assets"]["inputs"][field]
        assert ref["__type"] == "core/ASSET"
        assert p.assets[ref["info"]["id"]]["file"] == p.inputs[input_name].read_bytes()
    assert graph["751"] == p.workflow["751"]
    for key in p.workflow:
        if key != "1189":
            assert graph[key] == p.workflow[key]
    before = len([x for x in p.calls if x[0] == "POST"])
    p.run()  # new client, disk state = restart-like recovery
    assert len([x for x in p.calls if x[0] == "POST"]) == before


def test_missing_before_network(protocol):
    protocol.inputs["source"].unlink()
    with pytest.raises(ValueError, match="Invalid SDK"):
        protocol.run()
    assert protocol.calls == []


def test_bridge_must_be_explicitly_configured(protocol, monkeypatch):
    monkeypatch.delenv("COMFY_SDK_ASSET_BRIDGE")
    with pytest.raises(ComfySdkRunError, match="not been configured"):
        protocol.run()
    assert protocol.calls == []


def test_local_concurrent_duplicates_submit_once(protocol):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(protocol.run) for _ in range(2)]
        results = [future.result(timeout=15) for future in futures]
    assert results[0] == results[1]
    assert protocol.calls.count(("POST", "/api/v2/jobs")) == 1


def test_changed_bytes_cannot_reuse_old_job(protocol):
    protocol.run()
    calls = list(protocol.calls)
    protocol.inputs["source"].write_bytes(b"different synthetic input")
    with pytest.raises(ComfySdkRunError, match="inputs or deployment changed"):
        protocol.run()
    assert calls == protocol.calls


def test_actual_uploaded_bytes_feed_bridge(protocol, monkeypatch, tmp_path):
    # Explicit simulator for server materialization, NOT proof of hosted behavior.
    from test_sdk_assets import bridge
    protocol.run()
    inputs = dict(protocol.graph["workflow"]["openjutsu_assets"]["inputs"])
    root = tmp_path / "simulated-comfy-input"
    root.mkdir()
    for key in ("video", "global_ref", "global_ref2"):
        uploaded = protocol.assets[inputs[key]["info"]["id"]]
        name = uploaded["file_path"].decode()
        (root / name).write_bytes(uploaded["file"])
        inputs[key] = name
    bound = json.loads(bridge(monkeypatch, root).bind(**inputs)[0])
    for key, local in (("video", "source"), ("global_ref", "reference_1"), ("global_ref2", "reference_2")):
        assert (root / bound[key]).read_bytes() == protocol.inputs[local].read_bytes()


def test_upload_failure_is_pre_submit(protocol):
    protocol.mode = "upload_error"
    with pytest.raises(ComfySdkRunError) as error:
        protocol.run()
    assert "SECRET" not in str(error.value)
    state = json.loads((protocol.output / "submission.json").read_text())
    assert state["phase"] == "prepared"
    assert ("POST", "/api/v2/jobs") not in protocol.calls
    protocol.mode = "success"
    protocol.run()
    assert protocol.key == state["key"]


def test_submit_response_loss_is_never_resubmitted(protocol):
    protocol.mode = "lost_response"
    with pytest.raises(ComfySdkRunError):
        protocol.run()
    state = (protocol.output / "submission.json").read_bytes()
    calls = list(protocol.calls)
    with pytest.raises(ComfySdkRunError, match="outcome unknown"):
        protocol.run()
    assert protocol.calls == calls
    assert (protocol.output / "submission.json").read_bytes() == state


@pytest.mark.parametrize("mode,name", [("terminal_error", "result.mp4"), ("success", "../escape.mp4"),
                                      ("success", "C:\\escape.mp4")])
def test_terminal_and_traversal_fail_closed(protocol, mode, name):
    protocol.mode, protocol.name = mode, name
    with pytest.raises(ComfySdkRunError):
        protocol.run()
    assert not (protocol.output / "generated.mp4").exists()
    assert not any("content" in path for method, path in protocol.calls)
    assert json.loads((protocol.output / "submission.json").read_text())["job_id"] == "job-1"
