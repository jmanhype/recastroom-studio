# SPDX-License-Identifier: MIT
"""Settings screen contract: view without secrets, plain-language test, save and use."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from openjutsu.config import load_settings


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("RECASTROOM_COMFY_URL", raising=False)
    monkeypatch.delenv("OPENJUTSU_COMFY_URL", raising=False)
    monkeypatch.delenv("RECASTROOM_BACKEND", raising=False)
    monkeypatch.delenv("OPENJUTSU_BACKEND", raising=False)
    monkeypatch.delenv("COMFY_API_KEY", raising=False)
    monkeypatch.delenv("RECASTROOM_COMFY_API_KEY", raising=False)
    monkeypatch.delenv("OPENJUTSU_COMFY_API_KEY", raising=False)
    import app.main as main

    main.SETTINGS = load_settings(
        {"RECASTROOM_DATA_DIR": str(tmp_path), "RECASTROOM_BACKEND": "legacy"}
    )
    main.JOB_STATUS.clear()
    return TestClient(main.app)


def test_view_reports_defaults_without_saved_file(client: TestClient) -> None:
    response = client.get("/api/settings")
    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "legacy"
    assert payload["comfy_url"] == "http://127.0.0.1:8188"
    assert payload["locked"] == []
    assert payload["saved"] is False
    assert payload["has_api_key"] is False
    assert payload["api_key_hint"] is None
    assert payload["fields"]["backend"]["source"] == "default"


def test_save_and_use_hot_applies_and_persists(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/api/settings", json={"backend": "dry_run", "comfy_url": "http://127.0.0.1:9999"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "dry_run"
    assert payload["comfy_url"] == "http://127.0.0.1:9999"
    assert payload["saved"] is True

    saved_file = tmp_path / "connection.json"
    assert saved_file.is_file()
    saved = json.loads(saved_file.read_text(encoding="utf-8"))
    assert saved == {"backend": "dry_run", "comfy_url": "http://127.0.0.1:9999"}
    assert (saved_file.stat().st_mode & 0o777) == 0o600

    health = client.get("/api/health").json()
    assert health["backend"] == "dry_run"

    view = client.get("/api/settings").json()
    assert view["fields"]["backend"]["source"] == "saved"
    assert view["fields"]["comfy_url"]["source"] == "saved"


def test_save_refuses_unreachable_legacy_renderer(client: TestClient) -> None:
    response = client.post("/api/settings", json={"backend": "legacy", "comfy_url": "http://127.0.0.1:9"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["ok"] is False
    assert detail["message"]


def test_test_endpoint_answers_plain_language_without_http_error(client: TestClient) -> None:
    response = client.post("/api/settings/test", json={"backend": "legacy", "comfy_url": "http://127.0.0.1:9"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["code"] == "renderer_unreachable"
    assert payload["message"]


def test_test_endpoint_dry_run_is_ok(client: TestClient) -> None:
    payload = client.post("/api/settings/test", json={"backend": "dry_run"}).json()
    assert payload["ok"] is True
    assert payload["code"] == "local_dry_run"


def test_sdk_needs_a_key_then_reports_configured(client: TestClient) -> None:
    missing = client.post("/api/settings/test", json={"backend": "sdk"}).json()
    assert missing["ok"] is False
    assert missing["code"] == "sdk_missing_api_key"

    configured = client.post("/api/settings/test", json={"backend": "sdk", "comfy_api_key": "comfyui-test-key-1234"}).json()
    assert configured["ok"] is True
    assert configured["code"] == "sdk_configured"

    saved = client.post("/api/settings", json={"backend": "sdk", "comfy_api_key": "comfyui-test-key-1234"})
    assert saved.status_code == 200
    assert saved.json()["backend"] == "sdk"


def test_api_key_never_returns_to_the_browser(client: TestClient) -> None:
    saved = client.post("/api/settings", json={"backend": "sdk", "comfy_api_key": "comfyui-secret-abcd"})
    assert saved.status_code == 200
    view = client.get("/api/settings")
    assert "comfyui-secret-abcd" not in view.text
    payload = view.json()
    assert payload["has_api_key"] is True
    assert payload["api_key_hint"] == "…abcd"

    # A blank key on test keeps the saved one instead of clearing it.
    verdict = client.post("/api/settings/test", json={"backend": "sdk", "comfy_api_key": ""}).json()
    assert verdict["ok"] is True


def test_empty_field_on_save_reverts_to_launch_default(client: TestClient) -> None:
    assert client.post("/api/settings", json={"backend": "dry_run", "comfy_url": "http://127.0.0.1:9999"}).status_code == 200
    reverted = client.post("/api/settings", json={"backend": "dry_run", "comfy_url": ""})
    assert reverted.status_code == 200
    view = client.get("/api/settings").json()
    assert view["comfy_url"] == "http://127.0.0.1:8188"
    assert view["fields"]["comfy_url"]["source"] == "default"


def test_environment_locks_win_over_saved_values(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert client.post("/api/settings", json={"backend": "dry_run"}).status_code == 200
    monkeypatch.setenv("RECASTROOM_COMFY_URL", "http://10.9.8.7:8188")
    import app.main as main

    monkeypatch.setattr(main, "SETTINGS", load_settings({
        "RECASTROOM_DATA_DIR": str(tmp_path),
        "RECASTROOM_BACKEND": "legacy",
        "RECASTROOM_COMFY_URL": "http://10.9.8.7:8188",
    }))

    # A save that tries to change the locked address cannot persist it.
    assert client.post("/api/settings", json={"comfy_url": "http://127.0.0.1:9999"}).status_code == 200
    saved_file = json.loads((tmp_path / "connection.json").read_text(encoding="utf-8"))
    assert "comfy_url" not in saved_file

    view = client.get("/api/settings").json()
    assert "comfy_url" in view["locked"]
    assert view["comfy_url"] == "http://10.9.8.7:8188"
    assert view["fields"]["comfy_url"]["source"] == "environment"
    # The saved backend (not locked) still applies.
    assert view["backend"] == "dry_run"

    health = client.get("/api/health").json()
    assert health["backend"] == "dry_run"


def test_save_is_refused_while_a_job_is_running(client: TestClient) -> None:
    import app.main as main

    main.JOB_STATUS["job-1"] = {"job_id": "job-1", "state": "generating"}
    response = client.post("/api/settings", json={"backend": "dry_run"})
    assert response.status_code == 409
    assert "running" in response.json()["detail"].lower()


def test_invalid_drafts_are_rejected(client: TestClient) -> None:
    assert client.post("/api/settings/test", json={"backend": "bogus"}).status_code == 422
    assert client.post("/api/settings/test", json={"comfy_url": "ftp://example.invalid"}).status_code == 422
    assert client.post("/api/settings", json={"surprise": 1}).status_code == 422
    assert client.post("/api/settings", json={"comfy_url": "http://127.0.0.1:9999/"}).status_code == 400


def test_unreadable_connection_file_degrades_to_launch_settings(client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "connection.json").write_text("{not json", encoding="utf-8")
    view = client.get("/api/settings")
    assert view.status_code == 503

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["backend"] == "legacy"
