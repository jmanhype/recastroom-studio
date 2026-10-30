# SPDX-License-Identifier: MIT
"""Actual-HTTP E2E proof for project, character, prepare, run, and restart."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import os

import pytest

from tools.foundation_runtime import (
    FFMPEG,
    FFPROBE,
    PYTHON,
    TRUSTED_TOOL_DIRECTORIES,
    TOOL_ENVIRONMENT,
    TRUSTED_TOOL_PATH,
    child_environment,
    generate_media,
    media_probe,
    run_tool,
)
from tools.foundation_trial import run_trial


def test_foundation_server_uses_current_validated_venv(tmp_path: Path) -> None:
    child = subprocess.run(
        [
            str(PYTHON),
            "-c",
            "import json, sys; print(json.dumps({"
            '"executable": sys.executable, "prefix": sys.prefix, '
            '"base_prefix": sys.base_prefix}))',
        ],
        capture_output=True,
        check=True,
        env=child_environment(tmp_path),
        text=True,
        timeout=10,
    )
    identity = json.loads(child.stdout)

    assert PYTHON == Path(sys.executable)
    assert identity == {
        "executable": sys.executable,
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
    }


def test_media_tools_resolve_and_preflight_from_trusted_path() -> None:
    assert TOOL_ENVIRONMENT == {"PATH": TRUSTED_TOOL_PATH}
    assert TRUSTED_TOOL_PATH == "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

    for name, executable in (("ffmpeg", FFMPEG), ("ffprobe", FFPROBE)):
        expected = next(
            candidate
            for directory in TRUSTED_TOOL_DIRECTORIES
            if (candidate := directory / name).is_file()
            and os.access(candidate, os.X_OK)
        )
        assert executable == expected
        version = subprocess.run(
            [str(executable), "-version"],
            capture_output=True,
            check=True,
            env=TOOL_ENVIRONMENT,
            text=True,
            timeout=10,
        )
        assert f"{name} version" in version.stdout

    with pytest.raises(ValueError, match="Unsupported media tool 'provider-ffmpeg'"):
        run_tool(["provider-ffmpeg", "-version"])
    with pytest.raises(ValueError, match="No media tool specified"):
        run_tool([])


def test_real_media_generation_returns_real_probe_facts(tmp_path: Path) -> None:
    media = generate_media(tmp_path)

    assert set(media) == {"source", "primary", "secondary"}
    assert all(path.is_file() and path.stat().st_size > 0 for path in media.values())
    source_probe = media_probe(media["source"])
    primary_probe = media_probe(media["primary"])
    assert "mp4" in source_probe["format"]
    assert source_probe["duration_seconds"] > 0
    assert {(stream["codec_type"], stream["codec_name"]) for stream in source_probe["streams"]} == {
        ("video", "h264"),
        ("audio", "aac"),
    }
    assert primary_probe["streams"] == [{"codec_type": "video", "codec_name": "png", "width": 160, "height": 160}]


def test_saved_project_journey_survives_actual_server_restart(tmp_path: Path) -> None:
    result = run_trial(temp_root=tmp_path / "trial", evidence_root=tmp_path / "evidence")

    assert result["backend"] == "dry_run"
    assert result["binding"] == {"host": "127.0.0.1", "loopback_only": True}
    assert result["character"]["version"] == 1
    assert set(result["prepared_config"]) == {
        "audio_mode", "reference_names", "scheduler_steps", "seed", "video_name", "with_audio"
    }
    assert result["terminal_status"]["state"] == "complete"
    assert result["terminal_status"]["backend"] == "dry_run"
    assert result["restart"]["project_preserved"] is True
    assert result["restart"]["character_version_preserved"] is True
    assert result["restart"]["prepared_config_preserved"] is True
    assert result["restart"]["history_preserved"] is True
    assert result["restart"]["no_new_run_submitted_by_read_load"] is True
    assert result["restart"]["pre_switch_file_hashes_unchanged"] is True
    assert result["rejected_prepares"]["missing_saved_reference"] is True
    assert result["rejected_prepares"]["saved_and_uploaded_conflict"] is True
    assert result["rejected_prepares"]["missing_project"] is True
    assert result["rejected_prepares"]["duplicate_basename_actionable"] is True
    assert result["rejected_prepares"]["workspace_unchanged"] is True
    assert result["rejected_prepares"]["created_job_directories"] == 0
    assert result["legacy_upload_only"]["unrecorded_from_project"] is True
    assert result["legacy_upload_only"]["explicit_run"] is True

    receipt_path = tmp_path / "evidence" / "http-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt == result
    assert "/Users/" not in receipt_path.read_text(encoding="utf-8")
    assert not (tmp_path / "trial").exists()
