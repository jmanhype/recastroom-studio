#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Real replay, review, selection, HTTP, SQLite, media, and browser proofs."""
from __future__ import annotations

import hashlib
import io
import json
import os
from dataclasses import replace
from pathlib import Path
import sqlite3
import subprocess
import sys
from textwrap import dedent

import pytest

from app.m1_api import _comparison_geometry, _comparison_window
from openjutsu.m1_types import (
    ExecutionMode, FrameRange, ReplayReceipt, ReviewVerdict, ShotSpec, Timebase, WindowMap, public_json,
)
from openjutsu.config import load_settings
from openjutsu.pipeline import prepare_managed_workflow
from openjutsu.recipe_service import WORKFLOW_PATH
from openjutsu.take_service import TakeService
from openjutsu.workspace_store import (
    AttemptConflictError, AssetIntegrityError, ValidationError, WorkspaceStore,
)
from test_m1_resolution import _raw_pixels, _resolve, _workspace
from test_m1_worker import _worker
from test_m1_scenes import _client
from tools.foundation_runtime import FFMPEG, FFPROBE, FoundationServer, free_loopback_port


MARKER = '{"historical_metadata_state":"absent","import_contract_version":1}'
MARKER_SHA256 = "5bb4de2fde14152f8197333d12f2ca4fd2f66a9e6869e9d5aad0e43dbd245005"


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _counts(store: WorkspaceStore) -> tuple[int, int, int, int, int]:
    with store._connect() as db:
        return tuple(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in (
            "attempts", "takes", "assets", "qualified_replay_receipts",
            "unqualified_import_evidence",
        ))


def _replay_fixture(root: Path):
    store, scene_id, *character = _workspace(root)
    operation = _resolve(store, scene_id, tuple(character))
    duplicate = _resolve(store, scene_id, tuple(character))
    store.authorize_attempt(operation, "replay-source", ExecutionMode.DRY_RUN, None)
    with store.worker_lock("replay-source"):
        assert _worker(store)
    with store._connect() as db:
        take_id = db.execute(
            "SELECT take_id FROM takes WHERE operation_id=?", (operation.id,)
        ).fetchone()[0]
    source_take = store.get_take(operation.project_id, take_id)
    manifest = json.loads(operation.canonical_json)
    receipt = ReplayReceipt(
        operation.scene_revision_id, operation.shot_id,
        manifest["source"]["sha256"], manifest["source"]["proxy_sha256"],
        operation.pin.recipe_id, operation.pin.version,
        operation.pin.raw_graph_sha256, manifest["graph"]["resolved_semantic_sha256"],
        source_take.output.sha256, operation.window, ReviewVerdict.KEEPER,
    )
    return store, operation, duplicate, source_take, receipt


def _tail_replay_fixture(
    store: WorkspaceStore, base_scene_id: str, character: tuple[str, int]
):
    base_scene = store.get_scene_revision(store.list_projects()[0].project_id, base_scene_id)
    scene = store.save_scene_revision(replace(
        base_scene, id="pending", revision=2, shots=(
            ShotSpec("front", FrameRange(0, 8), "pass_through"),
            ShotSpec("middle", FrameRange(8, 16), "render"),
            ShotSpec("tail", FrameRange(16, 24), "render"),
        ),
    ))
    operations = [
        _resolve(store, scene.id, character, shot_id=shot_id)
        for shot_id in ("middle", "tail")
    ]
    for operation in operations:
        store.authorize_attempt(
            operation, f"preview-{operation.shot_id}", ExecutionMode.DRY_RUN, None
        )
    with store.worker_lock("preview-worker"):
        assert all(_worker(store) for _ in operations)
    results = []
    for operation in operations:
        with store._connect() as db:
            take_id = db.execute(
                "SELECT take_id FROM takes WHERE operation_id=?", (operation.id,)
            ).fetchone()[0]
        dry_run = store.get_take(operation.project_id, take_id)
        output = store.resolve_asset(dry_run.output.asset_id).path.read_bytes()
        manifest = json.loads(operation.canonical_json)
        receipt = ReplayReceipt(
            operation.scene_revision_id, operation.shot_id,
            manifest["source"]["sha256"], manifest["source"]["proxy_sha256"],
            operation.pin.recipe_id, operation.pin.version,
            operation.pin.raw_graph_sha256,
            manifest["graph"]["resolved_semantic_sha256"],
            dry_run.output.sha256, operation.window, None,
        )
        replay = TakeService(store).import_replay(
            operation.project_id, receipt, io.BytesIO(output)
        )
        results.append((operation, dry_run, replay, receipt))
    return results


def test_qualified_replay_reviews_reversible_selection_and_restart(tmp_path: Path):
    store, operation, duplicate, source_take, receipt = _replay_fixture(tmp_path)
    before = _counts(store)
    content = store.resolve_asset(source_take.output.asset_id).path.read_bytes()
    replay = TakeService(store).import_replay(
        operation.project_id, receipt, io.BytesIO(content)
    )
    assert _counts(store) == (before[0], before[1] + 1, before[2] + 1, 1, 0)
    assert replay.attempt_id is None and replay.operation_id == min(operation.id, duplicate.id)
    assert replay.origin == "retained_replay" and replay.qualified is True
    assert replay.output.sha256 == receipt.output_sha256 and replay.output.receipt is None
    with store._connect() as db:
        row = db.execute("SELECT * FROM qualified_replay_receipts WHERE take_id=?", (replay.id,)).fetchone()
        assert row["historical_verdict"] == "keeper"
        assert json.loads(row["window_json"]) == json.loads(receipt.window.to_json())
        assert db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0

    service = TakeService(store)
    first = service.review(replay.id, ReviewVerdict.NEEDS_REVIEW, "human needs another look")
    second = service.review(replay.id, ReviewVerdict.KEEPER, "human keeper after comparison")
    selection = service.select(
        operation.project_id, operation.scene_revision_id, operation.shot_id, replay.id, 0
    )
    deselected = service.select(
        operation.project_id, operation.scene_revision_id, operation.shot_id, None, selection.revision
    )
    with pytest.raises(AttemptConflictError):
        service.select(
            operation.project_id, operation.scene_revision_id, operation.shot_id,
            replay.id, selection.revision,
        )
    assert first != second and store.list_reviews(replay.id) == [first, second]
    assert store.list_selections(
        operation.project_id, operation.scene_revision_id, operation.shot_id
    ) == [selection, deselected]

    reopened = WorkspaceStore(store.root)
    assert reopened.get_take(operation.project_id, replay.id) == replay
    assert reopened.list_reviews(replay.id) == [first, second]
    assert reopened.list_selections(
        operation.project_id, operation.scene_revision_id, operation.shot_id
    ) == [selection, deselected]


@pytest.mark.parametrize("byte_class", ["source", "input", "raw_graph", "resolved_graph", "output"])
def test_replay_rehashes_all_actual_byte_classes_and_rolls_back(tmp_path, byte_class):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    before = _counts(store)
    row = store._binding_row(operation.project_id, operation.id)
    original_bytes = None
    path = None
    if byte_class in {"source", "input", "resolved_graph"}:
        key = {"source": "source_asset_id", "input": "cpu_input_asset_id",
               "resolved_graph": "graph_asset_id"}[byte_class]
        path = store.resolve_asset(str(row[key])).path
        original_bytes = path.read_bytes()
    elif byte_class == "raw_graph":
        path = WORKFLOW_PATH
        original_bytes = path.read_bytes()
    try:
        if path is not None:
            path.write_bytes(original_bytes + b"\0")
        content = store.resolve_asset(source_take.output.asset_id).path.read_bytes()
        if byte_class == "output":
            content += b"\0"
        with pytest.raises((AssetIntegrityError, ValidationError)):
            TakeService(store).import_replay(
                operation.project_id, receipt, io.BytesIO(content)
            )
        assert _counts(store) == before
    finally:
        if path is not None:
            path.write_bytes(original_bytes)


def test_replay_output_rejects_same_average_irregular_pts(tmp_path):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    valid_path = store.resolve_asset(source_take.output.asset_id).path
    irregular_path = tmp_path / "irregular-pts.nut"
    subprocess.run([
        str(FFMPEG), "-nostdin", "-loglevel", "error", "-y", "-i", str(valid_path),
        "-vf", "setpts=if(eq(N\\,2)\\,PTS-1024\\,if(eq(N\\,3)\\,PTS+1024\\,PTS))",
        "-c:v", "ffv1", "-level", "3", "-g", "1", "-pix_fmt", "yuv420p",
        "-f", "nut", str(irregular_path),
    ], check=True, capture_output=True, timeout=30)
    def average_rate(path: Path) -> str:
        probe = subprocess.run([
            str(FFPROBE), "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate", "-of", "json", str(path),
        ], check=True, capture_output=True, text=True, timeout=30)
        return str(json.loads(probe.stdout)["streams"][0]["avg_frame_rate"])
    irregular_bytes = irregular_path.read_bytes()
    assert average_rate(valid_path) == average_rate(irregular_path)
    irregular_receipt = replace(
        receipt, output_sha256=hashlib.sha256(irregular_bytes).hexdigest()
    )
    before = _counts(store)
    with pytest.raises(ValidationError, match="irregular|timing"):
        TakeService(store).import_replay(
            operation.project_id, irregular_receipt, io.BytesIO(irregular_bytes)
        )
    assert _counts(store) == before


def test_comparison_geometry_supports_nonzero_offsets_padding_and_timebases():
    window = WindowMap(
        FrameRange(8, 24), Timebase(1, 24), FrameRange(0, 16), Timebase(1, 24),
        2, 4, 22, FrameRange(2, 18), FrameRange(8, 24), Timebase(1, 24),
        "hypothetical-identity-geometry",
    )
    assert _comparison_geometry(window) == (8, 24, 2, 18, "24/1")
    keep_out_of_bounds = replace(window, decoder_keep=FrameRange(2, 23))
    for bad in (keep_out_of_bounds,):
        with pytest.raises(ValidationError, match="geometry"):
            _comparison_geometry(bad)


def test_current_cpu_window_authority_rejects_unsupported_variants(tmp_path):
    store, scene_id, *character = _workspace(tmp_path)
    scene = store.get_scene_revision(store.list_projects()[0].project_id, scene_id)
    shot = scene.shots[1]
    qualified = _resolve(store, scene_id, tuple(character)).window
    TakeService._validated_current_cpu_window(store, shot, qualified)
    with pytest.raises(ValidationError, match="EVIDENCE_UNAVAILABLE"):
        TakeService._validated_current_cpu_window(
            store, shot, qualified, pin=replace(
                _resolve(store, scene_id, tuple(character)).pin, profile_id="unsupported"
            )
        )
    variants = (
        replace(qualified, decoder_keep=FrameRange(1, 8)),
        replace(qualified, render_range=FrameRange(0, 7), expected_decoder_frames=7),
        replace(qualified, timeline_timebase=Timebase(1, 30)),
        replace(qualified, qualification_id="unqualified-geometry"),
    )
    for window in variants:
        with pytest.raises(ValidationError, match="EVIDENCE_UNAVAILABLE"):
            TakeService._validated_current_cpu_window(store, shot, window)


def test_replay_output_rejects_consistent_shifted_first_pts(tmp_path):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    source_path = store.resolve_asset(store.get_scene_revision(
        operation.project_id, operation.scene_revision_id
    ).source.asset_id).path
    valid_path = store.resolve_asset(source_take.output.asset_id).path
    shifted_path = tmp_path / "consistent-shifted-first-pts.nut"
    subprocess.run([
        str(FFMPEG), "-nostdin", "-loglevel", "error", "-y", "-i", str(source_path),
        "-vf", "select=between(n\\,8\\,15),setpts=PTS+83052",
        "-c:v", "ffv1", "-level", "3", "-g", "1", "-pix_fmt", "yuv420p",
        "-f", "nut", str(shifted_path),
    ], check=True, capture_output=True, timeout=30)
    shifted = shifted_path.read_bytes()
    shifted_receipt = replace(
        receipt, output_sha256=hashlib.sha256(shifted).hexdigest()
    )
    assert TakeService._probe(valid_path)[2] == 0
    shifted_pts = TakeService._probe(shifted_path)[2]
    assert shifted_pts > 0
    before = _counts(store)
    with pytest.raises(ValidationError, match="decoder frame count or timing mismatch"):
        TakeService(store).import_replay(
            operation.project_id, shifted_receipt, io.BytesIO(shifted)
        )
    assert _counts(store) == before


def test_replay_filters_unrelated_variants_but_rejects_matching_distinct_class(tmp_path):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    unrelated = replace(
        operation, id="operation-unrelated-pin", managed_job_id="job-unrelated-pin",
        pin=replace(operation.pin, raw_graph_sha256="f" * 64),
    )
    store.save_operation(unrelated)
    binding = store._binding_row(operation.project_id, operation.id)
    columns = list(binding.keys())
    values = ["operation-unrelated-pin"] + [binding[column] for column in columns[1:]]
    duplicate_binding = store.stage_asset(
        operation.project_id, "unrelated-preparation-binding.json",
        io.BytesIO(store.resolve_asset(str(binding["binding_asset_id"])).path.read_bytes()),
        role="preparation_binding", protected=True,
    )
    values[columns.index("binding_asset_id")] = duplicate_binding.asset_id
    values[columns.index("binding_sha256")] = duplicate_binding.sha256
    with store._transaction() as db:
        db.execute(
            f"INSERT INTO preparation_bindings ({','.join(columns)}) "
            f"VALUES ({','.join('?' for _ in values)})", values,
        )
    content = store.resolve_asset(source_take.output.asset_id).path.read_bytes()
    assert TakeService(store).import_replay(
        operation.project_id, receipt, io.BytesIO(content)
    ).operation_id == min(operation.id, _duplicate.id)
    reference_ids = list(json.loads(str(binding["reference_asset_ids_json"])))
    references = [store.resolve_asset(asset_id) for asset_id in reference_ids]
    reversed_manifest = json.loads(operation.canonical_json)
    reversed_manifest["character"]["reference_hashes"].reverse()
    canonical_json = public_json(reversed_manifest)
    reversed_operation = replace(
        operation, id="operation-reversed-references",
        managed_job_id="job-reversed-references", canonical_json=canonical_json,
        fingerprint=hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
    )
    settings = load_settings({
        "RECASTROOM_BACKEND": "dry_run", "RECASTROOM_DATA_DIR": str(store.root / "managed"),
        "RECASTROOM_FFMPEG": "ffmpeg", "RECASTROOM_FFPROBE": "ffprobe",
        "RECASTROOM_WHISPER": "whisper",
    })
    prepared = prepare_managed_workflow(
        settings, job_id=reversed_operation.managed_job_id,
        source=store.resolve_asset(str(binding["cpu_input_asset_id"])).path,
        reference_1=references[1].path, reference_2=references[0].path,
        words_path=None, rights_attested=True, window=operation.window,
        source_has_audio=False, with_audio=False, seed=operation.seed,
        workflow_template=json.loads(WORKFLOW_PATH.read_text(encoding="utf-8")),
    )
    graph_asset = store.stage_asset(
        operation.project_id, "reversed-managed-workflow.json",
        io.BytesIO(Path(prepared.job.workflow_path).read_bytes()),
        role="managed_graph", protected=True,
    )
    original_envelope = json.loads(
        store.resolve_asset(str(binding["binding_asset_id"])).path.read_bytes()
    )
    plan = json.loads(prepared.workflow["1189"]["inputs"]["plan"])
    envelope = dict(original_envelope)
    envelope.update({
        "operation_id": reversed_operation.id,
        "operation_fingerprint": reversed_operation.fingerprint,
        "graph": {"asset_id": graph_asset.asset_id, "sha256": graph_asset.sha256,
                  "semantic_sha256": hashlib.sha256(json.dumps(
                      prepared.effective_workflow, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()).hexdigest()},
        "references": list(reversed(original_envelope["references"])),
        "substitutions": {
            "planner": {"video": plan["video"], "global_ref": plan["global_ref"],
                        "global_ref2": plan["global_ref2"],
                        "source_asset_id": str(binding["cpu_input_asset_id"]),
                        "reference_asset_ids": list(reversed(reference_ids))},
            "outputs": {"primary": prepared.workflow["751"]["inputs"]["filename_prefix"],
                        "comparison": prepared.workflow["1110"]["inputs"]["filename_prefix"]},
        },
    })
    reversed_binding = store.stage_asset(
        operation.project_id, "reversed-preparation-binding.json",
        io.BytesIO(json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        role="preparation_binding", protected=True,
    )
    store.save_operation(reversed_operation)
    reversed_values = ["operation-reversed-references"] + [binding[column] for column in columns[1:]]
    reversed_values[columns.index("binding_asset_id")] = reversed_binding.asset_id
    reversed_values[columns.index("binding_sha256")] = reversed_binding.sha256
    reversed_values[columns.index("operation_fingerprint")] = reversed_operation.fingerprint
    reversed_values[columns.index("graph_asset_id")] = graph_asset.asset_id
    reversed_values[columns.index("graph_sha256")] = graph_asset.sha256
    reversed_values[columns.index("reference_asset_ids_json")] = json.dumps(
        list(reversed(reference_ids)), separators=(",", ":")
    )
    reversed_values[columns.index("reference_sha256s_json")] = json.dumps(
        [item.record.sha256 for item in reversed(references)], separators=(",", ":")
    )
    reversed_values[columns.index("substitutions_json")] = json.dumps(
        envelope["substitutions"], sort_keys=True, separators=(",", ":")
    )
    with store._transaction() as db:
        db.execute(
            f"INSERT INTO preparation_bindings ({','.join(columns)}) "
            f"VALUES ({','.join('?' for _ in reversed_values)})", reversed_values,
        )
    before_failed_import = _counts(store)
    with pytest.raises(ValidationError, match="EVIDENCE_AMBIGUOUS"):
        TakeService(store).import_replay(operation.project_id, receipt, io.BytesIO(content))
    assert _counts(store) == before_failed_import
    before = _counts(store)
    other_project = store.create_project("cross-project").project_id
    with pytest.raises(ValidationError, match="EVIDENCE_UNAVAILABLE|scene does not match"):
        TakeService(store).import_replay(other_project, receipt, io.BytesIO(content))
    assert _counts(store) == before


def test_pm_reproduced_nullable_linkage_and_complete_parent_immutability(tmp_path):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    output = store.resolve_asset(source_take.output.asset_id).path.read_bytes()
    replay = TakeService(store).import_replay(
        operation.project_id, receipt, io.BytesIO(output)
    )
    unqualified = TakeService(store).import_unqualified(
        operation.project_id, operation.shot_id, None, io.BytesIO(output)
    )
    other_scene = store.save_scene_revision(replace(
        store.get_scene_revision(operation.project_id, operation.scene_revision_id),
        id="pending", revision=2,
    ))
    clone = store.stage_asset(
        operation.project_id, "pm-null-operation-output.nut", io.BytesIO(output),
        role="retained_replay_output", protected=True,
    )
    with store._connect() as db:
        qualified_row = db.execute(
            "SELECT * FROM qualified_replay_receipts WHERE take_id=?", (replay.id,)
        ).fetchone()
        attempt_id = db.execute(
            "SELECT attempt_id FROM takes WHERE operation_id=?", (operation.id,)
        ).fetchone()[0]

    valid_window_json = str(qualified_row["window_json"])
    malformed_windows = {
        "empty JSON object": "{}",
        "extra nested field": _canonical_json(
            json.loads(valid_window_json) | {"unexpected": True}
        ),
        "wrong scalar type": _canonical_json(
            json.loads(valid_window_json) | {"qualification_id": 1}
        ),
        "boolean integer field": _canonical_json(
            json.loads(valid_window_json) | {"pad_left": True}
        ),
        "negative range": _canonical_json(
            json.loads(valid_window_json) | {"source_range": {"start": -1, "end": 8}}
        ),
        "nonreduced timebase": _canonical_json(
            json.loads(valid_window_json)
            | {"source_timebase": {"num": 2, "den": 48}}
        ),
        "decoder keep beyond count": _canonical_json(
            json.loads(valid_window_json) | {"decoder_keep": {"start": 0, "end": 9}}
        ),
        "noncanonical serialization": json.dumps(
            dict(reversed(list(json.loads(valid_window_json).items()))),
            separators=(",", ":"),
        ),
    }
    for index, (label, malformed_window) in enumerate(malformed_windows.items()):
        with pytest.raises(ValidationError, match="scope is invalid|workspace invariant"):
            with store._transaction() as db:
                bad_take = f"take-bad-window-{index}"
                db.execute(
                    """INSERT INTO takes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (bad_take, operation.project_id, operation.scene_revision_id,
                     operation.shot_id, None, None, clone.asset_id, receipt.output_sha256,
                     receipt.window.expected_decoder_frames, receipt.window.render_timebase.num,
                     receipt.window.render_timebase.den, "retained_replay", 1, "now"),
                )
                bad_values = list(tuple(qualified_row))
                bad_values[0] = bad_take
                bad_values[13] = None
                bad_values[11] = malformed_window
                db.execute(
                    "INSERT INTO qualified_replay_receipts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    bad_values,
                )
        with store._connect() as db:
            assert db.execute(
                "SELECT 1 FROM takes WHERE take_id=?", (bad_take,)
            ).fetchone() is None, label
    nullable_take = "take-pm-null-operation"
    with store._transaction() as db:
        db.execute(
            """INSERT INTO takes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (nullable_take, operation.project_id, operation.scene_revision_id,
             operation.shot_id, None, None, clone.asset_id, receipt.output_sha256,
             receipt.window.expected_decoder_frames, receipt.window.render_timebase.num,
             receipt.window.render_timebase.den, "retained_replay", 1, "now"),
        )
        values = list(tuple(qualified_row))
        values[0] = nullable_take
        values[13] = None
        db.execute(
            "INSERT INTO qualified_replay_receipts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            values,
        )
    nullable = store.get_take(operation.project_id, nullable_take)
    assert nullable.operation_id is None and nullable.qualified is True
    with pytest.raises(ValidationError, match="EVIDENCE_UNAVAILABLE"):
        _comparison_window(store, nullable)
    with store._connect() as db:
        assert db.execute(
            "SELECT operation_id FROM qualified_replay_receipts WHERE take_id=?",
            (nullable_take,),
        ).fetchone()[0] is None

    def snapshot():
        with store._connect() as db:
            tables = (row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ))
            return {
                table: [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                for table in tables
            }

    sql_mutations = {
        "PM operation non-NULL to NULL": (
            f"UPDATE takes SET operation_id=NULL WHERE take_id='{replay.id}'"
        ),
        "PM qualified origin/state/count/timebase": (
            f"UPDATE takes SET origin='dry_run',qualified=0,frame_count=frame_count+1,"
            f"timebase_num=timebase_num+1 WHERE take_id='{replay.id}'"
        ),
        "PM output asset identity": (
            f"UPDATE takes SET output_asset_id='{clone.asset_id}' WHERE take_id='{replay.id}'"
        ),
        "PM unqualified attachment/qualification/origin": (
            f"UPDATE takes SET scene_revision_id='{operation.scene_revision_id}',"
            f"origin='dry_run',qualified=1 WHERE take_id='{unqualified.id}'"
        ),
        "qualified project scope": (
            f"UPDATE takes SET project_id='{store.create_project('other').project_id}' "
            f"WHERE take_id='{replay.id}'"
        ),
        "qualified scene scope": (
            f"UPDATE takes SET scene_revision_id='{other_scene.id}' "
            f"WHERE take_id='{replay.id}'"
        ),
        "qualified shot scope": (
            f"UPDATE takes SET shot_id='absent' WHERE take_id='{replay.id}'"
        ),
        "qualified attempt lineage": (
            f"UPDATE takes SET attempt_id='{attempt_id}' WHERE take_id='{replay.id}'"
        ),
        "qualified output hash": (
            f"UPDATE takes SET output_sha256='{'0' * 64}' WHERE take_id='{replay.id}'"
        ),
        "qualified timebase denominator": (
            f"UPDATE takes SET timebase_den=timebase_den+1 WHERE take_id='{replay.id}'"
        ),
        "unqualified project scope": (
            f"UPDATE takes SET project_id='{store.create_project('second').project_id}' "
            f"WHERE take_id='{unqualified.id}'"
        ),
        "unqualified shot/hash/state": (
            f"UPDATE takes SET shot_id='absent',output_sha256='{'0' * 64}',"
            f"frame_count=frame_count+1,timebase_num=timebase_num+1 "
            f"WHERE take_id='{unqualified.id}'"
        ),
    }
    for label, sql in sql_mutations.items():
        before = snapshot()
        with pytest.raises(ValidationError, match="workspace invariant|immutable|scope"):
            with store._transaction() as db:
                db.execute(sql)
        assert snapshot() == before, label


def test_v4_carriers_are_append_only_mutually_exclusive_and_parent_guarded(tmp_path):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    output = store.resolve_asset(source_take.output.asset_id).path.read_bytes()
    replay = TakeService(store).import_replay(
        operation.project_id, receipt, io.BytesIO(output)
    )
    unqualified = TakeService(store).import_unqualified(
        operation.project_id, operation.shot_id, None, io.BytesIO(output)
    )
    with store._connect() as db:
        before = {
            table: [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for table in (row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ))
        }
        qualified_row = db.execute(
            "SELECT * FROM qualified_replay_receipts WHERE take_id=?", (replay.id,)
        ).fetchone()
        unqualified_row = db.execute(
            "SELECT * FROM unqualified_import_evidence WHERE take_id=?", (unqualified.id,)
        ).fetchone()
    sql_operations = (
        "INSERT OR REPLACE INTO qualified_replay_receipts SELECT * FROM qualified_replay_receipts",
        "UPDATE qualified_replay_receipts SET created_at='changed'",
        "DELETE FROM qualified_replay_receipts",
        "INSERT OR REPLACE INTO unqualified_import_evidence SELECT * FROM unqualified_import_evidence",
        "UPDATE unqualified_import_evidence SET created_at='changed'",
        "DELETE FROM unqualified_import_evidence",
        f"UPDATE takes SET output_sha256='{'0' * 64}' WHERE take_id='{replay.id}'",
        f"DELETE FROM takes WHERE take_id='{replay.id}'",
        "UPDATE operations SET seed=seed+1",
        "DELETE FROM operations",
        "UPDATE scene_revisions SET source_sha256='0' || source_sha256",
        "DELETE FROM scene_revisions",
        "UPDATE shots SET ordinal=ordinal+1",
        "DELETE FROM shots",
        f"UPDATE assets SET filename='changed' WHERE asset_id='{replay.output.asset_id}'",
        f"DELETE FROM assets WHERE asset_id='{replay.output.asset_id}'",
        "INSERT INTO qualified_replay_receipts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        "INSERT INTO unqualified_import_evidence VALUES (?,?,?,?,?,?,?)",
    )
    for sql in sql_operations:
        placeholders = sql.count("?")
        values = (
            (unqualified.id, *tuple(qualified_row)[1:]) if placeholders == 15
            else (replay.id, *tuple(unqualified_row)[1:]) if placeholders == 7 else ()
        )
        with pytest.raises(ValidationError):
            with store._transaction() as db:
                db.execute(sql, values)
        with store._connect() as db:
            after = {
                table: [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                for table in before
            }
        assert after == before
    malformed_hash = list(tuple(qualified_row))
    malformed_hash[4] = str(malformed_hash[4]).upper()
    malformed_marker = list(tuple(unqualified_row))
    malformed_marker[4] = '{"historical_metadata_state":"present","import_contract_version":1}'
    for table, values in (
        ("qualified_replay_receipts", malformed_hash),
        ("unqualified_import_evidence", malformed_marker),
    ):
        with pytest.raises(ValidationError):
            with store._transaction() as db:
                db.execute(f"INSERT INTO {table} VALUES ({','.join('?' for _ in values)})", values)
        with store._connect() as db:
            assert {
                item: [tuple(row) for row in db.execute(f"SELECT * FROM {item} ORDER BY rowid")]
                for item in before
            } == before


def test_zero_operation_history_is_evidence_unavailable_without_writes(tmp_path):
    store, scene_id, *_character = _workspace(tmp_path / "workspace")
    scene = store.get_scene_revision(store.list_projects()[0].project_id, scene_id)
    shot = scene.shots[1]
    window = WindowMap(
        shot.source_range, scene.source.timebase,
        FrameRange(0, shot.source_range.end - shot.source_range.start), scene.source.timebase,
        0, 0, shot.source_range.end - shot.source_range.start,
        FrameRange(0, shot.source_range.end - shot.source_range.start),
        shot.source_range, scene.source.timebase, "unavailable-history",
    )
    receipt = ReplayReceipt(
        scene.id, shot.id, "a" * 64, "b" * 64, "recipe", "v1", "c" * 64,
        "d" * 64, "e" * 64, window, None,
    )
    before = _counts(store)
    with pytest.raises(ValidationError, match="EVIDENCE_UNAVAILABLE"):
        TakeService(store).import_replay(scene.project_id, receipt, io.BytesIO(b"historical"))
    assert _counts(store) == before


def test_unqualified_none_only_marker_and_rejections(tmp_path):
    store, scene_id, *_character = _workspace(tmp_path / "workspace")
    scene = store.get_scene_revision(store.list_projects()[0].project_id, scene_id)
    shot = scene.shots[1]
    service = TakeService(store)
    before = _counts(store)
    history = next((tmp_path / "workspace" / "input").glob("foundation-source.mp4")).read_bytes()
    bad_values = [
        "", "null", "None", "{}", "[]", "0", "1", "true", "false", {}, [],
        {"historical_metadata": None}, object(), b"null",
    ]
    for value in bad_values:
        with pytest.raises(ValidationError, match="literal None"):
            service.import_unqualified(scene.project_id, shot.id, value, io.BytesIO(b"evidence"))
        assert _counts(store) == before
    imported = service.import_unqualified(
        scene.project_id, shot.id, None, io.BytesIO(history)
    )
    marker = store.get_unqualified_import_evidence(imported.id)
    encoded = marker.encode("utf-8")
    assert len(encoded) == 66 and hashlib.sha256(encoded).hexdigest() == MARKER_SHA256
    with store._connect() as db:
        evidence = db.execute(
            "SELECT * FROM unqualified_import_evidence WHERE take_id=?", (imported.id,)
        ).fetchone()
    assert tuple(evidence)[3:6] == (
        imported.output.sha256, MARKER, MARKER_SHA256,
    )
    with pytest.raises(ValidationError):
        store.append_unqualified_import_evidence(
            imported.id, scene.project_id, shot.id, imported.output.sha256
        )
    with pytest.raises(ValidationError):
        service.select(scene.project_id, scene.id, shot.id, imported.id, 0)
    assert store.list_attached_takes(scene.project_id, scene.id, shot.id) == []
    reopened = WorkspaceStore(store.root)
    assert reopened.list_unqualified_takes(scene.project_id) == [imported]
    assert reopened.get_unqualified_import_evidence(imported.id) == MARKER


def test_real_http_multipart_import_list_comparison_review_and_cas(tmp_path):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    tail_previews = _tail_replay_fixture(
        store, operation.scene_revision_id, operation.character_version
    )
    output = store.resolve_asset(source_take.output.asset_id).path.read_bytes()
    for main, client in _client(store.root):
        active = main._workspace_store()
        assert active.root == store.root

        def assert_typed_preview(take_record: object, window: WindowMap) -> None:
            preview = client.get(
                f"/api/projects/{take_record.project_id}/takes/{take_record.id}/comparison"
            )
            assert preview.status_code == 200, preview.text
            assert preview.headers["content-type"].startswith("video/mp4")
            preview_path = tmp_path / f"preview-{take_record.id}.mp4"
            preview_path.write_bytes(preview.content)
            count, period, first_pts, _ticks = TakeService._probe(preview_path)
            expected_count = window.source_range.end - window.source_range.start
            assert count == expected_count and first_pts == 0 and period == Timebase(1, 24)

            def half(x_expression: str) -> bytes:
                return subprocess.run([
                    str(FFMPEG), "-nostdin", "-loglevel", "error", "-i", str(preview_path),
                    "-vf", f"crop=iw/2:ih:{x_expression}:0", "-map", "0:v:0",
                    "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1",
                ], check=True, capture_output=True, timeout=30).stdout

            scene = store.get_scene_revision(take_record.project_id, take_record.scene_revision_id)
            source_path = store.resolve_asset(scene.source.asset_id).path
            output_path = store.resolve_asset(take_record.output.asset_id).path
            left, right = half("0"), half("iw/2")
            source_frames = _raw_pixels(
                source_path, window.source_range.start, window.source_range.end
            )
            candidate_frames = _raw_pixels(
                output_path, window.decoder_keep.start, window.decoder_keep.end
            )
            frame_bytes = len(source_frames) // expected_count
            for frame_index in range(expected_count):
                source_frame = source_frames[frame_index * frame_bytes:(frame_index + 1) * frame_bytes]
                candidate_frame = candidate_frames[frame_index * frame_bytes:(frame_index + 1) * frame_bytes]
                preview_left = left[frame_index * frame_bytes:(frame_index + 1) * frame_bytes]
                preview_right = right[frame_index * frame_bytes:(frame_index + 1) * frame_bytes]
                assert len(preview_left) == len(source_frame) == len(preview_right)
                left_mean = sum(abs(a - b) for a, b in zip(preview_left, source_frame)) / frame_bytes
                right_mean = sum(abs(a - b) for a, b in zip(preview_right, candidate_frame)) / frame_bytes
                left_outliers = sum(abs(a - b) > 32 for a, b in zip(preview_left, source_frame)) / frame_bytes
                right_outliers = sum(abs(a - b) > 32 for a, b in zip(preview_right, candidate_frame)) / frame_bytes
                assert left_mean < 4 and right_mean < 4, frame_index
                assert left_outliers < 0.01 and right_outliers < 0.01, frame_index

        replay = client.post(
            f"/api/projects/{operation.project_id}/replay-import",
            files={"file": ("retained.nut", output, "video/x-nut"),
                   },
            data={"receipt": receipt.to_json()},
        )
        assert replay.status_code == 201, replay.text
        take = replay.json()
        listed = client.get(
            f"/api/projects/{operation.project_id}/scene-revisions/{operation.scene_revision_id}/takes",
            params={"shot_id": operation.shot_id},
        )
        assert listed.status_code == 200 and any(item["id"] == take["id"] for item in listed.json())
        imported = active.get_take(operation.project_id, take["id"])
        assert_typed_preview(source_take, operation.window)
        assert_typed_preview(imported, receipt.window)
        for tail_operation, tail_dry_run, tail_replay, tail_receipt in tail_previews:
            assert_typed_preview(tail_dry_run, tail_operation.window)
            assert_typed_preview(tail_replay, tail_receipt.window)
        review = client.post(
            f"/takes/{take['id']}/reviews",
            json={"verdict": "keeper", "note": "browser comparison reviewed"},
        )
        assert review.status_code == 201
        selected = client.put(
            f"/api/projects/{operation.project_id}/scene-revisions/{operation.scene_revision_id}/shots/{operation.shot_id}/selection",
            json={"take_id": take["id"], "expected_revision": 0},
        )
        assert selected.status_code == 200 and selected.json()["revision"] == 1
        stale = client.put(
            f"/api/projects/{operation.project_id}/scene-revisions/{operation.scene_revision_id}/shots/{operation.shot_id}/selection",
            json={"take_id": None, "expected_revision": 0},
        )
        assert stale.status_code == 409 and stale.json()["detail"] == "SELECTION_REVISION_CONFLICT"

        good = {"file": ("historical.nut", output, "video/x-nut")}
        accepted = client.post(
            f"/api/projects/{operation.project_id}/unqualified-import",
            files=good, data={"shot_id": operation.shot_id},
        )
        assert accepted.status_code == 201, accepted.text
        before_attempts = _counts(active)[0]
        rejected_payloads = [
            {"files": good, "data": {"shot_id": operation.shot_id, "historical_metadata": "null"}},
            {"files": good, "data": {"shot_id": operation.shot_id, "historical_metadata_json": "{}"}},
            {"files": good, "data": {"shot_id": operation.shot_id, "alias": ""}},
            {"files": good, "data": {"shot_id": operation.shot_id, "extra": "x"}},
            {"files": {**good, "extra": ("metadata", b"{}", "application/json")}, "data": {"shot_id": operation.shot_id}},
            {"files": {"file": ("a", b"a"), "file2": ("b", b"b")}, "data": {"shot_id": operation.shot_id}},
        ]
        for payload in rejected_payloads:
            response = client.post(
                f"/api/projects/{operation.project_id}/unqualified-import", **payload
            )
            assert response.status_code == 422, response.text
        boundary = "OJc5nrDuplicateBoundary"
        raw = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"shot_id\"\r\n\r\n"
            f"{operation.shot_id}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"shot_id\"\r\n\r\n"
            f"{operation.shot_id}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"x\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\nx\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")
        duplicate = client.post(
            f"/api/projects/{operation.project_id}/unqualified-import", content=raw,
            headers={"content-type": f"multipart/form-data; boundary={boundary}"},
        )
        assert duplicate.status_code == 422
        assert _counts(active)[0] == before_attempts
        assert client.get(f"/api/projects/{operation.project_id}/takes/unqualified").status_code == 200


def test_real_browser_comparison_review_selection_and_conflict(tmp_path):
    store, operation, _duplicate, source_take, receipt = _replay_fixture(tmp_path)
    output = store.resolve_asset(source_take.output.asset_id).path.read_bytes()
    imported = TakeService(store).import_replay(
        operation.project_id, receipt, io.BytesIO(output)
    )
    server = FoundationServer(free_loopback_port(), store.root, tmp_path / "browser-server.log")
    server.start()
    try:
        evidence_root = Path(os.environ.get("OJ_C5NR_BROWSER_EVIDENCE", str(tmp_path)))
        script = dedent("""
            from pathlib import Path
            import sys
            from playwright.sync_api import sync_playwright
            base_url, evidence_root = sys.argv[1], Path(sys.argv[2])
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, channel="chrome")
                page = browser.new_page(viewport={"width": 1440, "height": 1200})
                posts = []
                page.on("request", lambda request: posts.append(request.url) if request.method == "POST" else None)
                page.goto(base_url)
                page.wait_for_function("() => Boolean(window.StudioUI)")
                page.evaluate("() => window.StudioUI.finishWalkthrough()")
                page.locator("#advanced-studio > summary").click()
                page.wait_for_selector("#project-select", state="visible")
                page.select_option("#project-select", sys.argv[3])
                page.wait_for_selector("#m1-review-shot option[value=second]", state="attached")
                page.select_option("#m1-review-shot", "second")
                page.get_by_role("button", name="Compare synchronized").last.click()
                page.wait_for_function(
                    "() => document.getElementById('m1-comparison-preview').readyState >= 2"
                )
                page.fill("#m1-review-note", "real synchronized browser review")
                page.get_by_role("button", name="Append review").click()
                page.get_by_role("button", name="Select candidate").last.click()
                page.get_by_role("button", name="Refresh selection state").click()
                page.get_by_role("button", name="Select candidate").last.click()
                page.wait_for_function(
                    "() => document.getElementById('m1-review-note-status').textContent.includes('Selection conflict visible')"
                )
                assert page.locator("#m1-comparison-preview").evaluate("node => node.videoWidth") == 640
                assert "/api/projects/" in page.locator("#m1-comparison-preview").evaluate("node => node.src")
                assert not any("/attempts" in url for url in posts)
                evidence_root.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(evidence_root / "browser-review.png"), full_page=True)
                browser.close()
        """)
        browser_result = subprocess.run(
            [sys.executable, "-", server.base_url,
             str(evidence_root), operation.project_id],
            input=script, text=True, timeout=60, capture_output=True,
        )
        assert browser_result.returncode == 0, browser_result.stderr
        assert (evidence_root / "browser-review.png").is_file()
    finally:
        server.stop()
