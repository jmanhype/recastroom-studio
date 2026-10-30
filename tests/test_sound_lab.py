# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from openjutsu.config import load_settings


REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def studio(tmp_path: Path):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = load_settings(
        {"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path)}
    )
    main.JOB_STATUS.clear()
    main.JOB_LOCKS.clear()
    try:
        with TestClient(main.app) as client:
            yield main, client
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)


def test_sound_lab_is_local_accessible_and_truthful(studio):
    _, client = studio

    page = client.get("/sound-lab.html")
    script = client.get("/sound-lab.js")
    stylesheet = client.get("/sound-lab.css")
    tone = client.get("/vendor/tone-15.1.22.js")

    assert page.status_code == 200
    assert script.status_code == 200
    assert stylesheet.status_code == 200
    assert tone.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert tone.headers["content-type"].startswith(("application/javascript", "text/javascript"))
    assert tone.content == (REPO / "app/web/vendor/tone-15.1.22.js").read_bytes()

    html = page.text
    for control in ("play-sketch", "stop-sound", "master-volume"):
        assert f'id="{control}"' in html
    for cue in ("pulse", "tick", "reveal", "bed"):
        assert f'data-audition="{cue}"' in html
    assert 'id="reference-video"' in html
    assert 'src="/media/recastroom-public-hero-16x9.mp4"' in html
    assert "not a voice generator" in html
    assert "96 BPM · 12.8S SKETCH" in html
    assert "TONE.JS 15.1.22 · LOCAL MIT ASSET" in html
    assert 'src="/vendor/tone-15.1.22.js"' not in html
    assert "audio engine loads after you press play" in html
    assert not re.search(r"https?://", html)

    js = script.text
    assert "script.src = '/vendor/tone-15.1.22.js'" in js
    assert "await Tone.start();" in js
    assert "Tone.getTransport()" in js
    assert "new Tone.Limiter(-1)" in js
    assert "window.RecastSoundLab = Object.freeze({" in js
    assert "Math.random" not in js
    assert "fetch(" not in js
    assert "XMLHttpRequest" not in js
    assert "localStorage" not in js

    css = stylesheet.text
    assert "@media(min-width:768px)" in css
    assert "@media(min-width:1024px)" in css
    assert "@media(prefers-reduced-motion:reduce)" in css


def test_tone_asset_is_pinned_and_licensed():
    bundle = REPO / "app/web/vendor/tone-15.1.22.js"
    license = REPO / "app/web/vendor/TONE-15.1.22-LICENSE.txt"
    assert bundle.is_file()
    assert license.is_file()
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == (
        "e290952fa43d9a7a780182a83c6fccf44d79cb7ae2cba102ef1f2b9d98124e22"
    )
    assert "MIT License" in license.read_text(encoding="utf-8")


def test_public_hero_video_is_served_from_the_package(studio):
    _, client = studio

    response = client.get("/media/recastroom-public-hero-16x9.mp4")
    keeper = REPO / "media/recastroom-public-hero-16x9.mp4"
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert response.content == keeper.read_bytes()
    assert hashlib.sha256(response.content).hexdigest() == (
        "2cabf3066c5bfe9fcdfc5ee760ea94519b87b8a1f96f268f4fe464e48bd08b88"
    )
