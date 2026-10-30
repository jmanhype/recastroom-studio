# SPDX-License-Identifier: MIT
"""Strict timing, actual HTTP/SQLite/loader lineage and native Chrome resolve proof."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from fractions import Fraction
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from textwrap import dedent

import pytest
import requests

from openjutsu.m1_types import WordTiming, WordTimingInterval, WindowMap, public_json
from openjutsu.pipeline import _managed_words
from openjutsu.recipe_service import OFFLINE_PIN
from openjutsu.timing import WordInterval, format_word_schedule, load_whisper_words
from test_m1_resolution import _workspace
from tools.foundation_runtime import FoundationServer, free_loopback_port

TOLERANCE = 1e-12  # seconds; no endpoint snapping or duration expansion
BROWSER_PYTHON = sys.executable


def _timing(source_id: str = "source", digest: str = "a" * 64,
            start: float = 9 / 24, end: float = 10 / 24) -> dict:
    return {"source_asset_id": source_id, "source_sha256": digest,
            "words": [{"start": start, "end": end, "word": "hello"}]}


def _invalid_payloads() -> list[dict]:
    cases = []
    for field, values in {
        "start": [True, "0", None, float("nan"), float("inf"), -float("inf"), -1, 1, 10**400],
        "end": [False, "1", None, float("nan"), float("inf"), -float("inf"), 0, -1],
        "word": [None, 7, "", " leading", "trailing ", "x" * 129, "a\x00b", "a\x1fb", "a\x7fb", "\ud800"],
    }.items():
        for value in values:
            case = _timing()
            case["words"][0][field] = value
            cases.append(case)
    for words in ([], [_timing()["words"][0]] * 513, [None], "words",
                  [{"start": 0, "end": .5, "word": "a"}, {"start": .4, "end": .6, "word": "b"}],
                  [{"start": .6, "end": .7, "word": "a"}, {"start": .1, "end": .2, "word": "b"}]):
        cases.append({**_timing(), "words": words})
    for field, value in (("source_asset_id", "../source"), ("source_sha256", "A" * 64),
                         ("extra", True), ("source_sha256", None)):
        cases.append({**_timing(), field: value})
    extra = _timing()
    extra["words"][0]["extra"] = True
    cases.append(extra)
    missing = _timing()
    del missing["words"][0]["end"]
    cases.append(missing)
    return cases


@pytest.mark.parametrize("payload", _invalid_payloads())
def test_strict_domain_rejects_constructor_and_json(payload: dict) -> None:
    for construct in (lambda: WordTiming(**payload), lambda: WordTiming.from_json(payload),
                      lambda: WordTiming.from_json(json.dumps(payload))):
        with pytest.raises((ValueError, TypeError)):
            construct()


def test_normalized_frozen_domain_and_interval_constructor() -> None:
    interval = WordTimingInterval(-0.0, 1, "café😀")
    assert interval.start == 0.0 and math.copysign(1, interval.start) == 1
    assert type(interval.end) is float and interval.word == "café😀"
    dto = WordTiming("source", "a" * 64, (interval, WordTimingInterval(1, 2, "B")))
    assert WordTiming.from_json(dto.to_json()) == dto
    assert isinstance(dto.words, tuple)
    for record, field in ((dto, "words"), (interval, "start")):
        with pytest.raises(FrozenInstanceError):
            setattr(record, field, None)
    for payload in _invalid_payloads()[:27]:
        with pytest.raises((ValueError, TypeError)):
            WordTimingInterval(**payload["words"][0])
    with pytest.raises(ValueError):
        WordTiming.from_json([])
    assert len(WordTiming("source", "a" * 64,
        tuple(WordTimingInterval(i, i + 1, "x") for i in range(512))).words) == 512
    canonical = {"schema_version": 1, "coordinate": "original_source_seconds",
                 "source_sha256": "a" * 64, "segments": [{"words": [{"start": 0.0, "end": 1.0, "word": "x"}]}]}
    assert hashlib.sha256(public_json(canonical).encode()).digest() != hashlib.sha256(
        public_json({**canonical, "source_sha256": "b" * 64}).encode()).digest()


def _counts(store) -> dict[str, int]:
    with store._connect() as db:
        return {name: db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("operations", "preparation_bindings", "assets", "attempts")}


def _verify_lineage(store, operation: dict, timing: dict | None) -> tuple[dict, dict]:
    manifest = json.loads(operation["canonical_json"])
    digest = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert operation["fingerprint"] == digest(public_json(manifest))
    assert manifest["recipe"]["h3_qualified"] is False
    assert all(token not in operation["canonical_json"] for token in
               (str(store.root), "asset_id", "filename", "word-timing.json", "hello"))
    binding = store.get_preparation_binding(operation["project_id"], operation["id"])
    asset = store.resolve_asset(binding.binding_asset_id)
    raw = asset.path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == binding.binding_sha256 == asset.record.sha256
    assert asset.record.protected and asset.record.role == "preparation_binding"
    envelope = json.loads(raw)
    assert envelope["operation_fingerprint"] == operation["fingerprint"]
    assert digest(envelope["word_schedule_content"]) == envelope["word_schedule_sha256"]
    assert envelope["word_schedule_sha256"] == manifest["prompt"]["word_schedule_sha256"]
    path = store.root / "managed/jobs" / operation["managed_job_id"] / "word-timing.json"
    if timing is None:
        assert "word_timing" not in manifest and "word_timing" not in envelope
        assert not path.exists() and "word_timing_sha256" not in operation["canonical_json"]
    else:
        original = WordTiming.from_json(timing)
        expected = {"schema_version": 1, "coordinate": "original_source_seconds",
                    "source_sha256": original.source_sha256,
                    "segments": [{"words": json.loads(original.to_json())["words"]}]}
        content = public_json(expected)
        lineage = manifest["word_timing"]
        assert path.read_bytes() == content.encode("utf-8") and content.endswith("\n")
        assert set(lineage) == {"coordinate", "source_sha256", "word_timing_sha256",
                                "original_word_count", "clipped_word_count"}
        assert envelope["word_timing"] == {**lineage, "canonical_content": content}
        assert lineage["word_timing_sha256"] == digest(content)
        assert lineage["source_sha256"] == original.source_sha256
        assert lineage["original_word_count"] == len(original.words)
        loaded = load_whisper_words(path)
        assert loaded == [WordInterval(w.start, w.end, w.word) for w in original.words]
        effective = _managed_words(loaded, WindowMap.from_json(operation["window"]), Fraction(24))
        assert lineage["clipped_word_count"] == len(effective)
        assert format_word_schedule(list(effective), 24) == envelope["word_schedule_content"]
        assert digest(content + " ") != lineage["word_timing_sha256"]
        changed = deepcopy(envelope)
        changed["word_timing"]["canonical_content"] += " "
        assert hashlib.sha256(json.dumps(changed, sort_keys=True, separators=(",", ":")).encode()).hexdigest() != binding.binding_sha256
    assert _counts(store)["attempts"] == 0
    return manifest, envelope


def test_managed_word_timing_ownership_digest_source_offset_and_ui_resolve(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    project = store.list_projects()[0].project_id
    scene = store.get_scene_revision(project, scene_id)
    timing = _timing(scene.source.asset_id, scene.source.sha256)
    body = {"scene_revision_id": scene_id, "shot_id": "second", "pin": json.loads(OFFLINE_PIN.to_json()),
            "character_version": character, "seed": 117, "rights_attested": True}
    evidence = Path(os.environ.get("OJ_LUOK_EVIDENCE", str(tmp_path / "evidence")))
    evidence.mkdir(parents=True, exist_ok=True)
    server = FoundationServer(free_loopback_port(), store.root, evidence / "server.log")
    server.start()
    try:
        with requests.Session() as http:
            http.trust_env = False
            url = f"{server.base_url}/api/projects/{project}/operations/resolve"
            def post(payload: dict, expected: int = 201) -> dict:
                response = http.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=30)
                assert response.status_code == expected, response.text
                assert str(store.root) not in response.text
                return response.json()
            invalids = _invalid_payloads()
            for case in invalids:
                if case.get("source_asset_id") == "source":
                    case["source_asset_id"] = scene.source.asset_id
                if case.get("source_sha256") == "a" * 64:
                    case["source_sha256"] = scene.source.sha256
            foreign = store.create_project("foreign")
            source_bytes = store.resolve_asset(scene.source.asset_id).path.read_bytes()
            for owner, role, protected in ((project, "source", True), (foreign.project_id, "source", True),
                                           (project, "source", False), (project, "reference_1", True)):
                asset = store.stage_asset(owner, "other.mp4", io.BytesIO(source_bytes), role=role, protected=protected)
                invalids.append(_timing(asset.asset_id, asset.sha256))
            invalids.extend([{**timing, "source_sha256": "b" * 64},
                             _timing(scene.source.asset_id, scene.source.sha256, .9, math.nextafter(1, math.inf))])
            before = _counts(store)
            for invalid in invalids:
                post({**body, "word_timing": invalid}, 422)
                assert _counts(store) == before and not (store.root / "managed").exists()
            post({**body, "extra": True, "word_timing": timing}, 422)
            source_path = store.resolve_asset(scene.source.asset_id).path
            source_path.write_bytes(source_bytes + b"tampered")
            try:
                post({**body, "word_timing": timing}, 409)
                assert _counts(store) == before and not (store.root / "managed").exists()
            finally:
                source_path.write_bytes(source_bytes)
            omitted = post(body)
            null = post({**body, "word_timing": None})
            legacy, empty = _verify_lineage(store, omitted, None)
            _verify_lineage(store, null, None)
            assert null["fingerprint"] == omitted["fingerprint"]
            operation = post({**body, "word_timing": timing})
            manifest, envelope = _verify_lineage(store, operation, timing)
            assert 'frames 2-3 / 0.042-0.083s: "hello"' in envelope["word_schedule_content"]
            assert manifest["prompt"]["word_schedule_sha256"] != legacy["prompt"]["word_schedule_sha256"]
            window = WindowMap.from_json(operation["window"])
            effective = _managed_words([WordInterval(9/24, 10/24, "hello")], window, Fraction(24))
            assert effective[0].start == pytest.approx(1/24, abs=TOLERANCE)
            assert effective[0].end == pytest.approx(2/24, abs=TOLERANCE)
            for start, end, count in ((7/24, 9/24, 1), (0, 8/24, 0), (16/24, 1, 0)):
                boundary = _timing(scene.source.asset_id, scene.source.sha256, start, end)
                result = post({**body, "word_timing": boundary})
                boundary_manifest, binding = _verify_lineage(store, result, boundary)
                assert boundary_manifest["word_timing"]["clipped_word_count"] == count
                if count:
                    assert 'frames 1-2 / 0.000-0.042s: "hello"' in binding["word_schedule_content"]
                    clipped = _managed_words([WordInterval(start, end, "hello")], window, Fraction(24))[0]
                    assert clipped.start == 0 and clipped.end == pytest.approx(1/24, abs=TOLERANCE)
                else:
                    assert binding["word_schedule_content"] == empty["word_schedule_content"]
                    assert result["fingerprint"] != omitted["fingerprint"]
            equivalent = json.loads(json.dumps({**timing, "words": [{"end": 1, "word": "whole", "start": -0.0}]}, indent=4))
            first = post({**body, "word_timing": equivalent})
            equivalent["words"][0].update(start=0, end=1.0)
            second = post({**body, "word_timing": equivalent})
            assert first["fingerprint"] == second["fingerprint"]
            _verify_lineage(store, first, equivalent)
            outside = deepcopy(timing)
            outside["words"].append({"start": .8, "end": .9, "word": "outside"})
            previous = post({**body, "word_timing": outside})
            for field, value in (("word", "changed"), ("end", .95)):
                outside["words"][-1][field] = value
                changed = post({**body, "word_timing": outside})
                current_manifest, _ = _verify_lineage(store, changed, outside)
                previous_manifest = json.loads(previous["canonical_json"])
                assert changed["fingerprint"] != previous["fingerprint"]
                assert current_manifest["word_timing"]["word_timing_sha256"] != previous_manifest["word_timing"]["word_timing_sha256"]
                assert current_manifest["prompt"]["word_schedule_sha256"] == manifest["prompt"]["word_schedule_sha256"]
                previous = changed
            _browser(server.base_url, evidence, project, timing)
            browser_result = json.loads((evidence / "browser.json").read_text())
            _verify_lineage(store, browser_result["resolvedOperation"], timing)
            assert _counts(store)["attempts"] == 0
            (evidence / "http-lineage.json").write_text(json.dumps({"operation": operation, "manifest": manifest,
                "binding": envelope, "negative_cases": len(invalids) + 2, "counts": _counts(store)}, indent=2))
    finally:
        server.stop()


def test_private_clipping_retains_positive_nextafter_and_legacy_nan() -> None:
    from openjutsu.m1_types import FrameRange, Timebase
    window = WindowMap(FrameRange(8, 16), Timebase(1, 24), FrameRange(0, 8), Timebase(1, 24),
                       0, 0, 8, FrameRange(0, 8), FrameRange(8, 16), Timebase(1, 24), "test")
    assert _managed_words([WordInterval(0, 8/24, "left"), WordInterval(16/24, 1, "right")], window, Fraction(24)) == ()
    words = [WordInterval(7/24, 9/24, "a"), WordInterval(10/24, 11/24, "B"),
             WordInterval(math.nextafter(16/24, -math.inf), 16/24, "tiny")]
    clipped = _managed_words(words, window, Fraction(24))
    assert [w.word for w in clipped] == ["a", "B", "tiny"]
    assert all(w.end > w.start for w in clipped)
    for original, result in zip(words, clipped):
        assert result.start == max(original.start, float(Fraction(8, 24))) - float(Fraction(8, 24))
        assert result.end == min(original.end, float(Fraction(16, 24))) - float(Fraction(8, 24))
    for word in (WordInterval(math.nan, .5, "nan"), WordInterval(.4, math.nan, "nan")):
        retained = _managed_words([word], window, Fraction(24))
        assert len(retained) == 1
        with pytest.raises(ValueError):
            format_word_schedule(list(retained), 24)


def _browser(base_url: str, evidence: Path, project: str, timing: dict) -> None:
    valid = evidence / "valid.json"
    valid.write_text(json.dumps(timing))
    script = evidence / "browser.py"
    script.write_text(dedent(r'''
        import json, sys
        from pathlib import Path
        from playwright.sync_api import sync_playwright
        url, root, project = sys.argv[1:]
        root = Path(root)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, channel="chrome")
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            posts, errors = [], []
            page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_function("() => Boolean(window.StudioUI)")
            page.locator("#advanced-studio > summary").click()
            page.wait_for_selector("#project-select", state="visible")
            page.select_option("#project-select", project)
            page.wait_for_selector("#character-select option:not([value=''])", state="attached")
            page.select_option("#character-select", index=1)
            page.wait_for_selector("#m1-shot-select option[value=second]", state="attached")
            page.select_option("#m1-shot-select", "second")
            page.check("#m1-rights")
            control = page.get_by_label("Optional original-source word timing JSON")
            for content in (b'{"extra":true}', b' ' * (512 * 1024 + 1)):
                control.set_input_files({"name": "invalid.json", "mimeType": "application/json", "buffer": content})
                page.wait_for_function("() => document.getElementById('m1-word-status').textContent.includes('refused')")
                page.click("#m1-resolve")
                page.wait_for_function("() => document.getElementById('m1-resolve-note').textContent.includes('Resolution refused')")
                assert not posts
            control.set_input_files(str(root / "valid.json"))
            page.wait_for_function("() => document.getElementById('m1-word-status').textContent.includes('Ready: 1')")
            with page.expect_response(lambda r: r.url.endswith('/operations/resolve')) as result:
                page.click("#m1-resolve")
            assert result.value.status == 201
            page.wait_for_function("() => window.M1UI.getState().resolvedOperation !== null")
            state = page.evaluate("() => window.M1UI.getState()")
            assert json.loads(state["resolvedOperation"]["canonical_json"])["word_timing"]["clipped_word_count"] == 1
            assert len(posts) == 1 and not errors
            page.locator("#m1-word-status").screenshot(path=str(root / "word-status.png"))
            page.get_by_role("button", name="Clear word timing", exact=True).click()
            assert page.evaluate("() => window.M1UI.getState().wordTiming") is None
            assert control.input_value() == ''
            control.set_input_files(str(root / "valid.json"))
            page.wait_for_function("() => window.M1UI.getState().wordTiming !== null")
            page.locator('#m1-source').set_input_files(str(root / "valid.json"))
            assert page.evaluate("() => window.M1UI.getState().wordTiming") is None
            assert control.input_value() == ''
            stale = json.loads((root / "valid.json").read_text())
            stale['source_asset_id'] = 'different-source'
            control.set_input_files({"name": "stale.json", "mimeType": "application/json",
                                     "buffer": json.dumps(stale).encode()})
            page.wait_for_function("() => document.getElementById('m1-word-status').textContent.includes('stale source')")
            assert len(posts) == 1
            page.select_option('#project-select', '')
            assert control.input_value() == ''
            assert page.evaluate("() => window.M1UI.getState().wordTiming") is None
            (root / "browser.json").write_text(json.dumps(state, indent=2))
            browser.close()
    '''))
    run = subprocess.run([BROWSER_PYTHON, str(script), base_url, str(evidence), project],
                         capture_output=True, text=True, timeout=100,
                         env={"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin", "HOME": str(evidence)})
    (evidence / "browser.log").write_text(run.stdout + run.stderr)
    assert run.returncode == 0, run.stdout + run.stderr
