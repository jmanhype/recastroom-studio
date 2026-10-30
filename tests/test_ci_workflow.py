# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github/workflows/ci.yml"


def test_ci_is_pinned_fast_and_reproducible():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "name: CI" in text
    assert "branches: [main]" in text
    assert "pull_request:" in text
    assert "workflow_dispatch:" in text
    assert "cancel-in-progress: true" in text
    assert "contents: read" in text
    assert "timeout-minutes: 20" in text
    assert "runs-on: macos-14" in text
    assert 'python-version: ["3.11", "3.12"]' in text
    assert "apt-get" not in text
    assert "brew tap-new recastroom/legacy" in text
    assert "brew install recastroom/legacy/ffmpeg" in text
    assert "homebrew-core/5e8c24087d2a54c386f50dfa7bccd4a2d406b09a/Formula/f/ffmpeg.rb" in text
    assert "homebrew-core/86c2371386a5f0b8a81d890ba1a233a6153ded7c/Formula/lib/libvpx.rb" in text
    assert "brew install --force --ignore-dependencies recastroom/legacy/libvpx" in text
    assert "ffmpeg -version | grep -F 'ffmpeg version 8.0.1'" in text
    assert "ffprobe -version | grep -F 'ffprobe version 8.0.1'" in text
    assert "python -m compileall -q app scripts src tests tools" in text
    assert "node --check app/web/landing.js" in text
    assert "node --check app/web/sound-lab.js" in text
    assert "node --check app/web/studio.js" in text
    assert "python -m pytest -q" in text

    uses = re.findall(r"uses: ([^ ]+) #", text)
    assert uses == [
        "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    ]
