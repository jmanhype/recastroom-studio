# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class WordInterval:
    start: float
    end: float
    word: str


def load_whisper_words(path: str | Path) -> list[WordInterval]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    words: list[WordInterval] = []
    for segment in payload.get("segments", []):
        for item in segment.get("words", []):
            words.append(
                WordInterval(
                    start=float(item["start"]),
                    end=float(item["end"]),
                    word=str(item.get("word", "")).strip(),
                )
            )
    return words


def _frame(timestamp: float, fps: float) -> int:
    # ComfyUI/BFS uses one-based source frames.
    return max(1, int(round(timestamp * fps)) + 1)


def format_word_schedule(words: list[WordInterval], fps: float = 24.0) -> str:
    if fps <= 0:
        raise ValueError("fps must be positive")
    if not words:
        return "No speech detected. Keep the mouth relaxed and closed unless the source guide visibly articulates."
    lines: list[str] = []
    previous_end = 0.0
    for item in words:
        if item.start - previous_end >= 0.18:
            lines.append(
                f"- frames {_frame(previous_end, fps)}-{_frame(item.start, fps)-1} / "
                f"{previous_end:.3f}-{item.start:.3f}s: silent pause; lips stay relaxed and closed."
            )
        lines.append(
            f"- frames {_frame(item.start, fps)}-{_frame(item.end, fps)} / "
            f"{item.start:.3f}-{item.end:.3f}s: \"{item.word}\" — active source-matched articulation."
        )
        previous_end = max(previous_end, item.end)
    return "\n".join(lines)
