# SPDX-License-Identifier: MIT
"""Real browser presentation proof for a durable unknown attempt outcome."""
from __future__ import annotations

import json, os, subprocess
from pathlib import Path
import sys
from textwrap import dedent
from urllib.parse import urlsplit

from openjutsu.m1_types import AttemptEvent, AttemptState as S, ExecutionMode as M
from test_m1_resolution import _resolve, _workspace
from tools.foundation_runtime import FoundationServer, free_loopback_port

BROWSER_PYTHON = Path(sys.executable)


def _browser_program() -> str:
    return dedent(r'''
        import json
        from pathlib import Path
        import sys
        from urllib.parse import urlsplit

        from playwright.sync_api import sync_playwright

        base_url, evidence_root, project_id, attempt_id, request_key = sys.argv[1:]
        evidence_root = Path(evidence_root); evidence_root.mkdir(parents=True, exist_ok=True)
        requests = []

        def observed(request):
            requests.append({"method": request.method, "url": request.url})
            if not request.url.startswith(base_url + "/"):
                raise AssertionError("non-loopback browser request: " + request.url)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, channel="chrome")
            page = browser.new_page(viewport={"width": 1440, "height": 768})
            page.on("request", observed)
            page.goto(base_url, wait_until="domcontentloaded")
            page.select_option("#project-select", project_id)
            page.wait_for_function("id => document.getElementById('m1-attempts').innerText.includes(id)", arg=attempt_id)
            visible = page.locator("#m1-attempts").inner_text()
            assert "Paused unknown outcome" in visible
            assert "reconciliation is required before any conclusion or retry" in visible
            assert attempt_id in visible and "Waiting for the sole worker." not in visible
            public_get = page.evaluate(
                "async project => await (await fetch(`/api/projects/${encodeURIComponent(project)}/attempts`)).json()",
                arg=project_id,
            )
            assert [item["id"] for item in public_get] == [attempt_id]
            assert public_get[0]["state"] == "reconcile_needed"
            assert public_get[0]["client_request_id"] == request_key
            page.get_by_role("button", name="Select attempt controls").click()
            page.get_by_role("button", name="Request reconciliation").click()
            page.wait_for_function(
                "() => document.getElementById('m1-production-note').textContent.includes("
                "'this does not authorize another attempt')"
            )
            before = page.evaluate("() => window.M1UI.getState()")
            page.evaluate("() => window.M1UI.refresh()")
            page.wait_for_timeout(300)
            after = page.evaluate("() => window.M1UI.getState()")
            assert before["attempts"] == after["attempts"] == public_get
            assert after["authorizedRequestKey"] is None
            page.screenshot(path=str(evidence_root / "paused-unknown.png"), full_page=True)
            browser.close()

        post_attempts = [item for item in requests if item["method"] == "POST"
                         and urlsplit(item["url"]).path == f"/api/projects/{project_id}/attempts"]
        reconciles = [item for item in requests if item["method"] == "POST" and item["url"].endswith(
            f"/attempts/{attempt_id}/reconcile")]
        assert not post_attempts and len(reconciles) == 1
        receipt = {
            "fixture": "OFFLINE presentation fixture; not live-provider lookup/recovery",
            "publicGet": public_get, "beforeState": before, "afterState": after,
            "requests": requests, "authorizePostCount": len(post_attempts),
            "reconcilePostCount": len(reconciles),
        }
        (evidence_root / "browser-evidence.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    ''')


def test_reconcile_needed_is_visible_paused_and_does_not_resubmit(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    operation = _resolve(store, scene_id, tuple(character))
    attempt = store.authorize_attempt(operation, "offline-unknown", M.DRY_RUN, None)
    with store.worker_lock("offline-worker"):
        fence = store.claim_attempt("offline-worker")
        assert fence is not None and fence.attempt_id == attempt.id
        for expected, target in ((S.PREPARED, S.READY), (S.READY, S.SUBMITTING),
                                 (S.SUBMITTING, S.RECONCILE_NEEDED)):
            store.transition_attempt(fence, expected, AttemptEvent(target.value, "{}"))
    evidence_root = Path(os.environ.get("OJ_A377_EVIDENCE", str(tmp_path / "evidence")))
    evidence_root.mkdir(parents=True, exist_ok=True)
    (evidence_root / "browser-home").mkdir()
    (evidence_root / "browser-tmp").mkdir()
    server = FoundationServer(free_loopback_port(), store.root, tmp_path / "server.log", test_lifespan="off")
    server.start()
    try:
        result = subprocess.run(
            [str(BROWSER_PYTHON), "-", server.base_url, str(evidence_root),
             operation.project_id, attempt.id, attempt.client_request_id],
            input=_browser_program(), text=True, timeout=120, capture_output=True,
            env={"PATH": os.environ["PATH"], "HOME": str(evidence_root / "browser-home"),
                 "TMPDIR": str(evidence_root / "browser-tmp")},
        )
        (evidence_root / "browser-stdout.log").write_text(result.stdout, encoding="utf-8")
        (evidence_root / "browser-stderr.log").write_text(result.stderr, encoding="utf-8")
        assert result.returncode == 0, result.stderr
    finally:
        server.stop()
    persisted = store.get_attempt(operation.project_id, attempt.id)
    assert persisted.state is S.RECONCILE_NEEDED
    assert persisted.client_request_id == attempt.client_request_id
    assert [item.id for item in store.list_attempts(operation.project_id)] == [attempt.id]
    evidence = json.loads((evidence_root / "browser-evidence.json").read_text())
    assert evidence["fixture"].startswith("OFFLINE presentation fixture")
    assert evidence["authorizePostCount"] == 0 and evidence["reconcilePostCount"] == 1
