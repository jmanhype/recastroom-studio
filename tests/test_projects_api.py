# SPDX-License-Identifier: MIT
"""Real store/API integration for saved projects in the existing studio flow."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from openjutsu.config import load_settings


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/fixtures/synthetic_source.mp4"
REFERENCE = ROOT / "tests/fixtures/synthetic_reference.png"
REFERENCE_BYTES = REFERENCE.read_bytes()


def reference_upload(filename: str = "primary.png") -> tuple[str, bytes, str]:
    return filename, REFERENCE_BYTES, "image/png"


def workspace_snapshot(root: Path) -> tuple[set[str], dict[str, str]]:
    paths = {str(path.relative_to(root)) for path in root.rglob("*")}
    files = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }
    return paths, files


def create_character(
    client: TestClient, project_id: str, *, second: bool = False
) -> dict:
    files = {"reference_1": reference_upload("primary.png")}
    if second:
        files["reference_2"] = reference_upload("secondary.png")
    response = client.post(
        "/api/characters",
        data={"project_id": project_id, "name": "Synthetic Performer", "description": "Fixture"},
        files=files,
    )
    assert response.status_code == 200, response.text
    return response.json()


def prepare_saved(client: TestClient, project_id: str, character: dict, seed: int = 77):
    return client.post(
        "/api/prepare",
        files={"source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4")},
        data={
            "rights_attested": "true",
            "seed": str(seed),
            "project_id": project_id,
            "character_id": character["character"]["character_id"],
            "character_version": str(character["character"]["version"]),
        },
    )


def test_saved_character_prepares_and_records_isolated_project_history(tmp_path):
    import app.main as main

    original_settings = main.SETTINGS
    original_store = main.PROJECT_STORE
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = load_settings(
        {"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path)}
    )
    try:
        with TestClient(main.app) as client:
            assert client.get("/api/health").status_code == 200
            assert client.get("/api/projects").status_code == 200
            assert main.PROJECT_STORE.root == tmp_path.resolve()

            project_a = client.post("/api/projects", json={"name": "Project A"}).json()
            project_b = client.post("/api/projects", json={"name": "Project B"}).json()
            assert client.get("/api/projects").json()["projects"] == [project_a, project_b]
            assert client.get(f"/api/projects/{project_a['project_id']}").json() == project_a

            character = create_character(client, project_a["project_id"], second=True)
            assert character["character"]["version"] == 1
            assert [item["filename"] for item in character["references"]] == [
                "primary.png", "secondary.png"
            ]
            preview = client.get(f"/api/assets/{character['references'][0]['asset_id']}")
            assert preview.status_code == 200
            assert preview.content == REFERENCE_BYTES
            assert preview.headers["content-type"] == "image/png"

            staged_before = {
                path.name for path in (tmp_path / "uploads").iterdir() if len(path.name) == 32
            }
            prepared_a = prepare_saved(client, project_a["project_id"], character)
            assert prepared_a.status_code == 200, prepared_a.text
            assert prepared_a.json()["project_id"] == project_a["project_id"]
            prepared_b = prepare_saved(client, project_b["project_id"], character, seed=78)
            assert prepared_b.status_code == 200, prepared_b.text
            staged_after = {
                path.name for path in (tmp_path / "uploads").iterdir() if len(path.name) == 32
            }
            assert staged_after == staged_before

            job_a = prepared_a.json()["job_id"]
            workflow = json.loads((tmp_path / "jobs" / job_a / "workflow.json").read_text())
            plan = json.loads(workflow["1189"]["inputs"]["plan"])
            assert plan["video"] == SOURCE.name
            assert (plan["global_ref"], plan["global_ref2"]) == ("primary.png", "secondary.png")
            assert plan["audio_mode"] == "auto"
            assert workflow["181"]["inputs"]["steps"] == 8
            assert workflow["13"]["inputs"]["noise_seed"] == 77
            assert workflow["1177"]["inputs"]["with_audio"] is True
            history_a = client.get(f"/api/projects/{project_a['project_id']}/jobs").json()["jobs"]
            history_b = client.get(f"/api/projects/{project_b['project_id']}/jobs").json()["jobs"]
            assert [item["job_id"] for item in history_a] == [job_a]
            assert [item["job_id"] for item in history_b] == [prepared_b.json()["job_id"]]
            assert history_a[0]["character_version"] == 1
            assert history_b[0]["character_id"] == character["character"]["character_id"]
            for record in (*history_a, *history_b):
                assert set(record["config"]) == {
                    "audio_mode", "reference_names", "scheduler_steps", "seed", "video_name", "with_audio"
                }
                assert record["workflow_url"] == f"/api/jobs/{record['job_id']}/workflow"
                assert record["prompt_url"] == f"/api/jobs/{record['job_id']}/prompt"
            assert str(tmp_path) not in prepared_a.text
            assert str(tmp_path) not in json.dumps(history_a + history_b)
    finally:
        main.SETTINGS = original_settings
        main.PROJECT_STORE = original_store
        main.app.state.workspace_store = original_store
        main.JOB_STATUS.clear(); main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear(); main.JOB_LOCKS.update(original_locks)


def test_saved_reference_validation_conflicts_and_integrity_are_actionable(tmp_path):
    import app.main as main

    original_settings = main.SETTINGS
    original_store = main.PROJECT_STORE
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = load_settings(
        {"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path)}
    )
    try:
        with TestClient(main.app) as client:
            client.get("/api/health")
            project = client.post("/api/projects", json={"name": "Errors"}).json()
            before_uploads = {path.name for path in (tmp_path / "uploads").iterdir()}
            unsafe = client.post(
                "/api/characters",
                data={"project_id": project["project_id"], "name": "Bad media"},
                files={"reference_1": ("preview.html", b"<html>not an image</html>", "text/html")},
            )
            assert unsafe.status_code == 422
            assert {path.name for path in (tmp_path / "uploads").iterdir()} == before_uploads

            character = create_character(client, project["project_id"])
            conflict = client.post(
                "/api/prepare",
                files={
                    "source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4"),
                    "reference_1": reference_upload(),
                },
                data={
                    "rights_attested": "true",
                    "project_id": project["project_id"],
                    "character_id": character["character"]["character_id"],
                    "character_version": "1",
                },
            )
            assert conflict.status_code == 422
            assert "not both" in conflict.json()["detail"]
            assert not (tmp_path / "jobs").exists()

            missing_project = client.post(
                "/api/prepare",
                files={"source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4")},
                data={
                    "rights_attested": "true",
                    "project_id": "0" * 32,
                    "character_id": character["character"]["character_id"],
                    "character_version": "1",
                },
            )
            assert missing_project.status_code == 404
            assert not (tmp_path / "jobs").exists()
            for malformed in ({"project_id": "bad"}, {"character_id": "bad", "character_version": "1"}):
                payload = {"rights_attested": "true", **malformed}
                invalid = client.post(
                    "/api/prepare",
                    files={"source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4")},
                    data=payload,
                )
                assert invalid.status_code == 422
                assert str(tmp_path) not in invalid.text
            assert not (tmp_path / "jobs").exists()

            asset_id = character["references"][0]["asset_id"]
            protected_path = main.PROJECT_STORE.resolve_asset(asset_id).path
            original_bytes = protected_path.read_bytes()
            protected_path.write_bytes(b"changed protected fixture")
            changed = prepare_saved(client, project["project_id"], character)
            assert changed.status_code == 409
            assert "protected asset bytes" in changed.json()["detail"]
            assert str(tmp_path) not in changed.text
            assert client.get(f"/api/assets/{asset_id}").status_code == 409
            assert client.get("/api/assets/not-an-id").status_code == 422
            protected_path.write_bytes(original_bytes)
    finally:
        main.SETTINGS = original_settings
        main.PROJECT_STORE = original_store
        main.app.state.workspace_store = original_store
        main.JOB_STATUS.clear(); main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear(); main.JOB_LOCKS.update(original_locks)


def test_upload_only_prepare_remains_compatible_and_unrecorded(tmp_path):
    import app.main as main

    original_settings = main.SETTINGS
    original_store = main.PROJECT_STORE
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = load_settings(
        {"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path)}
    )
    try:
        with TestClient(main.app) as client:
            client.get("/api/health")
            project = client.post("/api/projects", json={"name": "Unused"}).json()
            response = client.post(
                "/api/prepare",
                files={
                    "source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4"),
                    "reference_1": reference_upload(),
                },
                data={"rights_attested": "true", "seed": "79"},
            )
            assert response.status_code == 200, response.text
            job_id = response.json()["job_id"]
            assert "project_id" not in response.json()
            assert (tmp_path / "uploads" / job_id / SOURCE.name).read_bytes() == SOURCE.read_bytes()
            assert (tmp_path / "uploads" / job_id / "primary.png").read_bytes() == REFERENCE_BYTES
            assert client.get(f"/api/jobs/{job_id}/workflow").status_code == 200
            assert client.get(f"/api/projects/{project['project_id']}/jobs").json()["jobs"] == []
    finally:
        main.SETTINGS = original_settings
        main.PROJECT_STORE = original_store
        main.app.state.workspace_store = original_store
        main.JOB_STATUS.clear(); main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear(); main.JOB_LOCKS.update(original_locks)


def test_prepare_rejects_basename_collisions_before_any_writes(tmp_path):
    import app.main as main

    original_settings = main.SETTINGS
    original_store = main.PROJECT_STORE
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = load_settings(
        {"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path)}
    )
    try:
        with TestClient(main.app) as client:
            client.get("/api/health")
            project = client.post("/api/projects", json={"name": "Collisions"}).json()
            character = create_character(client, project["project_id"], second=True)
            project_url = f"/api/projects/{project['project_id']}"
            history_url = f"{project_url}/jobs"
            project_before = client.get(project_url).json()
            history_before = client.get(history_url).json()
            protected_paths = [
                main.PROJECT_STORE.resolve_asset(item["asset_id"]).path
                for item in character["references"]
            ]
            protected_before = {path: path.read_bytes() for path in protected_paths}
            source_bytes = SOURCE.read_bytes()
            first_reference = b"\x89PNG\r\n\x1a\nfirst synthetic reference"
            second_reference = b"\x89PNG\r\n\x1a\nsecond synthetic reference"
            before_paths, before_files = workspace_snapshot(tmp_path)
            before_status = main.JOB_STATUS.copy()
            before_locks = main.JOB_LOCKS.copy()

            duplicate = client.post(
                "/api/prepare",
                files={
                    "source": (SOURCE.name, source_bytes, "video/mp4"),
                    "reference_1": ("same.png", first_reference, "image/png"),
                    "reference_2": ("same.png", second_reference, "image/png"),
                    "words": ("", b"", "text/plain"),
                    "workflow": ("", b"", "application/json"),
                },
                data={"rights_attested": "true", "project_id": project["project_id"]},
            )
            assert duplicate.status_code == 422, duplicate.text
            assert duplicate.json()["detail"] == (
                "Upload filename collision for same.png: reference_1 and reference_2. "
                "Rename one of the uploads before preparing again."
            )
            assert "job_id" not in duplicate.json()
            assert str(tmp_path) not in duplicate.text
            assert workspace_snapshot(tmp_path) == (before_paths, before_files)
            assert {path: path.read_bytes() for path in protected_paths} == protected_before
            assert SOURCE.read_bytes() == source_bytes
            assert not (tmp_path / "jobs").exists()
            assert not [path for path in tmp_path.rglob("*") if path.name == "same.png"]
            assert all(
                path.read_bytes() != second_reference
                for path in tmp_path.rglob("*")
                if path.is_file()
            )

            cross_role = client.post(
                "/api/prepare",
                files={
                    "source": (SOURCE.name, source_bytes, "video/mp4"),
                    "reference_1": (SOURCE.name, first_reference, "image/png"),
                },
                data={"rights_attested": "true", "project_id": project["project_id"]},
            )
            assert cross_role.status_code == 422, cross_role.text
            assert cross_role.json()["detail"] == (
                f"Upload filename collision for {SOURCE.name}: source and reference_1. "
                "Rename one of the uploads before preparing again."
            )
            assert "job_id" not in cross_role.json()
            assert str(tmp_path) not in cross_role.text
            assert workspace_snapshot(tmp_path) == (before_paths, before_files)
            assert {path: path.read_bytes() for path in protected_paths} == protected_before
            assert SOURCE.read_bytes() == source_bytes
            assert not (tmp_path / "jobs").exists()
            assert client.get(project_url).json() == project_before
            assert client.get(history_url).json() == history_before
            assert main.JOB_STATUS == before_status
            assert main.JOB_LOCKS == before_locks
    finally:
        main.SETTINGS = original_settings
        main.PROJECT_STORE = original_store
        main.app.state.workspace_store = original_store
        main.JOB_STATUS.clear(); main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear(); main.JOB_LOCKS.update(original_locks)
