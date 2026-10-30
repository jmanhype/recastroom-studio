# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    "README.md",
    "docs/QUICKSTART.md",
    "docs/RELEASE_STATUS.md",
    "app/web/index.html",
    "app/web/studio.js",
    "app/web/landing.html",
    "app/web/legal.html",
    "app/web/sound-lab.html",
    "app/web/sound-lab.js",
    "app/web/m1.js",
    "media/README.md",
    "RIGHTS.md",
    "examples/PERMISSION_DECLARATION.md",
)


def test_public_claims_do_not_reintroduce_unsupported_jargon():
    forbidden = (
        "Dry run", "DRY RUN", "Dry-run", "RunPod", "Overall QC",
        "Approved example", ">Keeper<", "Keeper video", "frozen keeper",
        "metadata-clean", "Drama 3",
        "rights-clean", "frame sheets, probes", "hashes stay beside",
        "C1-compatible", "Exact audio lock", "M1 panel", "Operator attestation",
        "OWNER_BLOCKED", "Retained replay", "Strict receipt", "CAS token",
        "Frozen", "CPU dry",
    )
    for name in PUBLIC_FILES:
        text = (ROOT / name).read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, (name, phrase)


def test_default_launcher_and_hosted_instructions_match_runtime_boundary():
    launcher = (ROOT / "run.sh").read_text(encoding="utf-8")
    quickstart = (ROOT / "docs/QUICKSTART.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    landing = (ROOT / "app/web/landing.html").read_text(encoding="utf-8")

    assert 'RECASTROOM_BACKEND:-dry_run' in launcher
    assert "Start the app in preview mode" in quickstart
    assert "Preview output is not an H3 recast" in readme
    assert "compatible hosted deployment" in landing
    assert "RecastRoom bridge" in quickstart
    assert "COMFY_SDK_ASSET_BRIDGE=openjutsu-v1" in quickstart
    assert not re.search(r"https?://", landing)
