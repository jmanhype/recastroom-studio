# SPDX-License-Identifier: MIT
"""Native same-shot challenger authorization with the real worker and browser."""
from __future__ import annotations

import json, os, sqlite3, subprocess, time
from pathlib import Path
import sys
from textwrap import dedent

import requests
from openjutsu.m1_types import ExecutionMode as M
from test_m1_resolution import _resolve, _workspace
from tools.foundation_runtime import FoundationServer, free_loopback_port

BROWSER_PYTHON = Path(sys.executable)


def _browser_program() -> str:
    return dedent(r'''
        import json
        from pathlib import Path
        import sys

        from playwright.sync_api import sync_playwright

        base_url, evidence_root, project_id, incumbent_take_id = sys.argv[1:]
        evidence_root = Path(evidence_root); evidence_root.mkdir(parents=True, exist_ok=True)
        posts, statuses = [], []

        def request_observed(request):
            if request.method == "POST" and f"/api/projects/{project_id}/attempts" in request.url:
                posts.append({"url": request.url, "body": request.post_data})

        def response_observed(response):
            if response.request.method == "POST" and f"/api/projects/{project_id}/attempts" in response.url:
                statuses.append({"url": response.url, "status": response.status})

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, channel="chrome")
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            page.on("request", request_observed); page.on("response", response_observed)
            page.goto(base_url, wait_until="domcontentloaded")
            page.wait_for_function("() => Boolean(window.StudioUI)")
            page.locator("#advanced-studio > summary").click()
            page.wait_for_selector("#project-select", state="visible")
            page.select_option("#project-select", project_id)
            page.wait_for_selector("#character-select option:not([value=''])", state="attached")
            page.select_option("#character-select", index=1)
            page.wait_for_selector("#m1-shot-select option[value=second]", state="attached")
            page.select_option("#m1-shot-select", "second")
            page.check("#m1-rights"); page.click("#m1-resolve")
            page.wait_for_function("() => document.getElementById('m1-resolve-note').textContent.includes("
                "'No execution attempt, submission, renderer connection, or spending was created')")
            page.select_option("#m1-review-shot", "second")
            page.wait_for_selector(f"#m1-incumbent-select option[value={incumbent_take_id}]", state="attached")
            options = page.locator("#m1-incumbent-select").evaluate("node => Array.from(node.options).map("
                "option => ({value: option.value, label: option.text}))")
            assert [item["value"] for item in options if item["value"]] == [incumbent_take_id]
            assert page.locator("#m1-challenger-authorize").is_disabled()
            page.select_option("#m1-incumbent-select", incumbent_take_id)
            assert not posts and page.locator("#m1-challenger-authorize").is_disabled()
            page.check("#m1-challenger-rights")
            assert page.locator("#m1-challenger-authorize").is_enabled()
            assert page.locator("#m1-authorize").is_disabled()
            page.click("#m1-challenger-authorize")
            page.wait_for_function("() => { const state = window.M1UI.getState(); return state.challengerAttemptId"
                " && state.attempts.some(item => item.id === state.challengerAttemptId"
                " && item.state === 'completed'); }")
            first_state = page.evaluate("() => window.M1UI.getState()")
            page.click("#m1-challenger-authorize")
            page.wait_for_function("() => document.getElementById('m1-challenger-note').textContent.includes("
                "'cannot enqueue another attempt')")
            final_state = page.evaluate("() => window.M1UI.getState()")
            assert len(posts) == 2 and first_state["challengerRequestKey"] == final_state["challengerRequestKey"]
            assert len(final_state["challengerRequestKey"]) <= 128
            page.locator("#m1-authorize").locator("xpath=ancestor::section[1]").screenshot(
                path=str(evidence_root / "challenger-ui.png"))
            browser.close()

        receipt = {
            "authorizationPosts": posts, "authorizationStatuses": statuses,
            "firstState": first_state, "finalState": final_state, "options": options,
        }
        (evidence_root / "browser-evidence.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    ''')


def test_same_shot_challenger_ui_is_idempotent_and_selective(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path); character = tuple(character)
    first = _resolve(store, scene_id, character, shot_id="first")
    second = _resolve(store, scene_id, character, shot_id="second")
    store.authorize_attempt(first, "unaffected-baseline", M.DRY_RUN, None)
    incumbent = store.authorize_attempt(second, "incumbent-baseline", M.DRY_RUN, None)

    def api_takes(http: requests.Session, shot_id: str) -> list[dict]:
        response = http.get(f"{server.base_url}/api/projects/{first.project_id}/scene-revisions/{scene_id}/takes",
                            params={"shot_id": shot_id}, timeout=5)
        assert response.status_code == 200, response.text
        return response.json()

    def take_rows() -> dict[str, dict[str, str]]:
        with sqlite3.connect(f"file:{store.root / 'workspace.sqlite3'}?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT take_id,scene_revision_id,shot_id,attempt_id,operation_id,output_sha256"
                              " FROM takes ORDER BY created_at,take_id").fetchall()
        return {row["take_id"]: dict(row) for row in rows}

    evidence_root = Path(os.environ.get("OJ_C1PP_EVIDENCE", str(tmp_path / "evidence")))
    (evidence_root / "browser-home").mkdir(parents=True, exist_ok=True)
    (evidence_root / "browser-tmp").mkdir(parents=True, exist_ok=True)
    server = FoundationServer(free_loopback_port(), store.root, tmp_path / "server.log")
    server.start()
    try:
        with requests.Session() as http:
            deadline = time.monotonic() + 30
            while True:
                attempts = http.get(f"{server.base_url}/api/projects/{first.project_id}/attempts", timeout=5).json()
                states = {item["client_request_id"]: item["state"] for item in attempts}
                if all(state == "completed" for state in states.values()) or time.monotonic() > deadline:
                    break
                time.sleep(0.1)
            assert set(states.values()) == {"completed"}
            before_rows = take_rows()
            before_first, before_second = api_takes(http, "first"), api_takes(http, "second")
            incumbent_take = next(item for item in before_second if item["attempt_id"] == incumbent.id)
            result = subprocess.run(
                [str(BROWSER_PYTHON), "-", server.base_url, str(evidence_root), first.project_id,
                 incumbent_take["id"]], input=_browser_program(), text=True, timeout=120,
                capture_output=True, env={"PATH": os.environ["PATH"], "HOME": str(evidence_root / "browser-home"),
                "TMPDIR": str(evidence_root / "browser-tmp")},
            )
            (evidence_root / "browser-stdout.log").write_text(result.stdout, encoding="utf-8")
            (evidence_root / "browser-stderr.log").write_text(result.stderr, encoding="utf-8")
            assert result.returncode == 0, result.stderr
            after_first, after_second = api_takes(http, "first"), api_takes(http, "second")
    finally:
        server.stop()

    receipt = json.loads((evidence_root / "browser-evidence.json").read_text(encoding="utf-8"))
    bodies = [json.loads(item["body"]) for item in receipt["authorizationPosts"]]
    assert [item["status"] for item in receipt["authorizationStatuses"]] == [201, 200]
    assert all(set(body) == {"operation_id", "client_request_id", "mode", "challenger_of"} for body in bodies)
    request_key = bodies[0]["client_request_id"]
    assert bodies[1]["client_request_id"] == request_key and len(request_key) <= 128
    assert {body["mode"] for body in bodies} == {"dry_run"}
    assert {body["challenger_of"] for body in bodies} == {incumbent.id}
    with sqlite3.connect(f"file:{store.root / 'workspace.sqlite3'}?mode=ro", uri=True) as db:
        durable = db.execute("SELECT client_request_id,challenger_of,state,COUNT(*) FROM attempts"
                             " WHERE client_request_id=? GROUP BY client_request_id,challenger_of,state",
                             (request_key,)).fetchall()
    assert durable == [(request_key, incumbent.id, "completed", 1)]
    after_rows = take_rows()
    assert {key: value for key, value in after_rows.items() if key in before_rows} == before_rows
    old_attempts = {item["attempt_id"] for item in before_rows.values()}
    challenger_rows = [row for row in after_rows.values() if row["attempt_id"] not in old_attempts]
    assert len(challenger_rows) == 1 and challenger_rows[0]["shot_id"] == "second"
    assert challenger_rows[0]["scene_revision_id"] == scene_id
    assert after_first == before_first and len(after_second) == len(before_second) + 1
    assert any(item["id"] == before_second[0]["id"] and item["output"]["sha256"] == before_second[0]["output"]["sha256"]
               for item in after_second)
