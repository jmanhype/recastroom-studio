#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Replayable real-HTTP evidence for the saved-project Studio foundation."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any

import requests

from tools.foundation_runtime import (
    HOST,
    LOOPBACK_ONLY,
    FoundationServer,
    REPO,
    assert_public as _assert_public,
    call as _call,
    free_loopback_port as _free_loopback_port,
    generate_media as _generate_media,
    hash_tree as _hash_tree,
    media_probe as _media_probe,
    require_status as _require_status,
    sha256_bytes,
    sha256_file,
    wait_complete as _wait_complete,
    workspace_counts as _workspace_counts,
)
from tools.foundation_runtime import sha256_file as _sha256_file



def _prepare_saved(
    client: requests.Session,
    base_url: str,
    media: dict[str, Path],
    project_id: str,
    character: dict[str, Any],
    records: list[dict[str, Any]],
) -> tuple[requests.Response, object]:
    source = media["source"]
    return _call(
        client,
        base_url,
        "POST",
        "/api/prepare",
        records,
        files={"source": (source.name, source.read_bytes(), "video/mp4")},
        data={
            "rights_attested": "true",
            "seed": "117",
            "identity": "Synthetic journey performer",
            "project_id": project_id,
            "character_id": character["character"]["character_id"],
            "character_version": str(character["character"]["version"]),
        },
    )


def run_trial(*, temp_root: Path, evidence_root: Path) -> dict[str, Any]:
    """Exercise the saved-project foundation over real HTTP and two uvicorn runs."""
    temp_root = temp_root.resolve()
    evidence_root = evidence_root.resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    workspace = temp_root / "workspace"
    workspace.mkdir()
    media = _generate_media(temp_root)
    records: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {
        "schema_version": "openjutsu.studio-foundation-http-trial.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "binding": {"host": HOST, "loopback_only": LOOPBACK_ONLY},
        "backend": "dry_run",
        "browser_automation": "not used by this HTTP replay",
        "media": {
            name: {
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
                "probe": _media_probe(path),
            }
            for name, path in media.items()
        },
    }

    server_one = FoundationServer(_free_loopback_port(), workspace, evidence_root / "server-cycle-1.log")
    try:
        server_one.start()
        with requests.Session() as client:
            health_response, health = _call(client, server_one.base_url, "GET", "/api/health", records)
            _require_status(health_response, 200, "health")
            assert isinstance(health, dict) and health["backend"] == "dry_run"

            home_response, _home = _call(client, server_one.base_url, "GET", "/", records)
            _require_status(home_response, 200, "home")

            project_response, project_body = _call(
                client, server_one.base_url, "POST", "/api/projects", records, json={"name": "Foundation Journey"}
            )
            _require_status(project_response, 200, "create project")
            assert isinstance(project_body, dict)
            project_id = str(project_body["project_id"])

            character_response, character_body = _call(
                client,
                server_one.base_url,
                "POST",
                "/api/characters",
                records,
                data={
                    "project_id": project_id,
                    "name": "Synthetic Performer",
                    "description": "Generated journey reference",
                },
                files={
                    "reference_1": (media["primary"].name, media["primary"].read_bytes(), "image/png"),
                    "reference_2": (media["secondary"].name, media["secondary"].read_bytes(), "image/png"),
                },
            )
            _require_status(character_response, 200, "create character")
            assert isinstance(character_body, dict)
            character = character_body

            preview_response, _preview = _call(
                client,
                server_one.base_url,
                "GET",
                f"/api/assets/{character['references'][0]['asset_id']}",
                records,
            )
            _require_status(preview_response, 200, "asset preview")
            assert preview_response.content == media["primary"].read_bytes()

            before_failed_prepares = _hash_tree(workspace)
            before_failed_counts = _workspace_counts(workspace)
            source_only = _call(
                client,
                server_one.base_url,
                "POST",
                "/api/prepare",
                records,
                files={"source": (media["source"].name, media["source"].read_bytes(), "video/mp4")},
                data={"rights_attested": "true", "project_id": project_id},
            )
            _require_status(source_only[0], 422, "missing reference")
            conflict = _call(
                client,
                server_one.base_url,
                "POST",
                "/api/prepare",
                records,
                files={
                    "source": (media["source"].name, media["source"].read_bytes(), "video/mp4"),
                    "reference_1": (media["primary"].name, media["primary"].read_bytes(), "image/png"),
                },
                data={
                    "rights_attested": "true",
                    "project_id": project_id,
                    "character_id": character["character"]["character_id"],
                    "character_version": "1",
                },
            )
            _require_status(conflict[0], 422, "saved/upload conflict")
            missing_project = _call(
                client,
                server_one.base_url,
                "POST",
                "/api/prepare",
                records,
                files={"source": (media["source"].name, media["source"].read_bytes(), "video/mp4")},
                data={
                    "rights_attested": "true",
                    "project_id": "0" * 32,
                    "character_id": character["character"]["character_id"],
                    "character_version": "1",
                },
            )
            _require_status(missing_project[0], 404, "missing project")
            duplicate_basename = _call(
                client,
                server_one.base_url,
                "POST",
                "/api/prepare",
                records,
                files={
                    "source": (
                        media["primary"].name,
                        media["source"].read_bytes(),
                        "video/mp4",
                    ),
                    "reference_1": (
                        media["primary"].name,
                        media["primary"].read_bytes(),
                        "image/png",
                    ),
                },
                data={"rights_attested": "true"},
            )
            _require_status(duplicate_basename[0], 422, "duplicate basename")
            assert isinstance(duplicate_basename[1], dict)
            assert duplicate_basename[1]["detail"] == (
                "Upload filename collision for foundation-primary.png: source and reference_1. "
                "Rename one of the uploads before preparing again."
            )
            after_failed_prepares = _hash_tree(workspace)
            after_failed_counts = _workspace_counts(workspace)
            failed_prepares_unchanged = (
                before_failed_prepares == after_failed_prepares
                and before_failed_counts == after_failed_counts
            )
            if not failed_prepares_unchanged:
                raise RuntimeError("rejected prepare requests changed saved workspace state")
            assert not (workspace / "jobs").exists()

            prepared_response, prepared_body = _prepare_saved(
                client, server_one.base_url, media, project_id, character, records
            )
            _require_status(prepared_response, 200, "saved-reference prepare")
            assert isinstance(prepared_body, dict)
            job_id = str(prepared_body["job_id"])
            assert prepared_body["project_id"] == project_id
            prepared = prepared_body["prepared"]
            assert set(prepared["config"]) == {
                "audio_mode", "reference_names", "scheduler_steps", "seed", "video_name", "with_audio"
            }

            workflow_response, _workflow = _call(
                client, server_one.base_url, "GET", f"/api/jobs/{job_id}/workflow", records
            )
            prompt_response, _prompt = _call(
                client, server_one.base_url, "GET", f"/api/jobs/{job_id}/prompt", records
            )
            _require_status(workflow_response, 200, "workflow download")
            _require_status(prompt_response, 200, "prompt download")

            run_response, run_body = _call(
                client, server_one.base_url, "POST", f"/api/jobs/{job_id}/run", records
            )
            _require_status(run_response, 200, "explicit dry-run")
            assert isinstance(run_body, dict) and run_body["state"] == "queued"
            terminal = _wait_complete(client, server_one.base_url, job_id, records)
            assert terminal["backend"] == "dry_run"

            artifacts: dict[str, dict[str, Any]] = {}
            for artifact in ("generated", "final", "side_by_side"):
                artifact_response, _artifact = _call(
                    client,
                    server_one.base_url,
                    "GET",
                    f"/api/jobs/{job_id}/artifacts/{artifact}",
                    records,
                )
                _require_status(artifact_response, 200, f"{artifact} download")
                downloaded = temp_root / "downloads" / f"{artifact}.mp4"
                downloaded.parent.mkdir(parents=True, exist_ok=True)
                downloaded.write_bytes(artifact_response.content)
                artifacts[artifact] = {
                    "bytes": len(artifact_response.content),
                    "sha256": sha256_bytes(artifact_response.content),
                    "content_type": artifact_response.headers.get("content-type", ""),
                    "probe": _media_probe(downloaded),
                }

            history_response, history_body = _call(
                client, server_one.base_url, "GET", f"/api/projects/{project_id}/jobs", records
            )
            _require_status(history_response, 200, "project history")
            assert isinstance(history_body, dict) and [item["job_id"] for item in history_body["jobs"]] == [job_id]
            original_history = history_body["jobs"]
            version_response, original_version = _call(
                client,
                server_one.base_url,
                "GET",
                f"/api/characters/{character['character']['character_id']}/versions/1",
                records,
            )
            _require_status(version_response, 200, "character version")
    finally:
        server_one.stop()

    before_restart = _hash_tree(workspace)
    before_counts = _workspace_counts(workspace)
    server_two = FoundationServer(_free_loopback_port(), workspace, evidence_root / "server-cycle-2.log")
    try:
        server_two.start()
        with requests.Session() as client:
            restarted_health_response, restarted_health = _call(
                client, server_two.base_url, "GET", "/api/health", records
            )
            _require_status(restarted_health_response, 200, "restarted health")
            _call(client, server_two.base_url, "GET", "/", records)
            restarted_projects_response, restarted_projects = _call(
                client, server_two.base_url, "GET", "/api/projects", records
            )
            _require_status(restarted_projects_response, 200, "restarted projects")
            assert isinstance(restarted_projects, dict)
            assert any(item["project_id"] == project_id for item in restarted_projects["projects"])

            restarted_version_response, restarted_version = _call(
                client,
                server_two.base_url,
                "GET",
                f"/api/characters/{character['character']['character_id']}/versions/1",
                records,
            )
            _require_status(restarted_version_response, 200, "restarted character version")
            assert restarted_version == original_version

            restarted_history_response, restarted_history = _call(
                client, server_two.base_url, "GET", f"/api/projects/{project_id}/jobs", records
            )
            _require_status(restarted_history_response, 200, "restarted history")
            assert isinstance(restarted_history, dict)
            assert restarted_history["jobs"] == original_history

            restarted_status_response, restarted_status = _call(
                client, server_two.base_url, "GET", f"/api/jobs/{job_id}/status", records
            )
            _require_status(restarted_status_response, 200, "restarted status")
            assert isinstance(restarted_status, dict) and restarted_status == terminal
            after_read_load = _hash_tree(workspace)
            after_read_counts = _workspace_counts(workspace)

            adjacent_response, adjacent_body = _call(
                client, server_two.base_url, "POST", "/api/projects", records,
                json={"name": "Adjacent Switch"}
            )
            _require_status(adjacent_response, 200, "adjacent project")
            assert isinstance(adjacent_body, dict)
            switched_response, switched_body = _call(
                client, server_two.base_url, "GET", f"/api/projects/{adjacent_body['project_id']}/jobs", records
            )
            _require_status(switched_response, 200, "adjacent history")
            assert isinstance(switched_body, dict) and switched_body["jobs"] == []
            _call(
                client,
                server_two.base_url,
                "GET",
                f"/api/characters/{character['character']['character_id']}/versions/1",
                records,
            )

            legacy_response, legacy_body = _call(
                client,
                server_two.base_url,
                "POST",
                "/api/prepare",
                records,
                files={
                    "source": (media["source"].name, media["source"].read_bytes(), "video/mp4"),
                    "reference_1": (media["primary"].name, media["primary"].read_bytes(), "image/png"),
                },
                data={"rights_attested": "true", "seed": "118"},
            )
            _require_status(legacy_response, 200, "legacy upload-only prepare")
            assert isinstance(legacy_body, dict) and "project_id" not in legacy_body
            legacy_job_id = str(legacy_body["job_id"])
            legacy_run_response, _legacy_run = _call(
                client, server_two.base_url, "POST", f"/api/jobs/{legacy_job_id}/run", records
            )
            _require_status(legacy_run_response, 200, "legacy explicit run")
            _wait_complete(client, server_two.base_url, legacy_job_id, records)
            final_project_history_response, final_project_history = _call(
                client, server_two.base_url, "GET", f"/api/projects/{project_id}/jobs", records
            )
            _require_status(final_project_history_response, 200, "final project history")
            assert isinstance(final_project_history, dict)
            assert final_project_history["jobs"] == original_history
    finally:
        server_two.stop()

    after_restart = _hash_tree(workspace)
    preserved_files = {
        name: {"before": digest, "after": after_restart.get(name)}
        for name, digest in before_restart.items()
        if name.startswith("uploads/") or name.startswith(f"jobs/{job_id}/")
    }
    old_preserved = all(item["before"] == item["after"] for item in preserved_files.values())
    final_counts = _workspace_counts(workspace)
    if not old_preserved:
        raise RuntimeError("project switch or legacy flow changed pre-existing protected/job bytes")

    receipt.update(
        {
            "project": {"project_id": project_id, "name": "Foundation Journey"},
            "character": character["character"],
            "job_id": job_id,
            "prepared_config": prepared["config"],
            "terminal_status": terminal,
            "artifacts": artifacts,
            "restart": {
                "project_preserved": True,
                "character_version_preserved": True,
                "prepared_config_preserved": True,
                "history_preserved": True,
                "no_new_run_submitted_by_read_load": before_restart == after_read_load,
                "pre_switch_file_hashes_unchanged": old_preserved,
                "workspace_before": before_counts,
                "workspace_after_restart_reads": after_read_counts,
                "workspace_final": final_counts,
            },
            "rejected_prepares": {
                "missing_saved_reference": True,
                "saved_and_uploaded_conflict": True,
                "missing_project": True,
                "duplicate_basename_actionable": True,
                "workspace_unchanged": failed_prepares_unchanged,
                "workspace_before": before_failed_counts,
                "workspace_after": after_failed_counts,
                "created_job_directories": 0,
            },
            "legacy_upload_only": {
                "job_id": legacy_job_id,
                "unrecorded_from_project": True,
                "explicit_run": True,
                "completed": True,
            },
            "http_records": records,
        }
    )
    _assert_public(receipt, (REPO, temp_root, evidence_root))
    receipt_path = evidence_root / "http-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for log_path in (evidence_root / "server-cycle-1.log", evidence_root / "server-cycle-2.log"):
        _assert_public(log_path.read_text(encoding="utf-8", errors="replace"), (REPO, temp_root, evidence_root))
    shutil.rmtree(temp_root)
    return receipt


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temp-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    arguments = parser.parse_args()
    result = run_trial(temp_root=arguments.temp_root, evidence_root=arguments.evidence_root)
    print(
        json.dumps(
            {
                "ok": True,
                "job_id": result["job_id"],
                "receipt": (arguments.evidence_root.resolve() / "http-receipt.json").as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
