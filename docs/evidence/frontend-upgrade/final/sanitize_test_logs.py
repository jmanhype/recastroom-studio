#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path
import re


def main() -> int:
    story = Path(__file__).resolve().parents[4]
    repo = story.parents[2]
    roots = {
        str(story): "<story-worktree>",
        str(repo): "<repo>",
    }
    for path in sorted(Path(__file__).parent.joinpath("test-runs").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        for original, replacement in roots.items():
            text = text.replace(original, replacement)
        text = re.sub(
            r"/private/[^ ]+/pytest-of-[^/ ]+",
            "<pytest-temp>",
            text,
        )
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
