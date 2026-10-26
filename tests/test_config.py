# SPDX-License-Identifier: MIT
from pathlib import Path

import pytest

from openjutsu.config import load_settings


def test_default_workflow_prefers_repository_root(monkeypatch, tmp_path):
    workflow = tmp_path / "workflows" / "openjutsu_h3_lipsync_local.json"
    workflow.parent.mkdir()
    workflow.write_text("{}\n")
    monkeypatch.chdir(tmp_path)

    settings = load_settings({})

    assert settings.workflow == workflow
    assert settings.data_dir == tmp_path / "work"


def test_relative_environment_paths_resolve_from_current_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    settings = load_settings(
        {
            "RECASTROOM_WORKFLOW": "custom/workflow.json",
            "RECASTROOM_DATA_DIR": "custom/data",
        }
    )

    assert settings.workflow == tmp_path / "custom" / "workflow.json"
    assert settings.data_dir == tmp_path / "custom" / "data"


def test_legacy_environment_names_remain_compatible_and_public_names_win():
    settings = load_settings(
        {
            "OPENJUTSU_WORKFLOW": "legacy/workflow.json",
            "RECASTROOM_WORKFLOW": "public/workflow.json",
            "OPENJUTSU_BACKEND": "dry_run",
            "RECASTROOM_COMFY_API_KEY": "provided-by-owner",
        }
    )

    assert settings.workflow == Path("public/workflow.json").resolve()
    assert settings.backend == "dry_run"
    assert settings.comfy_api_key == "provided-by-owner"


def test_official_sdk_environment_is_surfaced_in_settings():
    settings = load_settings(
        {
            "COMFY_API_KEY": "provided-by-owner",
            "COMFY_BASE_URL": "https://deployment.example",
        }
    )

    assert settings.comfy_api_key == "provided-by-owner"
    assert settings.comfy_base_url == "https://deployment.example"


def test_unknown_backend_fails_closed():
    with pytest.raises(ValueError, match="RECASTROOM_BACKEND"):
        load_settings({"RECASTROOM_BACKEND": "typo"})
