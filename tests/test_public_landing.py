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


def test_public_landing_page_has_conversion_structure_and_local_assets(studio):
    _, client = studio

    page = client.get("/landing.html")
    stylesheet = client.get("/landing.css")
    script = client.get("/landing.js")
    legal = client.get("/legal.html")
    font = client.get("/fonts/manrope-latin-400-800.woff2")
    social = client.get("/images/recastroom-landing-social.jpg")
    video = client.get("/media/recastroom-public-hero-16x9.mp4")
    core_gallery = client.get("/media/gallery-core-recast.mp4")
    style_gallery = client.get("/media/gallery-style-lane.mp4")
    two_person_gallery = client.get("/media/gallery-two-person.mp4")

    for response in (
        page, stylesheet, script, legal, font, social, video,
        core_gallery, style_gallery, two_person_gallery,
    ):
        assert response.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert font.headers["content-type"].startswith("font/")
    assert social.headers["content-type"].startswith("image/jpeg")
    assert video.headers["content-type"].startswith("video/mp4")
    for gallery_video in (core_gallery, style_gallery, two_person_gallery):
        assert gallery_video.headers["content-type"].startswith("video/mp4")

    html = page.text
    assert "Keep the performance." in html
    assert "Change the lead." in html
    assert 'class="primary" href="/">Start a dry run</a>' in html
    assert 'href="/">Start an attested dry run</a>' in html
    assert "23.8 second proof" in html
    assert "No attestation, no render" in html
    assert "Deterministic dry run · no GPU · no API key · no inference" in html
    assert 'src="/media/recastroom-public-hero-16x9.mp4"' in html
    assert 'poster="/images/recastroom-landing-social.jpg"' in html
    assert 'id="hero-heading"' in html
    assert 'id="workflow"' in html
    assert 'id="runtime"' in html
    assert 'id="setup"' in html
    assert 'id="features"' in html
    assert 'id="proof"' in html
    assert 'id="gallery"' in html
    assert 'id="roadmap"' in html
    assert 'id="compare"' in html
    assert 'id="faq"' in html
    assert 'class="skip"' in html
    assert "<main id=\"main\">" in html
    assert html.count("<details") == 8
    assert not re.search(r"https?://", html)
    assert "/media/gallery-core-recast.mp4" in html
    assert "/media/gallery-style-lane.mp4" in html
    assert "/media/gallery-two-person.mp4" in html
    assert "Multi-person selection is a roadmap engine" in html
    assert "Broad, but not generic" in html
    assert "Know the execution boundary before you spend" in html
    assert "The first run tells you what is missing" in html
    assert "What RecastRoom optimizes for" in html
    assert "Original decoded audio restored" in html

    for story in ("source", "reference", "rights", "render", "audio", "review"):
        assert f'data-story="{story}"' in html
    assert "Privacy, terms, and rights" in legal.text

    js = script.text
    assert "IntersectionObserver" in js
    assert "requestAnimationFrame" in js
    assert "cancelAnimationFrame(frameRequest)" in js
    assert "prefers-reduced-motion" in js
    assert "Math.random" not in js
    assert "addEventListener('scroll'" not in js

    css = stylesheet.text
    assert "font-family: Manrope" in css
    assert "Helvetica" not in css
    assert "Inter," not in css
    assert "@media (min-width: 48rem)" in css
    assert "@media (min-width: 64rem)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert css.count("linear-gradient") == 1
    assert ".compare-scroll" in css
    assert "overflow-x: auto" in css
    assert "min-width: 48rem" in css


def test_public_landing_assets_are_pinned(studio):
    _, client = studio

    font = client.get("/fonts/manrope-latin-400-800.woff2")
    social = client.get("/images/recastroom-landing-social.jpg")
    video = client.get("/media/recastroom-public-hero-16x9.mp4")
    core_gallery = client.get("/media/gallery-core-recast.mp4")
    style_gallery = client.get("/media/gallery-style-lane.mp4")
    two_person_gallery = client.get("/media/gallery-two-person.mp4")
    assert hashlib.sha256(font.content).hexdigest() == (
        "e310b55a7fd9677f5e3555e6c6c4d064fa1f1d24393f0ddbe217cea12a8c432f"
    )
    assert hashlib.sha256(social.content).hexdigest() == (
        "d367605841757b50cf295c6581a2a8dee12b0c778841185156520bcbe783e0bd"
    )
    assert hashlib.sha256(video.content).hexdigest() == (
        "2cabf3066c5bfe9fcdfc5ee760ea94519b87b8a1f96f268f4fe464e48bd08b88"
    )
    assert hashlib.sha256(core_gallery.content).hexdigest() == (
        "f031c51eb79dba93bd53f892b22fc27e35aa78e671b15ffbf73c23aa2f9e267d"
    )
    assert hashlib.sha256(style_gallery.content).hexdigest() == (
        "36d8f25cf3ea66be52455623da48c5249e44b974666bba24aac67fd07dd79262"
    )
    assert hashlib.sha256(two_person_gallery.content).hexdigest() == (
        "7430625cf2571be959e876bb8ac02f278f403b381ccc9b388b612543fd21ed25"
    )
