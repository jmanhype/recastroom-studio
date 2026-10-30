# SPDX-License-Identifier: MIT
"""Real DTO, SQLite, FFprobe, HTTP, and restart proof for M1 scene setup."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import hashlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.main import app
from openjutsu.config import load_settings
from openjutsu.m1_types import *
from openjutsu.scene_service import SceneService, WindowQualificationUnavailableError
from openjutsu.workspace_store import WorkspaceStore, WorkspaceStoreError, _V4_REVERSE_TRIGGERS
from tools.foundation_runtime import FFPROBE, FoundationServer, generate_media, run_tool, sha256_file


ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64
FRAME = FrameRange(2, 12)
TIME = Timebase(1, 24)
WINDOW = WindowMap(FRAME, TIME, FrameRange(0, 10), TIME, 0, 0, 10, FrameRange(0, 10), FrameRange(3, 13), TIME, "qual-v1")
PIN = RecipePin("recipe", "v1", HASH, "profile", "adapter", "endpoint")
RECEIPT = Receipt("attempt", "provider", "request", "adapter", "endpoint", "receipt", HASH)
OUTPUT = OutputEvidence("output", HASH, 10, TIME, RECEIPT)
DTOs = [
    SourceTiming("source", HASH, 24, TIME, True, True),
    ShotSpec("shot", FRAME, "render"), FRAME, TIME,
    SceneRevision("scene", "project", SourceTiming("source", HASH, 24, TIME, True, True), (ShotSpec("shot", FRAME, "render"),), 1),
    WINDOW, PIN, ResolvedOperation("operation", "project", "scene", "shot", WINDOW, PIN, ("char", 1), 7, "{}", HASH, "job"),
    Fence("attempt", "owner", 1), AttemptRecord("attempt", "project", "operation", "client", ExecutionMode.DRY_RUN, None, AttemptState.PREPARED, None, 1),
    AttemptEvent("created", "{}"), Readiness(True, "ready", "ok"), BoundSubmission("operation", "binding", HASH, False), RECEIPT, OUTPUT,
    CancelResult(False, False, "cancellation is not supported"),
    TakeRecord("take", "project", "scene", "shot", "attempt", "operation", OUTPUT, "dry_run", True),
    ReplayReceipt("scene", "shot", HASH, HASH, "recipe", "v1", HASH, HASH, HASH, WINDOW, ReviewVerdict.KEEPER),
    ReviewRecord("review", "take", ReviewVerdict.KEEPER, "human reviewed"), SelectionRecord("project", "scene", "shot", "take", 2),
    EditItem("shot", "take", FRAME, FRAME, FrameRange(0, 10)), EditRevision("edit", "project", "scene", (EditItem("shot", "take", FRAME, FRAME, FrameRange(0, 10)),), AudioPolicy.MUTE, TIME),
    ExportRecord("export", "edit", "completed", "asset", HASH, "{}"),
    TakeRecord("unattached-take", "project", None, "shot", None, None, OUTPUT, "retained_replay", False),
    SelectionRecord("project", "scene", "unselected-shot", None, 1), ExportRecord("failed-export", "edit", "failed", None, None, "{}"),
]
EXPECTED_RECORDS = frozenset({
    "FrameRange", "Timebase", "SourceTiming", "ShotSpec", "SceneRevision", "WindowMap", "RecipePin",
    "ResolvedOperation", "Fence", "AttemptRecord", "AttemptEvent", "Readiness", "BoundSubmission",
    "Receipt", "OutputEvidence", "CancelResult", "TakeRecord", "ReplayReceipt", "ReviewRecord",
    "SelectionRecord", "EditItem", "EditRevision", "ExportRecord",
})


def _client(tmp_path: Path):
    import app.main as main
    saved = (main.SETTINGS, main.PROJECT_STORE, main.app.state.workspace_store)
    main.SETTINGS = load_settings({"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path), "OPENJUTSU_FFPROBE": str(FFPROBE)})
    try:
        with TestClient(main.app) as client:
            client.get("/api/health")
            yield main, client
    finally:
        main.SETTINGS, main.PROJECT_STORE, main.app.state.workspace_store = saved


def _source(store: WorkspaceStore, project_id: str, path: Path) -> str:
    return store.stage_asset(project_id, path.name, io.BytesIO(path.read_bytes()), role="source", protected=True).asset_id


def test_all_public_dto_contracts_roundtrip_and_are_frozen() -> None:
    for dto in DTOs:
        payload = dto.to_json()
        assert type(dto).from_json(payload) == dto
        assert "path" not in payload and "/Users/" not in payload
        with pytest.raises(FrozenInstanceError):
            setattr(dto, fields(dto)[0].name, "changed")
    assert {type(dto).__name__ for dto in DTOs} == EXPECTED_RECORDS
    assert SourceTiming.from_json(DTOs[0].to_json()).timebase == Timebase(1, 24)
    bad_values = [
        {"asset_id": "../escape", "sha256": HASH, "frame_count": 24, "timebase": TIME, "cfr": True, "has_audio": True},
        {"asset_id": "source", "sha256": "x", "frame_count": 24, "timebase": TIME, "cfr": True, "has_audio": True},
        {"asset_id": "source", "sha256": HASH, "frame_count": 0, "timebase": TIME, "cfr": True, "has_audio": True},
    ]
    for values in bad_values:
        with pytest.raises(ValueError):
            SourceTiming(**values)
    with pytest.raises(ValueError):
        Fence("attempt", "owner", 0)


def test_versioned_migration_repeats_and_rolls_back_without_m0_loss(tmp_path: Path) -> None:
    store = WorkspaceStore(tmp_path)
    project = store.create_project("M0 survives")
    asset = store.stage_asset(project.project_id, "reference.bin", io.BytesIO(b"protected"), role="reference", protected=True)
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as db:
        before = db.execute("SELECT project_id,name FROM projects").fetchall(), db.execute("SELECT * FROM assets").fetchall()
    m1_tables = ("qualified_replay_receipts", "unqualified_import_evidence", "preparation_bindings", "worker_epochs", "exports", "edit_revisions", "selection_events", "reviews", "takes", "provider_receipts", "attempt_events", "attempts", "operations", "shots", "scene_revisions")
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as legacy:
        for trigger in _V4_REVERSE_TRIGGERS:
            legacy.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        for table in m1_tables:
            legacy.execute(f"DROP TABLE {table}")
        legacy.execute("DROP INDEX assets_scope_key")
        legacy.execute("DROP TABLE schema_migrations")
        legacy.execute("CREATE TABLE operations (legacy_conflict TEXT NOT NULL PRIMARY KEY)")
        legacy.execute("INSERT INTO operations VALUES ('v0 conflict')")
        legacy.commit()
    with pytest.raises(WorkspaceStoreError):
        WorkspaceStore(tmp_path)
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "scene_revisions" not in tables and "shots" not in tables
        assert db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 0
        db.execute("DROP TABLE operations"); db.commit()
    reopened = WorkspaceStore(tmp_path)
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as db:
        after = db.execute("SELECT project_id,name FROM projects").fetchall(), db.execute("SELECT * FROM assets").fetchall()
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        versions = db.execute("SELECT version,name FROM schema_migrations ORDER BY version").fetchall()
    required = {"schema_migrations", "scene_revisions", "shots", "operations", "attempts", "attempt_events", "provider_receipts", "takes", "reviews", "selection_events", "edit_revisions", "exports", "worker_epochs", "preparation_bindings", "qualified_replay_receipts", "unqualified_import_evidence"}
    assert required <= tables and versions == [(1, "managed_milestone_one_schema"), (2, "scene_scoped_take_contract"), (3, "concrete_preparation_bindings"), (4, "replay_and_unqualified_import_evidence")] and before == after
    assert reopened.resolve_asset(asset.asset_id).record == asset


def test_exact_probe_reports_frame_period_and_rejects_vfr_without_paths(tmp_path: Path) -> None:
    store = WorkspaceStore(tmp_path / "workspace"); project = store.create_project("Probe")
    media = generate_media(tmp_path)
    fractional = tmp_path / "fractional.mp4"
    vfr = tmp_path / "vfr.mp4"
    run_tool(["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=24000/1001", "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(fractional)])
    run_tool(["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=24", "-t", "1", "-vf", "settb=1/1000,setpts=if(eq(N\\,0)\\,0\\,PREV_OUTPTS+if(eq(N\\,10)\\,100\\,40))", "-fps_mode", "passthrough", "-c:v", "libx264", "-bf", "0", "-pix_fmt", "yuv420p", str(vfr)])
    service = SceneService(store, ffprobe=str(FFPROBE))
    exact = service.probe_source(_source(store, project.project_id, media["source"]))
    ntsc = service.probe_source(_source(store, project.project_id, fractional))
    assert (exact.frame_count, exact.timebase, exact.cfr, exact.has_audio) == (24, Timebase(1, 24), True, True)
    assert (ntsc.frame_count, ntsc.timebase, ntsc.has_audio) == (24, Timebase(1001, 24000), False)
    with pytest.raises(Exception) as rejected:
        service.probe_source(_source(store, project.project_id, vfr))
    assert "variable-frame-rate" in str(rejected.value) and str(tmp_path) not in str(rejected.value)


def test_confirm_shots_requires_exact_complete_partition(tmp_path: Path) -> None:
    store = WorkspaceStore(tmp_path); project = store.create_project("Cuts"); other = store.create_project("Other")
    media = generate_media(tmp_path); service = SceneService(store, ffprobe=str(FFPROBE))
    source_id = _source(store, project.project_id, media["source"]); timing = service.probe_source(source_id)
    valid = (ShotSpec("render", FrameRange(0, 12), "render"), ShotSpec("pass", FrameRange(12, 24), "pass_through"))
    scene = service.confirm_shots(project.project_id, source_id, valid)
    assert scene.revision == 1 and scene.shots == valid and scene.source == timing
    for malformed in ({"id": "zero", "source_range": {"start": 0, "end": 0}, "kind": "render"}, {"id": "neg", "source_range": {"start": -1, "end": 24}, "kind": "pass_through"}):
        with pytest.raises(ValueError):
            ShotSpec.from_json(malformed)
    invalid = [
        (ShotSpec("gap", FrameRange(0, 23), "render"),), (ShotSpec("over", FrameRange(0, 13), "render"), ShotSpec("next", FrameRange(12, 24), "pass_through")),
        (ShotSpec("range", FrameRange(0, 25), "render"),), (ShotSpec("dup", FrameRange(0, 12), "render"), ShotSpec("dup", FrameRange(12, 24), "pass_through")),
    ]
    for shots in invalid:
        with pytest.raises(Exception, match="partition|greater|duplicated|out-of-range"):
            service.confirm_shots(project.project_id, source_id, shots)
    with pytest.raises(Exception, match="another project"):
        service.confirm_shots(other.project_id, source_id, valid)


def test_http_sources_and_scenes_use_active_store_and_never_execute(tmp_path: Path) -> None:
    for _main, client in _client(tmp_path):
        project = client.post("/api/projects", json={"name": "HTTP scenes"}).json()
        media = generate_media(tmp_path / "media")
        uploaded = client.post(f"/api/projects/{project['project_id']}/sources", files={"file": ("source.mp4", media["source"].read_bytes(), "video/mp4")})
        assert uploaded.status_code == 201
        timing = uploaded.json()
        assert (timing["frame_count"], timing["timebase"], timing["cfr"], timing["has_audio"]) == (24, {"num": 1, "den": 24}, True, True)
        body = {"source_asset_id": timing["asset_id"], "shots": [{"id": "one", "source_range": {"start": 0, "end": 9}, "kind": "render"}, {"id": "two", "source_range": {"start": 9, "end": 24}, "kind": "pass_through"}]}
        confirmed = client.post(f"/api/projects/{project['project_id']}/scenes", json=body)
        assert confirmed.status_code == 201
        scene = confirmed.json()
        assert scene["source"] == timing and scene["revision"] == 1 and client.get(f"/api/projects/{project['project_id']}/scenes").json() == [scene]
        with sqlite3.connect(tmp_path / "workspace.sqlite3") as db:
            assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
        assert str(tmp_path) not in json.dumps(scene)


def test_actual_http_ui_and_scene_revision_survive_fresh_process_restart(tmp_path: Path) -> None:
    media = generate_media(tmp_path / "media"); workspace = tmp_path / "workspace"; evidence = tmp_path / "evidence"; evidence.mkdir()
    from tools.foundation_runtime import free_loopback_port
    server = FoundationServer(free_loopback_port(), workspace, evidence / "server.log")
    server.start(); import requests
    with requests.Session() as http:
        project = http.post(f"{server.base_url}/api/projects", json={"name": "Restart"}).json(); assert project
        timing = http.post(f"{server.base_url}/api/projects/{project['project_id']}/sources", files={"file": ("source.mp4", media["source"].read_bytes(), "video/mp4")}).json()
        body = {"source_asset_id": timing["asset_id"], "shots": [{"id": "front", "source_range": {"start": 0, "end": 12}, "kind": "render"}, {"id": "tail", "source_range": {"start": 12, "end": 24}, "kind": "pass_through"}]}
        scene = http.post(f"{server.base_url}/api/projects/{project['project_id']}/scenes", json=body).json()
        home_one = http.get(f"{server.base_url}/").content; script_one = http.get(f"{server.base_url}/m1.js").content
    server.stop(); before = sha256_file(tmp_path / "workspace/workspace.sqlite3")
    server_two = FoundationServer(free_loopback_port(), workspace, evidence / "server-restart.log"); server_two.start()
    with requests.Session() as http:
        restored = http.get(f"{server_two.base_url}/api/projects/{project['project_id']}/scenes").json()
        home_two = http.get(f"{server_two.base_url}/").content; script_two = http.get(f"{server_two.base_url}/m1.js").content
    server_two.stop(); after = sha256_file(tmp_path / "workspace/workspace.sqlite3")
    assert restored == [scene] and home_one == home_two and script_one == script_two and before == after
    receipt = {"source_sha256": timing["sha256"], "scene": scene, "server_processes": 2, "read_only_database_sha256_before": before, "database_sha256_after": after}
    (evidence / "m1-restart.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    assert "/Users/" not in (evidence / "m1-restart.json").read_text()


def test_scene_ui_is_offline_connected_and_preserves_stale_response_guards() -> None:
    home = TestClient(app).get("/"); script = TestClient(app).get("/m1.js")
    assert home.status_code == script.status_code == 200
    for element_id in ("m1-scenes-heading", "m1-source", "m1-upload", "m1-shot-list", "m1-confirm", "m1-scenes"):
        assert f'id="{element_id}"' in home.text
    assert home.text.index("/projects.js") < home.text.index("/m1.js") < home.text.index("/studio.js")
    assert "does not resolve recipes, submit jobs, or generate media" in home.text and "read-only" in home.text
    assert "let requestEpoch = 0" in script.text and "const isCurrent = (version) => version === requestEpoch" in script.text
    assert "window.M1UI = Object.freeze({refresh" in script.text and "/api/projects/${encodeURIComponent(projectId)}/scenes" in script.text
    assert "projects:selection-change" in script.text and "projects:prepared" in script.text and "studio:reset" in script.text
    assert "/run" not in script.text and "URL.createObjectURL" not in script.text
    node = shutil.which("node")
    assert node is not None, "Node.js is required for JavaScript syntax verification"
    subprocess.run([node, "--check", str(ROOT / "app/web/m1.js")], check=True, capture_output=True, text=True)


def test_validate_window_fails_closed_before_recipe_resolution(tmp_path: Path) -> None:
    with pytest.raises(WindowQualificationUnavailableError, match="no qualified recipe window"):
        SceneService(WorkspaceStore(tmp_path / "workspace")).validate_window(DTOs[1], PIN)


def test_m1_router_precedes_static_ui_and_follows_active_settings(tmp_path: Path) -> None:
    import app.main as main
    api = next(index for index, route in enumerate(main.app.routes) if any(getattr(item, "path", "") == "/api/projects/{project_id}/scenes" for item in getattr(getattr(route, "original_router", route), "routes", [route])))
    static = next(index for index, route in enumerate(main.app.routes) if getattr(route, "name", "") == "web")
    assert api < static
    saved_settings, saved_store = main.SETTINGS, main.PROJECT_STORE
    try:
        for root in (tmp_path / "one", tmp_path / "two"):
            root.mkdir()
            main.SETTINGS = load_settings({"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(root)})
            assert main._workspace_store().root == root.resolve(strict=True)
        assert main.app.state.workspace_store is main.PROJECT_STORE and main.PROJECT_STORE is not saved_store
    finally:
        main.SETTINGS, main.PROJECT_STORE = saved_settings, saved_store
        main.app.state.workspace_store = saved_store
