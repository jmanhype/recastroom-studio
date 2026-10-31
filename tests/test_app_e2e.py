# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from openjutsu.config import load_settings


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "tests/fixtures/synthetic_source.mp4"
REFERENCE = REPO / "tests/fixtures/synthetic_reference.png"
WORDS = REPO / "tests/fixtures/word_timings.json"


def files() -> dict[str, tuple[str, bytes, str]]:
    return {
        "source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4"),
        "reference_1": (REFERENCE.name, REFERENCE.read_bytes(), "image/png"),
        "words": (WORDS.name, WORDS.read_bytes(), "application/json"),
    }


def configure_app(main, tmp_path: Path, backend: str):
    main.SETTINGS = load_settings(
        {
            "OPENJUTSU_BACKEND": backend,
            "OPENJUTSU_DATA_DIR": str(tmp_path),
        }
    )
    main.JOB_STATUS.clear()
    main.JOB_LOCKS.clear()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_prepare_omits_absent_optional_uploads(tmp_path, monkeypatch):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    configure_app(main, tmp_path, "dry_run")
    try:
        with TestClient(main.app) as client:
            prepared = client.post(
                "/api/prepare",
                files={
                    "source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4"),
                    "reference_1": (REFERENCE.name, REFERENCE.read_bytes(), "image/png"),
                },
                data={
                    "identity": "Synthetic fixture performer",
                    "seed": "50",
                    "rights_attested": "true",
                },
            )
            assert prepared.status_code == 200
            manifest = prepared.json()["manifest"]
            assert manifest["reference_2"] is None
            assert manifest["word_schedule_path"] is None
            job_id = manifest["job_id"]
            assert not (tmp_path / "uploads" / job_id / "reference_2").exists()
            assert not (tmp_path / "uploads" / job_id / "word_timings.json").exists()
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)


def test_dry_run_backend_completes_upload_to_review_artifacts(tmp_path, monkeypatch):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    configure_app(main, tmp_path, "dry_run")
    try:
        with TestClient(main.app) as client:
            health = client.get("/api/health")
            assert health.status_code == 200
            assert health.json()["backend"] == "dry_run"

            missing = client.post(
                "/api/prepare",
                files=files(),
                data={"identity": "Synthetic fixture performer", "seed": "50"},
            )
            assert missing.status_code == 422
            assert missing.json()["detail"] == "Permission declaration is required."
            assert not (tmp_path / "jobs").exists()

            invalid = client.post(
                "/api/prepare",
                files=files(),
                data={
                    "identity": "Synthetic fixture performer",
                    "seed": "50",
                    "rights_attested": "invalid",
                },
            )
            assert invalid.status_code == 422
            assert not (tmp_path / "jobs").exists()

            prepared = client.post(
                "/api/prepare",
                files=files(),
                data={
                    "identity": "Synthetic fixture performer",
                    "seed": "50",
                    "rights_attested": "true",
                },
            )
            assert prepared.status_code == 200
            payload = prepared.json()
            assert payload["scene"]["recommended"] is True
            job_id = payload["job_id"]
            assert client.get(payload["workflow_url"]).status_code == 200
            prompt = client.get(payload["prompt_url"]).text
            assert '"rights"' in prompt
            assert '"clean"' in prompt

            queued = client.post(f"/api/jobs/{job_id}/run")
            assert queued.status_code == 200
            status = client.get(f"/api/jobs/{job_id}/status")
            assert status.status_code == 200
            assert status.json()["state"] == "complete"
            assert status.json()["backend"] == "dry_run"
            assert status.json()["presentation"] == "preview"
            assert "Preview complete" in status.json()["message"]
            assert "no AI inference" in status.json()["message"]
            assert status.json()["prompt_id"].startswith("dry-run-")

            job_dir = tmp_path / "jobs" / job_id
            assert (job_dir / "generated.mp4").read_bytes() == SOURCE.read_bytes()
            final_probe = probe(job_dir / "final.mp4")
            assert final_probe["streams"][0]["codec_type"] == "video"
            assert final_probe["streams"][1]["codec_type"] == "audio"
            review_probe = probe(job_dir / "source_vs_final.mp4")
            video_stream = next(s for s in review_probe["streams"] if s["codec_type"] == "video")
            assert video_stream["width"] == 1920

            for artifact in ("generated", "final", "side_by_side"):
                downloaded = client.get(f"/api/jobs/{job_id}/artifacts/{artifact}")
                assert downloaded.status_code == 200, (
                    artifact,
                    downloaded.text,
                    sorted(path.name for path in job_dir.iterdir()),
                )
                assert downloaded.headers["content-type"].startswith("video/mp4")
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)


def test_custom_recastroom_compatible_workflow_replaces_default_template(tmp_path, monkeypatch):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    configure_app(main, tmp_path, "dry_run")
    custom = json.loads((REPO / "workflows/recastroom_h3_workflow.json").read_text())
    custom["586"]["inputs"]["lora_name"] = "operator_test_character_swap_v1.1.safetensors"
    try:
        with TestClient(main.app) as client:
            prepared = client.post(
                "/api/prepare",
                files={
                    **files(),
                    "workflow": (
                        "custom-recast.json",
                        json.dumps(custom).encode(),
                        "application/json",
                    ),
                },
                data={
                    "identity": "Synthetic fixture performer",
                    "seed": "50",
                    "rights_attested": "true",
                },
            )
            assert prepared.status_code == 200, prepared.text
            job_id = prepared.json()["job_id"]
            saved = json.loads(
                (tmp_path / "jobs" / job_id / "workflow.json").read_text()
            )
            assert saved["586"]["inputs"]["lora_name"] == "operator_test_character_swap_v1.1.safetensors"
            assert saved["1177"]["inputs"]["source_blur"] == "head + hands (keep mouth)"
            assert saved["14"]["inputs"]["latent_image"] == ["201", 0]
            assert "/Users/" not in prepared.text
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)


def test_sdk_backend_without_credentials_fails_closed_in_status(tmp_path, monkeypatch):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    monkeypatch.delenv("COMFY_API_KEY", raising=False)
    monkeypatch.delenv("OPENJUTSU_COMFY_API_KEY", raising=False)
    monkeypatch.delenv("COMFY_BASE_URL", raising=False)
    configure_app(main, tmp_path, "sdk")
    try:
        with TestClient(main.app) as client:
            prepared = client.post(
                "/api/prepare",
                files=files(),
                data={
                    "identity": "Synthetic fixture performer",
                    "seed": "50",
                    "rights_attested": "true",
                },
            )
            job_id = prepared.json()["job_id"]
            assert client.post(f"/api/jobs/{job_id}/run").status_code == 200
            status = client.get(f"/api/jobs/{job_id}/status").json()
            assert status["state"] == "error"
            assert status["backend"] == "sdk"
            assert status["error"]["error"]["code"] == "missing_comfy_api_key"
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)


@pytest.mark.parametrize(
    ("backend", "backend_label", "message"),
    [
        ("dry_run", "dry_run", "Preview execution requires a recorded permission declaration"),
        ("legacy", "legacy", "ComfyUI execution requires a recorded permission declaration"),
        ("sdk", "sdk", "Hosted Comfy execution requires a recorded permission declaration"),
    ],
)
def test_tampered_attestation_blocks_every_backend(
    tmp_path, monkeypatch, backend, backend_label, message
):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    monkeypatch.delenv("COMFY_API_KEY", raising=False)
    monkeypatch.delenv("OPENJUTSU_COMFY_API_KEY", raising=False)
    monkeypatch.delenv("COMFY_BASE_URL", raising=False)
    configure_app(main, tmp_path, backend)
    if backend == "legacy":
        monkeypatch.setattr(
            main,
            "renderer_readiness",
            lambda *_args, **_kwargs: SimpleNamespace(ready=True),
        )
    try:
        with TestClient(main.app) as client:
            prepared = client.post(
                "/api/prepare",
                files=files(),
                data={
                    "identity": "Synthetic fixture performer",
                    "seed": "50",
                    "rights_attested": "true",
                },
            )
            assert prepared.status_code == 200, prepared.text
            job_id = prepared.json()["job_id"]
            manifest_path = tmp_path / "jobs" / job_id / "job.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["rights_attested"] = False
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            assert client.post(f"/api/jobs/{job_id}/run").status_code == 200
            status = client.get(f"/api/jobs/{job_id}/status").json()
            assert status["state"] == "error"
            assert status["backend"] == backend_label
            assert message in status["message"]
            assert not (tmp_path / "jobs" / job_id / "generated.mp4").exists()
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)
