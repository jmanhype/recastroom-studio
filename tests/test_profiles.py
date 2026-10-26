# SPDX-License-Identifier: MIT
from openjutsu.profiles import RecastProfile


def test_prompt_contains_rights_and_lipsync_contract() -> None:
    prompt = RecastProfile().render_prompt("WORD_SCHEDULE")
    assert "source audio" in prompt
    assert "WORD_SCHEDULE" in prompt
    assert "unlicensed celebrity" in prompt
    assert "deceased performer" in prompt
