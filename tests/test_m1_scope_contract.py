# SPDX-License-Identifier: MIT
"""Real SQLite storage contracts; NOT a substitute implementation of TakeService."""
from dataclasses import fields, replace
import hashlib
import io
import json
from pathlib import Path
import sqlite3

import pytest

from openjutsu.m1_types import (
    FrameRange, OutputEvidence, ReplayReceipt, SceneRevision, SelectionRecord,
    ShotSpec, SourceTiming, TakeRecord, Timebase, WindowMap,
)
from openjutsu.workspace_store import (
    ValidationError, WorkspaceStore, _M1_MIGRATION_STATEMENTS, _V4_REVERSE_TRIGGERS,
)

HASH = "a" * 64
TIME = Timebase(1, 24)
OUTPUT = OutputEvidence("output", HASH, 24, TIME, None)


def _insert(db: sqlite3.Connection, table: str, **row: object) -> None:
    db.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))


def _fixture(root: Path, *, v1: bool = False):
    store = WorkspaceStore(root)
    if v1:
        # Construct the exact historical v1 schema from its unchanged statements,
        # retaining real M0 tables. This is fixture setup, not a patched migrator.
        with store._transaction() as db:
            for trigger in _V4_REVERSE_TRIGGERS:
                db.execute(f"DROP TRIGGER IF EXISTS {trigger}")
            for table in ("qualified_replay_receipts", "unqualified_import_evidence", "preparation_bindings", "worker_epochs", "exports", "edit_revisions", "selection_events", "reviews", "takes",
                          "provider_receipts", "attempt_events", "attempts", "operations", "shots", "scene_revisions"):
                db.execute(f"DROP TABLE {table}")
            db.execute("DROP INDEX assets_scope_key")
            db.execute("DELETE FROM schema_migrations WHERE version > 1")
            for statement in _M1_MIGRATION_STATEMENTS:
                db.execute(statement)
            versions = [row[0] for row in db.execute("SELECT version FROM schema_migrations ORDER BY version")]
            objects = {row[0] for row in db.execute("SELECT name FROM sqlite_master")}
            take_columns = {row[1] for row in db.execute("PRAGMA table_info(takes)")}
            assert versions == [1] and "preparation_bindings" not in objects
            assert not any(name.startswith("preparation_binding_") for name in objects)
            assert "scene_revision_id" not in take_columns
    scopes = []
    for n in range(2):
        project = store.create_project(f"Project {n}").project_id
        asset = store.stage_asset(project, "protected.bin", io.BytesIO(b"protected source"), role="source", protected=True)
        for revision in range(2):
            scene = store.save_scene_revision(SceneRevision(
                "proposal", project, SourceTiming(asset.asset_id, asset.sha256, 24, TIME, True, False),
                (ShotSpec("shot-1", FrameRange(0, 24), "render"),), revision + 1))
            output = store.stage_asset(project, f"output-{revision}.bin", io.BytesIO(f"output {n}-{revision}".encode()), role="output")
            i = len(scopes)
            take = dict(take_id=f"take-{i}", project_id=project, shot_id="shot-1", attempt_id=f"attempt-{i}",
                        operation_id=f"op-{i}", output_asset_id=output.asset_id, output_sha256=output.sha256,
                        frame_count=24, timebase_num=1, timebase_den=24, origin="provider", qualified=1, created_at="retained")
            with store._transaction() as db:
                _insert(db, "operations", operation_id=f"op-{i}", project_id=project, scene_revision_id=scene.id,
                        shot_id="shot-1", window_json="{}", pin_json="{}", seed=1, canonical_json="{}",
                        fingerprint=HASH, managed_job_id=f"job-{i}", created_at="retained")
                _insert(db, "attempts", attempt_id=f"attempt-{i}", project_id=project, operation_id=f"op-{i}",
                        client_request_id=f"request-{i}", mode="sdk", state="completed", revision=1, created_at="retained")
                _insert(db, "takes", **take, **({} if v1 else {"scene_revision_id": scene.id}))
            scopes.append((project, scene.id, take))
    return store, scopes


def _snapshot(store: WorkspaceStore):
    with store._connect() as db:
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {table: [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")] for table in tables}


def test_exact_dto_scope_roundtrip_and_identical_construction_json_validation():
    take = TakeRecord("take", "project", "scene", "shot-1", None, None, OUTPUT, "retained_replay", True)
    unattached = replace(take, scene_revision_id=None, qualified=False)
    selection = SelectionRecord("project", "scene", "shot-1", None, 1)
    assert [f.name for f in fields(selection)] == ["project_id", "scene_revision_id", "shot_id", "take_id", "revision"]
    assert [f.name for f in fields(take)][:4] == ["id", "project_id", "scene_revision_id", "shot_id"]
    for dto in (take, unattached, selection):
        assert type(dto).from_json(dto.to_json()) == dto
    for dto, changes in ((take, {"scene_revision_id": None}), (take, {"scene_revision_id": "../scene"}),
                         (unattached, {"operation_id": "op"}), (unattached, {"attempt_id": "attempt"}),
                         (unattached, {"origin": "provider"}), (selection, {"project_id": ""}),
                         (selection, {"scene_revision_id": None}), (selection, {"revision": True})):
        payload = json.loads(dto.to_json()) | changes
        with pytest.raises(ValueError):
            type(dto)(**payload)
        with pytest.raises(ValueError):
            type(dto).from_json(payload)
    for dto in (take, selection):
        payload = json.loads(dto.to_json()); del payload["scene_revision_id"]
        with pytest.raises((ValueError, TypeError)):
            type(dto)(**payload)
        with pytest.raises(ValueError):
            type(dto).from_json(payload)


def test_four_scoped_streams_cas_deselect_restart_and_frozen_rows(tmp_path):
    store, scopes = _fixture(tmp_path)
    with store._transaction() as db:
        for i, (project, scene, take) in enumerate(scopes):
            _insert(db, "selection_events", selection_id=f"select-{i}", project_id=project,
                    scene_revision_id=scene, shot_id="shot-1", take_id=take["take_id"], revision=1, created_at="first")
        _insert(db, "edit_revisions", edit_revision_id="frozen", project_id=scopes[0][0], scene_revision_id=scopes[0][1],
                items_json='[{"shot_id":"shot-1","take_id":"take-0"}]', audio="mute", timebase_num=1,
                timebase_den=24, created_at="frozen")
    before = _snapshot(store)
    store = WorkspaceStore(tmp_path)
    project, scene, take = scopes[0]
    with store._transaction() as db:
        _insert(db, "selection_events", selection_id="deselect", project_id=project, scene_revision_id=scene,
                shot_id="shot-1", take_id=None, revision=2, created_at="second")
    store = WorkspaceStore(tmp_path)
    with store._connect() as db:
        assert db.execute("SELECT take_id,revision FROM selection_events WHERE selection_id='deselect'").fetchone()[:] == (None, 2)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert [r[2] for r in db.execute("PRAGMA index_xinfo(takes_project_shot_idx)")][:4] == [
            "project_id", "scene_revision_id", "shot_id", "created_at"]
    with pytest.raises(ValidationError):
        with store._transaction() as db:
            _insert(db, "selection_events", selection_id="stale", project_id=project, scene_revision_id=scene,
                    shot_id="shot-1", take_id="take-0", revision=2, created_at="stale")
    with store._transaction() as db:
        _insert(db, "selection_events", selection_id="reselect", project_id=project, scene_revision_id=scene,
                shot_id="shot-1", take_id="take-0", revision=3, created_at="third")
    after = _snapshot(WorkspaceStore(tmp_path))
    assert after["selection_events"][:4] == before["selection_events"]
    assert len(after["selection_events"]) == 6
    assert {k: v for k, v in after.items() if k != "selection_events"} == {k: v for k, v in before.items() if k != "selection_events"}
    with store._transaction() as db:
        _insert(db, "selection_events", selection_id="independent-cas", project_id=scopes[1][0], scene_revision_id=scopes[1][1],
                shot_id="shot-1", take_id=None, revision=2, created_at="independent")
    assert _snapshot(store)["selection_events"][:6] == after["selection_events"]


@pytest.mark.parametrize("bad", ["project", "shot", "other_scene_take", "other_project_take", "unqualified", "unattached", "missing", "malformed"])
def test_selection_scope_rejections_append_nothing(tmp_path, bad):
    store, scopes = _fixture(tmp_path)
    project, scene, take = scopes[0]
    with store._transaction() as db:
        if bad in ("unqualified", "unattached"):
            db.execute("UPDATE takes SET qualified=0 WHERE take_id='take-0'")
        if bad == "unattached":
            db.execute("UPDATE takes SET scene_revision_id=NULL,operation_id=NULL,attempt_id=NULL,origin='retained_replay' WHERE take_id='take-0'")
    row = dict(selection_id="bad", project_id=project, scene_revision_id=scene,
               shot_id="shot-1", take_id="take-0", revision=1, created_at="never")
    changes = {"project": {"project_id": scopes[2][0]}, "shot": {"shot_id": "absent"},
               "other_scene_take": {"take_id": "take-1"}, "other_project_take": {"take_id": "take-2"},
               "missing": {"scene_revision_id": None}, "malformed": {"scene_revision_id": "../invalid"}}
    before = _snapshot(store)
    with pytest.raises(ValidationError):
        with store._transaction() as db:
            _insert(db, "selection_events", **(row | changes.get(bad, {})))
    assert _snapshot(store) == before


@pytest.mark.parametrize("sql", [
    "UPDATE takes SET scene_revision_id=NULL WHERE take_id='take-0'",
    "UPDATE takes SET scene_revision_id=(SELECT scene_revision_id FROM takes WHERE take_id='take-1') WHERE take_id='take-0'",
    "UPDATE takes SET shot_id='absent' WHERE take_id='take-0'",
    "UPDATE takes SET operation_id='op-1' WHERE take_id='take-0'",
    "UPDATE takes SET attempt_id='attempt-1' WHERE take_id='take-0'",
    "UPDATE takes SET attempt_id='attempt-2' WHERE take_id='take-0'",
    "UPDATE takes SET output_asset_id=(SELECT output_asset_id FROM takes WHERE take_id='take-2') WHERE take_id='take-0'",
    "UPDATE operations SET shot_id='absent' WHERE operation_id='op-0'",
    "UPDATE attempts SET operation_id='op-1' WHERE attempt_id='attempt-0'",
])
def test_lineage_constraints_and_parent_mutations_rollback(tmp_path, sql):
    store, _ = _fixture(tmp_path)
    before = _snapshot(store)
    with pytest.raises(ValidationError):
        with store._transaction() as db:
            db.execute(sql)
    assert _snapshot(store) == before


def test_null_operation_still_enforces_real_composite_foreign_keys(tmp_path):
    store, scopes = _fixture(tmp_path)
    with store._transaction() as db:
        db.execute("UPDATE takes SET operation_id=NULL,attempt_id=NULL,origin='retained_replay' WHERE take_id='take-0'")
    before = _snapshot(store)
    for column, value in (("scene_revision_id", scopes[2][1]), ("shot_id", "absent")):
        with pytest.raises(ValidationError):
            with store._transaction() as db:
                db.execute(f"UPDATE takes SET {column}=? WHERE take_id='take-0'", (value,))
        assert _snapshot(store) == before
    with store._transaction() as db:
        # Same scope, distinct operations: equality of the attempt's operation
        # must be checked as well as equality of project/scene/shot.
        op = dict(db.execute("SELECT * FROM operations WHERE operation_id='op-0'").fetchone())
        _insert(db, "operations", **(op | {"operation_id": "alias-op", "managed_job_id": "alias-job"}))
    with pytest.raises(ValidationError):
        with store._transaction() as db:
            db.execute("UPDATE takes SET operation_id='alias-op',attempt_id='attempt-0' WHERE take_id='take-0'")


def test_qualified_replay_scope_with_null_operation_and_unattached_storage(tmp_path):
    store, scopes = _fixture(tmp_path)
    project, scene, take = scopes[0]
    window = WindowMap(FrameRange(0, 24), TIME, FrameRange(0, 24), TIME, 0, 0, 24,
                       FrameRange(0, 24), FrameRange(0, 24), TIME, "qualification")
    receipt = ReplayReceipt(scene, "shot-1", HASH, HASH, "recipe", "v1", HASH, HASH, take["output_sha256"], window, None)
    assert ReplayReceipt.from_json(receipt.to_json()) == receipt
    # Explicit v2 storage contract only: S4 owns validation/import of actual receipt bytes.
    with store._transaction() as db:
        db.execute("UPDATE takes SET operation_id=NULL,attempt_id=NULL,origin='retained_replay' WHERE take_id='take-0'")
        db.execute("UPDATE takes SET operation_id=NULL,attempt_id=NULL,origin='retained_replay',qualified=0,scene_revision_id=NULL WHERE take_id='take-1'")
        _insert(db, "selection_events", selection_id="replay-selection", project_id=project, scene_revision_id=receipt.scene_revision_id,
                shot_id=receipt.shot_id, take_id="take-0", revision=1, created_at="now")
    with WorkspaceStore(tmp_path)._connect() as db:
        assert db.execute("SELECT scene_revision_id,operation_id,qualified FROM takes WHERE take_id='take-0'").fetchone()[:] == (scene, None, 1)
        assert db.execute("SELECT scene_revision_id,operation_id,qualified FROM takes WHERE take_id='take-1'").fetchone()[:] == (None, None, 0)
    with pytest.raises(ValidationError):
        with store._transaction() as db:
            db.execute("UPDATE takes SET qualified=0 WHERE take_id='take-0'")


def test_populated_v1_backfill_preserves_history_assets_and_inbound_foreign_keys(tmp_path):
    store, scopes = _fixture(tmp_path, v1=True)
    project, scene, take = scopes[0]
    with store._transaction() as db:
        db.execute("UPDATE takes SET operation_id=NULL WHERE take_id='take-1'")  # verified attempt-only
        db.execute("UPDATE takes SET operation_id=NULL,attempt_id=NULL,origin='retained_replay',qualified=0 WHERE take_id='take-3'")
        _insert(db, "reviews", review_id="review", take_id="take-0", verdict="keeper", note="human", created_at="old")
        for revision in (1, 2):
            _insert(db, "selection_events", selection_id=f"selection-{revision}", project_id=project, shot_id="shot-1",
                    take_id="take-0", revision=revision, created_at="old")
        _insert(db, "attempt_events", event_id="event", attempt_id="attempt-0", sequence=0, kind="completed", payload_json="{}", created_at="old")
        _insert(db, "provider_receipts", attempt_id="attempt-0", provider_id="provider", request_key="request", adapter_version="v1",
                endpoint_fingerprint="local", receipt_asset_id=take["output_asset_id"], receipt_sha256=take["output_sha256"], recorded_at="old")
        _insert(db, "edit_revisions", edit_revision_id="edit", project_id=project, scene_revision_id=scene,
                items_json='[{"shot_id":"shot-1","take_id":"take-0"}]', audio="mute", timebase_num=1, timebase_den=24, created_at="old")
        _insert(db, "exports", export_id="export", edit_revision_id="edit", state="completed", asset_id=take["output_asset_id"],
                sha256=take["output_sha256"], checks_json='{"frozen":true}', created_at="old")
        _insert(db, "worker_epochs", epoch=1, owner_id="worker", acquired_at="old")
    before = _snapshot(store)
    asset_bytes = {p: p.read_bytes() for p in store.uploads_root.rglob("*") if p.is_file()}
    migrated = WorkspaceStore(tmp_path)
    with migrated._connect() as db:
        for table in ("takes", "selection_events"):
            columns = [row[1] for row in db.execute(f"PRAGMA table_info({table})") if row[1] != "scene_revision_id"]
            assert [tuple(row) for row in db.execute(f"SELECT {','.join(columns)} FROM {table} ORDER BY rowid")] == before[table]
        assert [r[0] for r in db.execute("SELECT scene_revision_id FROM takes ORDER BY take_id")] == [scopes[0][1], scopes[1][1], scopes[2][1], None]
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        for table in ("reviews", "selection_events"):
            assert "takes" in [r[2] for r in db.execute(f"PRAGMA foreign_key_list({table})")]
    after = _snapshot(migrated)
    assert before["schema_migrations"][0] == after["schema_migrations"][0]
    assert [r[0] for r in after["schema_migrations"]] == [1, 2, 3, 4]
    assert after["qualified_replay_receipts"] == []
    assert after["unqualified_import_evidence"] == []
    for table in before.keys() - {"takes", "selection_events", "schema_migrations"}:
        assert after[table] == before[table]
    assert asset_bytes and all(p.read_bytes() == data for p, data in asset_bytes.items())
    assert _snapshot(WorkspaceStore(tmp_path)) == after
    with pytest.raises(ValidationError):
        with migrated._transaction() as db:
            db.execute("DELETE FROM takes WHERE take_id='take-0'")
    assert _snapshot(migrated) == after


@pytest.mark.parametrize("bad", ["null_selection", "mixed_stream", "contradictory_attempt", "unproven_replay", "wrong_project", "late_asset_owner"])
def test_ambiguous_v1_refuses_atomically_with_byte_and_row_preservation(tmp_path, bad):
    store, scopes = _fixture(tmp_path, v1=True)
    project, scene, take = scopes[0]
    with store._transaction() as db:
        _insert(db, "selection_events", selection_id="legacy", project_id=project, shot_id="shot-1",
                take_id=None if bad == "null_selection" else "take-0", revision=1, created_at="old")
        if bad == "mixed_stream":
            _insert(db, "selection_events", selection_id="ambiguous", project_id=project, shot_id="shot-1", take_id="take-1", revision=2, created_at="old")
        if bad == "contradictory_attempt":
            db.execute("UPDATE takes SET attempt_id='attempt-1' WHERE take_id='take-0'")
        if bad == "unproven_replay":
            db.execute("UPDATE takes SET attempt_id=NULL,operation_id=NULL,origin='retained_replay' WHERE take_id='take-0'")
        if bad == "wrong_project":
            db.execute("UPDATE operations SET project_id=? WHERE operation_id='op-0'", (scopes[2][0],))
        if bad == "late_asset_owner":
            # Valid v1 references, invalid v2 composite ownership: fails after
            # CREATE INDEX/TABLE, proving DDL rollback as well as preflight refusal.
            db.execute("UPDATE assets SET project_id=? WHERE asset_id=?", (scopes[2][0], take["output_asset_id"]))
    before = _snapshot(store)
    original = store.db_path.read_bytes()
    for _ in range(2):
        with pytest.raises(ValidationError, match="scope migration v2:.*(retrying|authoritative).*(unchanged)"):
            WorkspaceStore(tmp_path)
        assert _snapshot(store) == before
        assert store.db_path.read_bytes() == original
        assert hashlib.sha256(store.db_path.read_bytes()).digest() == hashlib.sha256(original).digest()
