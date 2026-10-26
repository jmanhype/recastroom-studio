#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from openjutsu.cli import main


if __name__ == "__main__":
    sys.exit(main())
