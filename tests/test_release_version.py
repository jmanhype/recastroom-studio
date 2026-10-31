# SPDX-License-Identifier: MIT
"""Keep public version-bearing surfaces synchronized for release review."""
from __future__ import annotations

import re
from pathlib import Path

from openjutsu import __version__


REPO = Path(__file__).resolve().parents[1]


def test_release_version_is_synchronized_across_public_surfaces() -> None:
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.MULTILINE)
    assert match is not None
    version = match.group(1)

    import app.main as main

    assert __version__ == version
    assert main.app.version == version
    assert f"The expected application version is `{version}`." in (
        REPO / "docs/QUICKSTART.md"
    ).read_text(encoding="utf-8")
    assert f"`{version}`" in (REPO / "docs/RELEASE.md").read_text(encoding="utf-8")
    assert f"`{version}`" in (REPO / "docs/RELEASE_STATUS.md").read_text(encoding="utf-8")
    assert f"## {version} — " in (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
