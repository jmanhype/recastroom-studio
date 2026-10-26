# SPDX-License-Identifier: MIT
from openjutsu.timing import WordInterval, format_word_schedule


def test_format_word_schedule_adds_silent_pause() -> None:
    words = [
        WordInterval(0.0, 0.5, "Hello"),
        WordInterval(1.0, 1.5, "world"),
    ]
    schedule = format_word_schedule(words, fps=24)
    assert 'frames 1-13 / 0.000-0.500s: "Hello"' in schedule
    assert "frames 13-24 / 0.500-1.000s: silent pause" in schedule
    assert 'frames 25-37 / 1.000-1.500s: "world"' in schedule


def test_empty_schedule_is_safe() -> None:
    assert "No speech detected" in format_word_schedule([])
