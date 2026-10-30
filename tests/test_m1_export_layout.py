# SPDX-License-Identifier: MIT
"""Real browser layout, accessibility, export, and attachment-download proof."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from textwrap import dedent

from test_m1_export import _export_fixture
from tools.foundation_runtime import FoundationServer, free_loopback_port


BROWSER_PYTHON = Path(sys.executable)


def _browser_program() -> str:
    return dedent(r'''
        import hashlib
        import json
        from pathlib import Path
        import sys

        from playwright.sync_api import sync_playwright

        base_url, evidence_root, project_id, replay_id = sys.argv[1:]
        evidence_root = Path(evidence_root)
        evidence_root.mkdir(parents=True, exist_ok=True)
        requests = []
        evidence = {"base_url": base_url, "requests": [], "viewports": {}}


        def request_url(url):
            requests.append(url)
            if not url.startswith(base_url + "/"):
                raise AssertionError("non-loopback browser request: " + url)


        def prepare_rows(page):
            page.select_option("#project-select", project_id)
            page.wait_for_function(
                "() => document.querySelectorAll('.m1-export-row').length === 3"
            )
            page.wait_for_function(
                "take => [...document.querySelectorAll('.m1-export-row [data-export-field=take] option')]"
                ".some(option => option.value === take)", arg=replay_id,
            )
            rows = page.locator(".m1-export-row")
            rows.nth(0).locator("[data-export-field=shot]").select_option("tail")
            rows.nth(2).locator("[data-export-action=remove]").click()
            rows.nth(1).locator("[data-export-field=take]").select_option(replay_id)
            rows.nth(0).locator("[data-export-field=source-start]").fill("16")
            rows.nth(0).locator("[data-export-field=source-end]").fill("24")
            rows.nth(1).locator("[data-export-field=source-start]").fill("10")
            rows.nth(1).locator("[data-export-field=source-end]").fill("14")
            rows.nth(1).locator("[data-export-field=keep-start]").fill("2")
            rows.nth(1).locator("[data-export-field=keep-end]").fill("6")

            def row_index(shot):
                values = page.eval_on_selector_all(
                    ".m1-export-row [data-export-field=shot]", "nodes => nodes.map(node => node.value)"
                )
                return values.index(shot)

            rows.nth(row_index("tail")).locator("[data-export-action=later]").click()
            rows.nth(row_index("tail")).locator("[data-export-action=earlier]").click()
            assert page.eval_on_selector_all(
                ".m1-export-row [data-export-field=shot]", "nodes => nodes.map(node => node.value)"
            ) == ["tail", "second"]
            page.evaluate("() => window.M1UI.refresh()")
            assert page.eval_on_selector_all(
                ".m1-export-row [data-export-field=shot]", "nodes => nodes.map(node => node.value)"
            ) == ["tail", "second"]
            assert page.eval_on_selector_all(
                ".m1-export-row [data-export-field=take]", "nodes => nodes.map(node => node.value)"
            ) == ["", replay_id]


        def measure_export(page):
            page.locator("#m1-export-list").scroll_into_view_if_needed()
            payload = page.evaluate("""
                () => {
                  const panel = document.getElementById('m1-export-list');
                  const panelRect = panel.getBoundingClientRect();
                  const fieldNodes = [...panel.querySelectorAll('[data-export-field]')];
                  const actionNodes = [...panel.querySelectorAll('[data-export-action]')];
                  const rectangle = node => {
                    const rect = node.getBoundingClientRect();
                    return {left: rect.left, top: rect.top, right: rect.right,
                            bottom: rect.bottom, width: rect.width, height: rect.height};
                  };
                  return {
                    panel: {...rectangle(panel), clientWidth: panel.clientWidth,
                            scrollWidth: panel.scrollWidth},
                    document: {clientWidth: document.documentElement.clientWidth,
                               scrollWidth: document.documentElement.scrollWidth},
                    rowClasses: [...panel.children].map(row => row.className),
                    fields: fieldNodes.map(node => ({
                      field: node.dataset.exportField, value: node.value,
                      enabled: !node.disabled, rectangle: rectangle(node),
                      label: node.closest('label')?.innerText.trim() || '',
                      labelCount: node.labels.length,
                      clientWidth: node.clientWidth, scrollWidth: node.scrollWidth,
                    })),
                    actions: actionNodes.map(node => ({
                      action: node.dataset.exportAction, text: node.innerText.trim(),
                      enabled: !node.disabled, rectangle: rectangle(node),
                      clientWidth: node.clientWidth, scrollWidth: node.scrollWidth,
                    })),
                  };
                }
            """)
            assert payload["rowClasses"] == ["m1-export-row", "m1-export-row"]
            assert [item["field"] for item in payload["fields"]] == [
                "shot", "take", "source-start", "source-end", "keep-start", "keep-end"
            ] * 2
            assert [item["action"] for item in payload["actions"]] == list(
                ("earlier", "later", "remove")
            ) * 2
            for item in payload["fields"] + payload["actions"]:
                assert item["enabled"] and item["rectangle"]["width"] > 1
                assert item["rectangle"]["height"] > 1
                assert item["scrollWidth"] <= item["clientWidth"] + 1
                for edge in ("right", "bottom"):
                    assert item["rectangle"][edge] <= payload["panel"][edge] + 1
            for item in payload["fields"]:
                assert item["labelCount"] == 1 and item["label"]
                if item["field"].startswith("keep"):
                    assert "automatic window" in item["label"]
            assert payload["fields"][4]["value"] == payload["fields"][5]["value"] == ""
            for item in payload["actions"]:
                assert item["text"] in {"Earlier", "Later", "Remove"}
            assert payload["panel"]["scrollWidth"] <= payload["panel"]["clientWidth"] + 1
            assert payload["document"]["scrollWidth"] <= payload["document"]["clientWidth"] + 1
            return payload


        def focus_order(page):
            page.keyboard.press("Tab")
            selectors = [f"[data-export-field={field}]" for field in (
                "shot", "take", "source-start", "source-end", "keep-start", "keep-end"
            )] + [f"[data-export-action={action}]" for action in (
                "earlier", "later", "remove"
            )]
            page.locator(".m1-export-row").nth(0).locator(selectors[0]).focus()
            order = []
            for selector in selectors:
                facts = page.evaluate("""
                    () => {
                      const node = document.activeElement;
                      const style = getComputedStyle(node);
                      return {field: node.dataset.exportField || '',
                              action: node.dataset.exportAction || '',
                              focusVisible: node.matches(':focus-visible'),
                              outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth};
                    }
                """)
                order.append(facts)
                assert facts["focusVisible"]
                assert facts["outlineStyle"] == "solid" and facts["outlineWidth"] != "0px"
                page.keyboard.press("Tab")
            assert [item["field"] for item in order if item["field"]] == [
                "shot", "take", "source-start", "source-end", "keep-start", "keep-end"
            ]
            assert [item["action"] for item in order if item["action"]] == [
                "earlier", "later", "remove"
            ]
            return order


        def measure_archive(page, width):
            details = page.locator("#archive-panel")
            if details.get_attribute("open") is None:
                page.locator("#archive-panel > summary").click()
            query = page.locator("#archive-query")
            query.fill("local layout only")
            query.focus()
            search = page.locator("#archive-search")
            search.focus()
            payload = page.evaluate("""
                () => {
                  const row = document.querySelector('.archive-search');
                  const query = document.getElementById('archive-query');
                  const search = document.getElementById('archive-search');
                  const rectangle = node => {
                    const rect = node.getBoundingClientRect();
                    return {left: rect.left, top: rect.top, right: rect.right,
                            bottom: rect.bottom, width: rect.width, height: rect.height};
                  };
                  return {rowClass: row.className, query: {...rectangle(query), enabled: !query.disabled},
                          search: {...rectangle(search), enabled: !search.disabled},
                          row: rectangle(row)};
                }
            """)
            for control in ("query", "search"):
                item = payload[control]
                assert item["enabled"] and item["width"] > 1 and item["height"] > 1
                assert item["right"] <= payload["row"]["right"] + 1
                assert item["bottom"] <= payload["row"]["bottom"] + 1
            assert payload["rowClass"] == "archive-search"
            page.locator("#archive-panel").scroll_into_view_if_needed()
            page.screenshot(path=str(evidence_root / f"archive-{width}.png"))
            return payload


        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, channel="chrome", args=["--no-first-run", "--no-default-browser-check"]
            )
            for width, height in ((1440, 768), (390, 844)):
                context = browser.new_context(
                    viewport={"width": width, "height": height}, accept_downloads=True
                )
                context.on("page", lambda child: child.on("request", lambda request: request_url(request.url)))
                page = context.new_page()
                page.on("request", lambda request: request_url(request.url))
                page.goto(base_url, wait_until="domcontentloaded")
                page.wait_for_function("() => Boolean(window.StudioUI)")
                page.evaluate("() => window.StudioUI.finishWalkthrough()")
                page.locator("#advanced-studio > summary").click()
                page.wait_for_selector("#project-select", state="visible")
                prepare_rows(page)
                layout = measure_export(page)
                layout["focusOrder"] = focus_order(page)
                layout["archive"] = measure_archive(page, width)
                page.locator("#m1-export-list").scroll_into_view_if_needed()
                page.screenshot(path=str(evidence_root / f"export-{width}.png"))
                evidence["viewports"][str(width)] = layout
                if width == 1440:
                    page.get_by_role("button", name="Create fixed edit version").click()
                    page.wait_for_function(
                        "() => document.getElementById('m1-export-status').textContent.includes('Fixed edit version')"
                    )
                    page.get_by_role("button", name="Export result").click()
                    page.wait_for_function(
                        "() => document.getElementById('m1-export-status').textContent.includes('Export completed')"
                    )
                    state = page.evaluate("() => window.M1UI.getState()")
                    evidence["editRevision"] = state["editRevision"]
                    evidence["exportRecord"] = state["exportRecord"]
                    with page.expect_download() as download_info:
                        page.locator("#m1-export-download").click()
                    download = download_info.value
                    downloaded = download.path()
                    content = downloaded.read_bytes()
                    destination = evidence_root / "actual-attachment-download.mp4"
                    destination.write_bytes(content)
                    evidence["download"] = {
                        "filename": download.suggested_filename,
                        "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                context.close()
            browser.close()

        assert all(url.startswith(base_url + "/") for url in requests)
        assert not any("/api/archive/sources" in url or "archive.org" in url for url in requests)
        evidence["requests"] = requests
        (evidence_root / "browser-evidence.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8"
        )
    ''')


def test_real_chrome_export_layout_workflow_and_download(tmp_path: Path) -> None:
    store, scene, replay = _export_fixture(tmp_path)
    evidence_root = Path(os.environ.get(
        "OJ_34UC_EVIDENCE", str(tmp_path / "m1-export-layout-evidence")
    ))
    evidence_root.mkdir(parents=True, exist_ok=True)
    server = FoundationServer(free_loopback_port(), store.root, tmp_path / "browser-server.log")
    server.start()
    try:
        browser_home = evidence_root / "browser-home"
        browser_tmp = evidence_root / "browser-tmp"
        browser_home.mkdir(exist_ok=True)
        browser_tmp.mkdir(exist_ok=True)
        environment = {
            "PATH": os.environ["PATH"], "HOME": str(browser_home), "TMPDIR": str(browser_tmp),
        }
        result = subprocess.run(
            [str(BROWSER_PYTHON), "-", server.base_url, str(evidence_root),
             scene.project_id, replay.id],
            input=_browser_program(), text=True, timeout=240, capture_output=True,
            env=environment,
        )
        (evidence_root / "browser-stdout.log").write_text(result.stdout, encoding="utf-8")
        (evidence_root / "browser-stderr.log").write_text(result.stderr, encoding="utf-8")
        assert result.returncode == 0, result.stderr

        evidence = json.loads((evidence_root / "browser-evidence.json").read_text())
        record = evidence["exportRecord"]
        assert evidence["editRevision"]["items"] == [
            {"shot_id": "tail", "take_id": None,
             "source_range": {"start": 16, "end": 24}, "decoder_keep": None,
             "timeline_range": {"start": 0, "end": 8}},
            {"shot_id": "second", "take_id": replay.id,
             "source_range": {"start": 10, "end": 14},
             "decoder_keep": {"start": 2, "end": 6},
             "timeline_range": {"start": 8, "end": 12}},
        ]
        persisted = store.get_export(scene.project_id, record["id"])
        persisted_bytes = store.resolve_asset(str(persisted.asset_id)).path.read_bytes()
        downloaded_bytes = (evidence_root / "actual-attachment-download.mp4").read_bytes()
        persisted_hash = hashlib.sha256(persisted_bytes).hexdigest()
        assert record["sha256"] == persisted.sha256 == persisted_hash
        assert evidence["download"]["sha256"] == persisted_hash
        assert downloaded_bytes == persisted_bytes and len(downloaded_bytes) > 1000
        assert all(url.startswith(server.base_url + "/") for url in evidence["requests"])
        assert not any("/api/archive/sources" in url or "archive.org" in url for url in evidence["requests"])
        for width in ("1440", "390"):
            for name in (f"export-{width}.png", f"archive-{width}.png"):
                assert (evidence_root / name).is_file() and (evidence_root / name).stat().st_size > 1000
    finally:
        server.stop()
