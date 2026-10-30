# SPDX-License-Identifier: MIT
"""Native browser upload proof for strict retained-replay import."""
from __future__ import annotations
import hashlib, http.client, json, os, socket, subprocess, threading, traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys
from textwrap import dedent
from typing import Any
from urllib.parse import urlsplit
from openjutsu.m1_types import ReplayReceipt, ReviewVerdict
from openjutsu.take_service import TakeService
from test_m1_export import _export_fixture
from tools.foundation_runtime import FoundationServer, free_loopback_port
BROWSER_PYTHON = Path(sys.executable)
class _StreamingLoopbackProxy:
    """Forward native bytes to the real server; optionally drop one committed response."""
    def __init__(self, server: FoundationServer, store: Any, evidence: Path, project_id: str, *, fault: bool):
        self._store = store
        self._evidence = evidence
        self._fault = fault
        self.records: list[dict[str, Any]] = []
        self.handler_errors: list[str] = []
        parsed = urlsplit(server.base_url)
        if parsed.hostname != "127.0.0.1":
            raise AssertionError("proxy upstream must remain loopback-only")
        self._upstream_port = int(parsed.port or 80)
        outer = self
        class Handler(BaseHTTPRequestHandler):
            timeout = 5
            def log_message(self, *args: object) -> None:
                return None
            def forward(self) -> None:
                if self.headers.get("Transfer-Encoding") or self.headers.get("Expect"):
                    raise RuntimeError("unsupported HTTP request framing")
                length = self.headers.get("Content-Length")
                if length is None and self.command != "GET":
                    raise RuntimeError("request body length is required")
                remaining = 0 if length is None else int(length)
                if not 0 <= remaining <= 32 * 1024 * 1024:
                    raise RuntimeError("request body outside bounded range")
                upstream = http.client.HTTPConnection(
                    "127.0.0.1", outer._upstream_port, timeout=15)
                try:
                    upstream.putrequest(self.command, self.path, skip_host=True,
                                        skip_accept_encoding=True)
                    for name, value in self.headers.items():
                        if name.lower() != "connection":
                            upstream.putheader(name, value)
                    upstream.putheader("Connection", "close")
                    upstream.endheaders()
                    digest = hashlib.sha256()
                    while remaining:
                        chunk = self.rfile.read(min(65536, remaining))
                        if not chunk:
                            raise RuntimeError("truncated native request")
                        digest.update(chunk)
                        upstream.send(chunk)
                        remaining -= len(chunk)
                    response = upstream.getresponse()
                    body = response.read(1024 * 1024 + 1)
                    if len(body) > 1024 * 1024 or response.read(1):
                        raise RuntimeError("response body outside bounded range")
                    path = self.path.split("?", 1)[0]
                    if self.command == "POST" and path == f"/api/projects/{project_id}/replay-import":
                        outer._record({
                            "status": response.status,
                            "request_bytes": int(length or 0),
                            "request_sha256": digest.hexdigest(),
                            "response": json.loads(body.decode("utf-8")),
                            "sqlite_at_response": _snapshot(outer._store),
                        })
                        if outer._fault:
                            if response.status != 201 or len(outer.records) != 1:
                                raise RuntimeError("armed fault expected actual upstream 201")
                            self.close_connection = True
                            self.connection.shutdown(socket.SHUT_RDWR)
                            self.connection.close()
                            return
                    self.send_response_only(response.status, response.reason)
                    for name, value in response.getheaders():
                        if name.lower() not in ("transfer-encoding", "connection", "content-length"):
                            self.send_header(name, value)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                finally:
                    upstream.close()
            do_GET = forward
            do_POST = forward
        class Server(HTTPServer):
            def handle_error(self, request: object, client_address: object) -> None:
                outer.handler_errors.append(traceback.format_exc())
        self._server = Server(("127.0.0.1", 0), Handler)
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"
        self._thread: threading.Thread | None = None
    def _record(self, record: dict[str, Any]) -> None:
        self.records.append(record)
        self._evidence.parent.mkdir(parents=True, exist_ok=True)
        self._evidence.write_text(json.dumps({
            "scope": "OFFLINE transport fault; not provider execution or H3 qualification",
            "fault_armed": self._fault, "records": self.records,
        }, indent=2), encoding="utf-8")
    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="m1-replay-proxy", daemon=False)
        self._thread.start()
    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                self.handler_errors.append("proxy owner thread did not stop within 5 seconds")
        (self._evidence.parent / "handler-errors.json").write_text(json.dumps(self.handler_errors))
        assert not self.handler_errors, "\n".join(self.handler_errors)
def _strict_receipt(store, take_id: str) -> ReplayReceipt:
    with store._connect() as db:
        row = db.execute("SELECT * FROM qualified_replay_receipts WHERE take_id=?", (take_id,)).fetchone()
    assert row is not None
    payload = dict(row)
    for column in ("take_id", "project_id", "operation_id", "created_at"): payload.pop(column)
    payload["window"] = json.loads(payload.pop("window_json"))
    return ReplayReceipt.from_json(json.dumps(payload, sort_keys=True, separators=(",", ":")))
def _snapshot(store) -> dict[str, int]:
    counts = ("attempts", "takes", "assets", "qualified_replay_receipts", "reviews", "selection_events", "edit_revisions", "exports")
    with store._connect() as db:
        return {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in counts}
def _browser_program() -> str:
    return dedent(r'''
        import json, sys
        from pathlib import Path
        from playwright.sync_api import sync_playwright
        (mode, base_url, evidence_root, project_id, baseline_id, replay_path,
         valid_path, malformed_path, wrong_path) = sys.argv[1:]
        evidence_root = Path(evidence_root); evidence_root.mkdir(parents=True, exist_ok=True)
        import_path = f"/api/projects/{project_id}/replay-import"
        posts = []
        request_posts = []
        request_failures = []
        page_errors = []
        def observed(response):
            if response.request.method == "POST":
                posts.append({"url": response.url, "status": response.status})
        def requested(request):
            if request.method == "POST":
                request_posts.append(request.url)
        def failed(request):
            request_failures.append({"url": request.url, "failure": request.failure})
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, channel="chrome")
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            page.on("response", observed)
            page.on("request", requested)
            page.on("requestfailed", failed)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.goto(base_url, wait_until="domcontentloaded")
            page.select_option("#project-select", project_id)
            page.wait_for_selector("#m1-review-shot option[value=second]", state="attached")
            page.select_option("#m1-review-shot", "second")
            page.wait_for_function("id => document.getElementById('m1-takes').innerText.includes(id)", arg=baseline_id)
            replay_control = page.get_by_label("Retained replay bytes")
            receipt_control = page.get_by_label("Strict receipt JSON")
            button = page.locator("#m1-replay-import")
            assert button.is_disabled()
            def submit(expected, text):
                with page.expect_response(lambda response: response.url.endswith(import_path)) as observed:
                    page.click("#m1-replay-import")
                assert observed.value.status == expected
                page.wait_for_function("text => document.getElementById('m1-replay-status').textContent.includes(text)", arg=text)
            if mode == "negative":
                replay_control.set_input_files(replay_path)
                assert button.is_disabled() and "Select both the actual replay bytes" in page.locator(
                    "#m1-replay-status").inner_text()
                receipt_control.set_input_files(malformed_path)
                assert button.is_enabled(); submit(422, "Replay refused:")
                receipt_control.set_input_files(wrong_path)
                submit(422, "No take, review, selection, or export was created")
                state = page.evaluate("() => window.M1UI.getState()")
                assert state["retainedReplayImport"] is None
                assert state["selectedTakeId"] is None and state["selectionRevision"] == 0
            elif mode == "success":
                replay_control.set_input_files(replay_path)
                assert button.is_disabled()
                receipt_control.set_input_files(valid_path)
                assert button.is_enabled(); submit(201, "not fresh provider execution or H3 qualification")
                state = page.evaluate("() => window.M1UI.getState()")
                imported = state["retainedReplayImport"]["take"]
                visible = page.locator("#m1-replay-lineage").inner_text()
                visible_values = (imported["origin"], "Qualification true", imported["scene_revision_id"],
                                  imported["shot_id"], imported["output"]["sha256"], "Historical verdict keeper")
                assert all(value in visible for value in visible_values)
                assert state["selectedTakeId"] is None and state["selectionRevision"] == 0
                assert state["challengerIncumbentTakeId"] is None
                assert page.locator("#m1-mode option[value=retained_replay]").is_disabled()
            else:
                replay_control.set_input_files(replay_path)
                receipt_control.set_input_files(valid_path)
                assert button.is_enabled()
                page.click("#m1-replay-import")
                page.wait_for_function("text => document.getElementById('m1-replay-status').textContent.includes(text)",
                                       arg="The import may already be recorded; inspect current saved state before retrying")
                page.wait_for_function("() => !document.getElementById('m1-replay-import').disabled")
                page.wait_for_timeout(1000)
                replay_posts = [url for url in request_posts if url.endswith(import_path)]
                assert len(replay_posts) == 1, replay_posts
                assert len(request_failures) == 1, request_failures
                assert request_failures[0]["failure"] == "net::ERR_EMPTY_RESPONSE", request_failures
                assert "No take, review, selection, or export was created" not in page.locator(
                    "#m1-replay-status").inner_text()
                state = page.evaluate("() => window.M1UI.getState()")
                assert state["retainedReplayImport"] is None
                assert state["selectedTakeId"] is None and state["selectionRevision"] == 0
            page.screenshot(path=str(evidence_root / f"replay-{mode}.png"), full_page=True)
            browser.close()
        assert not any(item["url"].endswith(f"/api/projects/{project_id}/attempts") for item in posts)
        assert not page_errors, page_errors
        receipt = {"mode": mode, "posts": posts, "requestPosts": request_posts,
                   "requestFailures": request_failures,
                   "scope": "OFFLINE transport fault; not provider execution or H3 qualification",
                   "importedTake": state["retainedReplayImport"]["take"] if mode == "success" else None}
        (evidence_root / f"browser-evidence-{mode}.json").write_text(json.dumps(receipt, indent=2))
    ''')
def _run_browser(mode: str, server: FoundationServer, store: Any, evidence: Path,
                 project_id: str, baseline_id: str,
                 files: tuple[Path, Path, Path, Path]) -> dict:
    evidence = evidence / mode
    home, temporary = evidence / "browser-home", evidence / "browser-tmp"
    home.mkdir(parents=True, exist_ok=True); temporary.mkdir(parents=True, exist_ok=True)
    proxy = _StreamingLoopbackProxy(
        server, store, evidence / "upstream.json", project_id, fault=mode == "ambiguous")
    proxy.start()
    try:
        result = subprocess.run(
            [str(BROWSER_PYTHON), "-", mode, proxy.base_url, str(evidence), project_id,
             baseline_id, *(str(path) for path in files)],
            input=_browser_program(), text=True, timeout=120, capture_output=True,
            env={"PATH": os.environ["PATH"], "HOME": str(home), "TMPDIR": str(temporary),
                 "PYTHONPATH": os.environ.get("PYTHONPATH", "")},
        )
        (evidence / f"browser-stdout-{mode}.log").write_text(result.stdout, encoding="utf-8")
        (evidence / f"browser-stderr-{mode}.log").write_text(result.stderr, encoding="utf-8")
        assert result.returncode == 0, result.stderr
    finally:
        proxy.stop()
    receipt = json.loads((evidence / f"browser-evidence-{mode}.json").read_text(encoding="utf-8"))
    receipt["upstreamReplayPosts"] = proxy.records
    return receipt
def test_replay_file_and_receipt_upload_with_visible_lineage_and_malformed_refusal(tmp_path: Path):
    store, scene, baseline = _export_fixture(tmp_path)
    receipt = _strict_receipt(store, baseline.id)
    service = TakeService(store)
    service.review(baseline.id, ReviewVerdict.NEEDS_REVIEW, "existing review must remain immutable")
    service.select(scene.project_id, scene.id, baseline.shot_id, baseline.id, 0)
    reviews = store.list_reviews(baseline.id)
    selections = store.list_selections(scene.project_id, scene.id, baseline.shot_id)
    output = store.resolve_asset(baseline.output.asset_id).path.read_bytes()
    replay_path = tmp_path / "retained.nut"; replay_path.write_bytes(output)
    valid_path = tmp_path / "receipt.json"; valid_path.write_text(receipt.to_json(), encoding="utf-8")
    malformed_path = tmp_path / "malformed.json"; malformed_path.write_text("{", encoding="utf-8")
    wrong_path = tmp_path / "wrong-lineage.json"
    wrong_path.write_text(receipt.to_json().replace(f'"{baseline.shot_id}"', '"first"'), encoding="utf-8")
    evidence = Path(os.environ.get("OJ_5EOQ_EVIDENCE", tmp_path / "evidence"))
    server = FoundationServer(free_loopback_port(), store.root, tmp_path / "server.log", test_lifespan="off")
    server.start()
    try:
        before = _snapshot(store)
        files = (replay_path, valid_path, malformed_path, wrong_path)
        refused = _run_browser(
            "negative", server, store, evidence, scene.project_id, baseline.id, files)
        assert [item["status"] for item in refused["posts"] if "replay-import" in item["url"]] == [422, 422]
        assert _snapshot(store) == before
        accepted = _run_browser(
            "success", server, store, evidence, scene.project_id, baseline.id, files)
        assert [item["status"] for item in accepted["posts"] if "replay-import" in item["url"]] == [201]
        after = _snapshot(store)
        assert _strict_receipt(store, baseline.id) == receipt
        assert store.list_reviews(baseline.id) == reviews
        assert store.list_selections(scene.project_id, scene.id, baseline.shot_id) == selections
        unchanged = ("attempts", "reviews", "selection_events", "edit_revisions", "exports")
        assert all(after[table] == before[table] for table in unchanged)
        assert all(after[table] == before[table] + 1 for table in ("takes", "assets", "qualified_replay_receipts"))
        imported = store.get_take(scene.project_id, accepted["importedTake"]["id"])
        assert len(reviews) == 1 and len(selections) == 1
        assert (imported.origin, imported.qualified, imported.output.sha256) == ("retained_replay", True, receipt.output_sha256)
        committed = _snapshot(store)
        known_take_ids = {take.id for take in store.list_attached_takes(
            scene.project_id, scene.id, baseline.shot_id)}
        uncertain = _run_browser(
            "ambiguous", server, store, evidence, scene.project_id, baseline.id, files)
        upstream = uncertain["upstreamReplayPosts"]
        browser_replay_posts = [url for url in uncertain["requestPosts"]
                                if url.endswith("/replay-import")]
        assert len(browser_replay_posts) == 1, browser_replay_posts
        assert len(upstream) == 1 and upstream[0]["status"] == 201, upstream
        assert upstream[0]["request_bytes"] > replay_path.stat().st_size
        assert len(upstream[0]["request_sha256"]) == 64
        uncertain_after = _snapshot(store)
        assert all(uncertain_after[table] == committed[table] for table in unchanged)
        assert all(uncertain_after[table] == committed[table] + 1 for table in (
            "takes", "assets", "qualified_replay_receipts"))
        uncertain_ids = {take.id for take in store.list_attached_takes(
            scene.project_id, scene.id, baseline.shot_id)}
        added_ids = uncertain_ids - known_take_ids
        assert len(added_ids) == 1
        uncertain_imported = store.get_take(scene.project_id, added_ids.pop())
        assert upstream[0]["sqlite_at_response"] == uncertain_after
        assert upstream[0]["response"]["id"] == uncertain_imported.id
        assert store.list_reviews(baseline.id) == reviews
        assert store.list_selections(scene.project_id, scene.id, baseline.shot_id) == selections
        assert (uncertain_imported.origin, uncertain_imported.qualified,
                uncertain_imported.scene_revision_id, uncertain_imported.shot_id,
                uncertain_imported.output.sha256) == ("retained_replay", True, scene.id,
                    baseline.shot_id, receipt.output_sha256)
        registered = store.resolve_asset(uncertain_imported.output.asset_id).path.read_bytes()
        assert hashlib.sha256(registered).hexdigest() == receipt.output_sha256
    finally:
        server.stop()
