# SPDX-License-Identifier: MIT
"""Frozen managed resolution, real persistence, HTTP, and fail-closed proofs."""
from __future__ import annotations

import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path
import sqlite3
import subprocess

import pytest

from openjutsu.config import load_settings
from openjutsu.m1_types import BoundSubmission, FrameRange, RecipePin, ResolvedOperation, ShotSpec, Timebase, WindowMap
from openjutsu.pipeline import prepare_managed_workflow
from openjutsu.recipe_service import (
    CPU_CLIP_SHA256,
    OFFLINE_PIN,
    OFFLINE_SOURCE_SHA256,
    RecipeIntegrityError,
    RecipeService,
    UnsupportedRecipeError,
    WORKFLOW_PATH,
)
from openjutsu.scene_service import SceneService
from openjutsu.timing import WordInterval, _frame
from openjutsu.workspace_store import WorkspaceStore
from openjutsu.workspace_store import AssetIntegrityError, ValidationError, _V4_REVERSE_TRIGGERS
from tools.foundation_runtime import (
    FFMPEG,
    FFPROBE,
    FoundationServer,
    free_loopback_port,
    generate_media,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FIXTURE = ROOT / "tests/fixtures/synthetic_source.mp4"
REFERENCE_FIXTURE = ROOT / "tests/fixtures/synthetic_reference.png"


def _workspace(tmp_path: Path) -> tuple[WorkspaceStore, str, tuple[str, int]]:
    store = WorkspaceStore(tmp_path / "workspace")
    project = store.create_project("Resolution")
    media = generate_media(tmp_path)
    source = store.stage_asset(
        project.project_id, media["source"].name, io.BytesIO(media["source"].read_bytes()),
        role="source", protected=True,
    )
    references = []
    for role, asset in (("reference_1", media["primary"]), ("reference_2", media["secondary"])):
        references.append(store.stage_asset(
            project.project_id, asset.name, io.BytesIO(asset.read_bytes()), role=role, protected=True
        ).asset_id)
    character = store.create_character_version("Frozen performer", references)
    timing = SceneService(store, ffprobe=str(FFPROBE)).probe_source(source.asset_id)
    scene = SceneService(store, ffprobe=str(FFPROBE)).confirm_shots(
        project.project_id, source.asset_id,
        (ShotSpec("first", FrameRange(0, 8), "render"),
         ShotSpec("second", FrameRange(8, 16), "render"),
         ShotSpec("tail", FrameRange(16, timing.frame_count), "pass_through")),
    )
    return store, scene.id, character.character_id, character.version


def _resolve(store: WorkspaceStore, scene_id: str, character: tuple[str, int],
             seed: int = 117, shot_id: str = "second", *, rights_attested: bool = True):
    return RecipeService(store).resolve(
        store.list_projects()[0].project_id, scene_id, shot_id, OFFLINE_PIN, character, seed,
        rights_attested=rights_attested,
    )


def _raw_pixels(path: Path, start: int, end: int) -> bytes:
    result = subprocess.run([
        str(FFMPEG), "-nostdin", "-loglevel", "error", "-i", str(path),
        "-vf", f"select='between(n\\,{start}\\,{end - 1})'", "-fps_mode", "passthrough",
        "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1",
    ], check=True, capture_output=True, timeout=30)
    return result.stdout


def test_recipe_resolution_freezes_effective_inputs_and_persists_in_one_store(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    operation = _resolve(store, scene_id, tuple(character))
    repeat = _resolve(store, scene_id, tuple(character))
    manifest = json.loads(operation.canonical_json)
    assert store.get_operation(operation.project_id, operation.id) == operation
    assert operation.fingerprint == hashlib.sha256(operation.canonical_json.encode()).hexdigest()
    assert repeat.fingerprint == operation.fingerprint and repeat.id != operation.id
    assert manifest["recipe"]["non_inference"] is True and manifest["recipe"]["h3_qualified"] is False
    assert manifest["source"]["original_pts"]["frame_period_seconds"] == {"num": 1, "den": 24}
    assert manifest["source"]["original_pts"]["first_frame"] == 8
    assert manifest["source"]["proxy_policy"] == "lossless_ffv1_extract"
    assert manifest["source"]["proxy_sha256"] == "ce1dc17d855b5d04aad9ac729d535fdc8b6e5f16a4d375e99d274d7216b2715c"
    assert manifest["graph"]["raw_sha256"] == OFFLINE_PIN.raw_graph_sha256
    artifact = store.root / "managed" / "jobs" / operation.managed_job_id / "effective-workflow.json"
    assert manifest["graph"]["resolved_semantic_sha256"] != manifest["graph"]["prepared_workflow_sha256"]
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == manifest["graph"]["prepared_workflow_sha256"]
    repeat_artifact = store.root / "managed" / "jobs" / repeat.managed_job_id / "effective-workflow.json"
    assert hashlib.sha256(repeat_artifact.read_bytes()).hexdigest() == manifest["graph"]["prepared_workflow_sha256"]
    assert manifest["character"]["reference_hashes"] == [
        "4d3b4ed2652ce453e10fb8dc6f44b317f76aae37659c7021ef44b87422a86343",
        "0cd734b612f4b224e015ce135237a013f1d186c574c60bc78da12d144705d072",
    ]
    assert manifest["effective_overrides"]["with_audio"] is False
    assert manifest["audio_policy"] == "source_edit_map"
    assert all(entry["support"] != "pass" for entry in manifest["graph"]["node_model_requirements"])
    serialized = json.dumps(manifest)
    assert str(tmp_path) not in serialized and SOURCE_FIXTURE.name not in serialized
    assert "asset_id" not in serialized and "filename" not in serialized
    changed_seed = _resolve(store, scene_id, tuple(character), 118)
    assert changed_seed.fingerprint != operation.fingerprint
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        reference_ids = [row[0] for row in db.execute(
            "SELECT asset_id FROM assets WHERE role IN ('reference_1','reference_2') ORDER BY role"
        )]
    second = store.create_character_version("Frozen performer", reference_ids, "v2")
    assert _resolve(store, scene_id, (second.character_id, second.version)).fingerprint != operation.fingerprint
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 4
        assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_strict_attestation_fails_before_any_resolution_side_effect(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    service = RecipeService(store)
    project_id = store.list_projects()[0].project_id
    for invalid in (False, None, 1, "true"):
        with pytest.raises(UnsupportedRecipeError, match="rights_attested"):
            service.resolve(project_id, scene_id, "second", OFFLINE_PIN,
                            tuple(character), 117, rights_attested=invalid)
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM preparation_bindings").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 3
    assert not (store.root / "managed").exists()
    assert _resolve(store, scene_id, tuple(character)).id.startswith("operation-")


def test_populated_v2_to_v3_migration_is_additive_and_idempotent(tmp_path: Path) -> None:
    store, scene_id, *_character = _workspace(tmp_path)
    database = tmp_path / "workspace/workspace.sqlite3"
    with sqlite3.connect(database) as db:
        for trigger in _V4_REVERSE_TRIGGERS:
            db.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        db.execute("DROP TABLE qualified_replay_receipts")
        db.execute("DROP TABLE unqualified_import_evidence")
        db.execute("DROP TABLE preparation_bindings")
        db.execute("DELETE FROM schema_migrations WHERE version >= 3")
        db.commit()
        assert [row[0] for row in db.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        )] == [1, 2]
        tables = [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )]
        before = {
            table: db.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            for table in tables if table != "schema_migrations"
        }
    WorkspaceStore(tmp_path / "workspace")
    with sqlite3.connect(database) as db:
        assert [row[0] for row in db.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        )] == [1, 2, 3, 4]
        objects = {row[0] for row in db.execute("SELECT name FROM sqlite_master")}
        assert {"preparation_bindings", "qualified_replay_receipts", "unqualified_import_evidence"} <= objects
        assert db.execute("SELECT COUNT(*) FROM qualified_replay_receipts").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM unqualified_import_evidence").fetchone()[0] == 0
        assert {"preparation_binding_immutable_update", "preparation_binding_immutable_delete"} <= objects
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        tables = [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )]
        after = {
            table: db.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            for table in tables if table not in {
                "schema_migrations", "preparation_bindings", "qualified_replay_receipts", "unqualified_import_evidence"}
        }
        assert after == before
    first_hash = hashlib.sha256(database.read_bytes()).hexdigest()
    WorkspaceStore(tmp_path / "workspace")
    assert hashlib.sha256(database.read_bytes()).hexdigest() == first_hash


def test_concrete_preparation_binding_is_immutable_and_revalidated(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    operation = _resolve(store, scene_id, tuple(character))
    project_id = operation.project_id
    scene = store.get_scene_revision(project_id, scene_id)
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        reference_ids = tuple(row[0] for row in db.execute(
            "SELECT asset_id FROM assets WHERE role IN ('reference_1','reference_2') ORDER BY role"
        ))
        row = db.execute(
            "SELECT binding_sha256,graph_asset_id FROM preparation_bindings WHERE operation_id = ?",
            (operation.id,),
        ).fetchone()
    binding = store.get_preparation_binding(project_id, operation.id)
    assert binding == store.verify_preparation_binding(
        project_id, operation.id, operation.fingerprint,
        source_asset_id=scene.source.asset_id, reference_asset_ids=reference_ids,
    )
    assert row[0] != json.loads(operation.canonical_json)["graph"]["resolved_semantic_sha256"]
    assert store.save_preparation_binding(
        operation, binding, source_asset_id=scene.source.asset_id,
        reference_asset_ids=reference_ids,
    ) == binding
    graph_path = store.resolve_asset(str(row[1])).path
    graph_bytes = graph_path.read_bytes()
    graph_path.write_bytes(graph_bytes + b"\0")
    with pytest.raises(AssetIntegrityError):
        store.verify_preparation_binding(
            project_id, operation.id, operation.fingerprint,
            source_asset_id=scene.source.asset_id, reference_asset_ids=reference_ids,
        )
    graph_path.write_bytes(graph_bytes)
    binding_path = store.resolve_asset(binding.binding_asset_id).path
    binding_bytes = binding_path.read_bytes()
    duplicate = store.stage_asset(
        project_id, "duplicate-binding.json", io.BytesIO(binding_bytes),
        role="preparation_binding", protected=True,
    )
    changed = BoundSubmission(operation.id, duplicate.asset_id, duplicate.sha256, False)
    with pytest.raises(ValidationError, match="immutable"):
        store.save_preparation_binding(
            operation, changed, source_asset_id=scene.source.asset_id,
            reference_asset_ids=reference_ids,
        )
    binding_path.write_bytes(binding_bytes + b"\0")
    with pytest.raises(AssetIntegrityError):
        store.get_preparation_binding(project_id, operation.id)
    binding_path.write_bytes(binding_bytes)
    with pytest.raises(ValidationError, match="verification mismatch"):
        store.verify_preparation_binding(
            project_id, operation.id, "f" * 64, source_asset_id=scene.source.asset_id,
            reference_asset_ids=reference_ids,
        )
    mutable = store.root / "managed" / "jobs" / operation.managed_job_id / "workflow.json"
    mutable.write_bytes(mutable.read_bytes() + b"\0")
    assert store.get_preparation_binding(project_id, operation.id) == binding


def test_finite_cpu_table_measures_exact_extraction_pts_and_pixels(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    project_id = store.list_projects()[0].project_id
    source_asset = store.get_scene_revision(project_id, scene_id).source.asset_id
    full_scene = SceneService(store, ffprobe=str(FFPROBE)).confirm_shots(
        project_id, source_asset, (ShotSpec("full", FrameRange(0, 24), "render"),)
    )
    cases = {
        "full": (full_scene.id, "full", 0, 24, None),
        "first": (scene_id, "first", 0, 8, CPU_CLIP_SHA256[(0, 8)]),
        "second": (scene_id, "second", 8, 16, CPU_CLIP_SHA256[(8, 16)]),
        "tail-render": (
            SceneService(store, ffprobe=str(FFPROBE)).confirm_shots(project_id, source_asset, (
                ShotSpec("prefix", FrameRange(0, 16), "pass_through"),
                ShotSpec("tail-render", FrameRange(16, 24), "render"),
            )).id, "tail-render", 16, 24, CPU_CLIP_SHA256[(16, 24)],
        ),
    }
    fingerprints = []
    source_path = store.resolve_asset(source_asset).path
    for label, (resolution_scene, shot_id, start, end, clip_hash) in cases.items():
        operation = _resolve(store, resolution_scene, tuple(character), shot_id=shot_id)
        manifest = json.loads(operation.canonical_json)
        count = end - start
        assert (operation.window.source_range.start, operation.window.source_range.end) == (start, end)
        assert (operation.window.render_range.start, operation.window.render_range.end) == (0, count)
        assert (operation.window.timeline_range.start, operation.window.timeline_range.end) == (start, end)
        assert operation.window.expected_decoder_frames == count and operation.window.pad_left == 0
        assert manifest["audio_policy"] == "source_edit_map"
        if clip_hash is None:
            input_path, policy = source_path, "original_protected_bytes"
        else:
            with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
                asset_id = db.execute(
                    "SELECT asset_id FROM assets WHERE role='cpu_input' AND sha256=?", (clip_hash,)
                ).fetchone()[0]
            input_path, policy = store.resolve_asset(asset_id).path, "lossless_ffv1_extract"
        assert manifest["source"]["proxy_sha256"] == (clip_hash or OFFLINE_SOURCE_SHA256)
        assert manifest["source"]["proxy_policy"] == policy
        assert _raw_pixels(source_path, start, end) == _raw_pixels(input_path, 0, count)
        probe = subprocess.run([
            str(FFPROBE), "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries", "stream=nb_read_frames,time_base", "-show_entries", "frame=pts,duration",
            "-of", "json", str(input_path),
        ], check=True, capture_output=True, text=True, timeout=30)
        payload = json.loads(probe.stdout)
        frames = payload["frames"][start:end] if clip_hash is None else payload["frames"]
        assert len(frames) == count and payload["streams"][0]["nb_read_frames"] in {str(24), str(count)}
        frame_period = Fraction(str(payload["streams"][0]["time_base"]))
        assert all(int(frame["duration"]) * frame_period == Fraction(1, 24) for frame in frames)
        fingerprints.append(operation.fingerprint)
    assert len(set(fingerprints)) == 4
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_forged_bindings_fail_and_operation_persistence_stays_atomic(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    operation = _resolve(store, scene_id, tuple(character))
    project_id = operation.project_id
    scene = store.get_scene_revision(project_id, scene_id)
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        reference_ids = tuple(row[0] for row in db.execute(
            "SELECT asset_id FROM assets WHERE role IN ('reference_1','reference_2') ORDER BY role"
        ))
        graph_id = db.execute(
            "SELECT graph_asset_id FROM preparation_bindings WHERE operation_id=?", (operation.id,)
        ).fetchone()[0]
    binding = store.get_preparation_binding(project_id, operation.id)
    envelope = json.loads(store.resolve_asset(binding.binding_asset_id).path.read_bytes())
    graph = json.loads(store.resolve_asset(graph_id).path.read_text())
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        assets_before = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]

    def forged(identifier: str, *, graph_override=None, substitution=None, cpu_map=None, prompt=None):
        managed_job_id = "managed-" + identifier
        next_operation = ResolvedOperation(
            "operation-" + identifier, operation.project_id, operation.scene_revision_id,
            operation.shot_id, operation.window, operation.pin, operation.character_version,
            operation.seed, operation.canonical_json, operation.fingerprint, managed_job_id,
        )
        next_graph = json.loads(json.dumps(graph))
        next_graph["751"]["inputs"]["filename_prefix"] = f"openjutsu/{managed_job_id}"
        next_graph["1110"]["inputs"]["filename_prefix"] = f"openjutsu/{managed_job_id}_compare"
        if graph_override is not None:
            next_graph = graph_override
        graph_asset = store.stage_asset(
            project_id, f"{identifier}-graph.json", io.BytesIO(json.dumps(next_graph).encode()),
            role="managed_graph", protected=True,
        )
        payload = json.loads(json.dumps(envelope))
        payload["operation_id"] = next_operation.id
        payload["graph"]["asset_id"] = graph_asset.asset_id
        payload["graph"]["sha256"] = graph_asset.sha256
        payload["substitutions"]["outputs"] = {
            "primary": f"openjutsu/{managed_job_id}",
            "comparison": f"openjutsu/{managed_job_id}_compare",
        }
        if substitution is not None:
            payload["substitutions"] = substitution
        if cpu_map is not None:
            payload["cpu_input"].update(cpu_map)
        if prompt is not None:
            payload["prompt_content"] = prompt
            payload["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
        content = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        asset = store.stage_asset(
            project_id, f"{identifier}-binding.json", io.BytesIO(content),
            role="preparation_binding", protected=True,
        )
        return next_operation, BoundSubmission(next_operation.id, asset.asset_id, asset.sha256, False)

    changed_output = json.loads(json.dumps(graph))
    changed_output["751"]["inputs"]["filename_prefix"] = "attacker/output"
    changed_output["1110"]["inputs"]["filename_prefix"] = "attacker/output_compare"
    changed_output["751"]["inputs"]["filename_prefix"] = "attacker/output"
    output_substitution = json.loads(json.dumps(envelope["substitutions"]))
    output_substitution["outputs"] = {
        "primary": "attacker/output", "comparison": "attacker/output_compare",
    }

    def role_candidate(identifier: str, field: str, forged_name: str):
        candidate_graph = json.loads(json.dumps(graph))
        candidate_plan = json.loads(candidate_graph["1189"]["inputs"]["plan"])
        candidate_plan[field] = forged_name
        candidate_graph["1189"]["inputs"]["plan"] = json.dumps(candidate_plan, separators=(",", ":"))
        candidate_graph["751"]["inputs"]["filename_prefix"] = f"openjutsu/managed-{identifier}"
        candidate_graph["1110"]["inputs"]["filename_prefix"] = f"openjutsu/managed-{identifier}_compare"
        candidate_substitution = {
            "planner": {**envelope["substitutions"]["planner"], field: forged_name},
            "outputs": {"primary": f"openjutsu/managed-{identifier}",
                        "comparison": f"openjutsu/managed-{identifier}_compare"},
        }
        return forged(identifier, graph_override=candidate_graph, substitution=candidate_substitution)

    failures = [
        ("output", "outputs", forged("output", graph_override=changed_output, substitution=output_substitution)),
        ("role-video", "concrete graph", role_candidate("role-video", "video", "attacker-source.nut")),
        ("role-primary", "concrete graph", role_candidate("role-primary", "global_ref", "attacker-primary.png")),
        ("role-secondary", "concrete graph", role_candidate("role-secondary", "global_ref2", "attacker-secondary.png")),
        ("slots", "concrete graph", forged("slots", substitution={
            "planner": {**envelope["substitutions"]["planner"],
                        "reference_asset_ids": list(reversed(reference_ids))},
            "outputs": {"primary": "openjutsu/managed-slots", "comparison": "openjutsu/managed-slots_compare"},
        })),
        ("map", "map", forged("map", cpu_map={"original_range": [7, 15]})),
        ("prompt", "canonical effective", forged("prompt", prompt="forged prompt")),
    ]
    for _label, expected_error, (next_operation, next_binding) in failures:
        with pytest.raises(ValidationError, match=expected_error):
            store._save_operation_and_preparation(
                next_operation, next_binding, source_asset_id=scene.source.asset_id,
                reference_asset_ids=reference_ids,
            )
    positive_operation, positive_binding = forged("positive-control")
    assert store._save_operation_and_preparation(
        positive_operation, positive_binding, source_asset_id=scene.source.asset_id,
        reference_asset_ids=reference_ids,
    ).id == positive_operation.id
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM preparation_bindings").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM assets").fetchone()[0] > assets_before


def test_unqualified_windows_profiles_and_drift_fail_closed(tmp_path: Path) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    service = RecipeService(store)
    h3 = RecipePin(OFFLINE_PIN.recipe_id, OFFLINE_PIN.version, OFFLINE_PIN.raw_graph_sha256,
                   "h3_gpu", OFFLINE_PIN.adapter_version, OFFLINE_PIN.endpoint_fingerprint)
    with pytest.raises(UnsupportedRecipeError, match="OWNER_BLOCKED"):
        service.resolve(store.list_projects()[0].project_id, scene_id, "first", h3,
                        tuple(character), 117, rights_attested=True)
    project_id = store.list_projects()[0].project_id
    source_asset = store.get_scene_revision(project_id, scene_id).source.asset_id
    n_minus_one = SceneService(store, ffprobe=str(FFPROBE)).confirm_shots(
        project_id, source_asset,
        (ShotSpec("short", FrameRange(0, 23), "render"), ShotSpec("tail", FrameRange(23, 24), "pass_through")),
    )
    with pytest.raises(UnsupportedRecipeError, match="finite"):
        service.resolve(project_id, n_minus_one.id, "short", OFFLINE_PIN,
                        tuple(character), 117, rights_attested=True)
    arbitrary = RecipePin("caller", "v1", "a" * 64, "custom", "adapter", "b" * 64)
    with pytest.raises(UnsupportedRecipeError, match="versioned pinned allowlist"):
        service.resolve(project_id, scene_id, "first", arbitrary,
                        tuple(character), 117, rights_attested=True)
    other = store.create_project("Other owner")
    media = generate_media(tmp_path / "other-media")
    foreign_refs = [store.stage_asset(other.project_id, asset.name, io.BytesIO(asset.read_bytes()),
                                      role=role, protected=True).asset_id
                    for role, asset in (("reference_1", media["primary"]), ("reference_2", media["secondary"]))]
    foreign = store.create_character_version("Foreign", foreign_refs)
    with pytest.raises(RecipeIntegrityError, match="project-owned"):
        service.resolve(project_id, scene_id, "first", OFFLINE_PIN,
                        (foreign.character_id, foreign.version), 117, rights_attested=True)


def test_graph_tamper_and_reference_drift_refuse_before_execution(tmp_path: Path, monkeypatch) -> None:
    store, scene_id, *character = _workspace(tmp_path)
    tampered = tmp_path / "tampered.json"
    payload = json.loads(WORKFLOW_PATH.read_text())
    payload["1189"]["inputs"]["plan"] = payload["1189"]["inputs"]["plan"].replace("24", "25")
    tampered.write_text(json.dumps(payload))
    import openjutsu.recipe_service as recipe_service
    monkeypatch.setattr(recipe_service, "WORKFLOW_PATH", tampered)
    with pytest.raises(RecipeIntegrityError, match="raw graph bytes changed"):
        _resolve(store, scene_id, tuple(character))
    monkeypatch.setattr(recipe_service, "WORKFLOW_PATH", WORKFLOW_PATH)
    with sqlite3.connect(tmp_path / "workspace/workspace.sqlite3") as db:
        reference_id = db.execute("SELECT asset_id FROM assets WHERE role = 'reference_1'").fetchone()[0]
    reference_path = store.resolve_asset(reference_id).path
    original = reference_path.read_bytes()
    reference_path.write_bytes(original + b"\0")
    with pytest.raises(RecipeIntegrityError, match="reference bytes changed"):
        _resolve(store, scene_id, tuple(character))


def test_managed_window_fps_audio_and_word_offset_are_explicit_not_defaulted(tmp_path: Path) -> None:
    assert _frame(0, 24) == 1
    timebase = Timebase(1, 24)
    window = WindowMap(
        FrameRange(8, 16), timebase, FrameRange(10, 18), timebase, 2, 2, 10,
        FrameRange(2, 10), FrameRange(8, 16), timebase, "explicit-test-window",
    )
    words = tmp_path / "words.json"
    words.write_text(json.dumps({"segments": [{"words": [
        {"start": 9 / 24, "end": 10 / 24, "word": "offset"},
    ]}]}))
    template = json.loads(WORKFLOW_PATH.read_text())

    def prepare(job_id: str, *, audio: bool):
        return prepare_managed_workflow(
            load_settings({"RECASTROOM_BACKEND": "dry_run", "RECASTROOM_DATA_DIR": str(tmp_path / "jobs")}),
            job_id=job_id, source=SOURCE_FIXTURE, reference_1=REFERENCE_FIXTURE, reference_2=None,
            words_path=words, rights_attested=True, window=window,
            source_has_audio=True, with_audio=audio, seed=117, workflow_template=template,
        )

    prepared = prepare("managed-one", audio=False)
    second = prepare("managed-two", audio=False)
    plan = json.loads(prepared.workflow["1189"]["inputs"]["plan"])
    effective_plan = json.loads(prepared.effective_workflow["1189"]["inputs"]["plan"])
    assert (plan["start_f"], plan["end_f"], plan["fps"]) == (10, 18, 24)
    assert plan["segs"][0]["chain_history"] == 10
    assert prepared.workflow["1177"]["inputs"]["with_audio"] is False
    assert prepared.workflow["200"]["inputs"]["start_frame"] == 2
    assert prepared.workflow["201"]["inputs"]["legacy_start_frame"] == 2
    assert "frames 2-3" in prepared.word_schedule and Path(prepared.job.workflow_path).is_file()
    assert plan["video"] == SOURCE_FIXTURE.name and effective_plan["video"] == "<source>"
    assert hashlib.sha256(json.dumps(prepared.effective_workflow, sort_keys=True).encode()).hexdigest() == hashlib.sha256(
        json.dumps(second.effective_workflow, sort_keys=True).encode()
    ).hexdigest()
    with pytest.raises(ValueError, match="incompatible"):
        prepare_managed_workflow(
            load_settings({"RECASTROOM_DATA_DIR": str(tmp_path / "jobs")}), job_id="bad-audio",
            source=SOURCE_FIXTURE, reference_1=REFERENCE_FIXTURE, reference_2=None,
            words_path=words, rights_attested=True, window=window, source_has_audio=False,
            with_audio=True, seed=1, workflow_template=template,
        )
    with pytest.raises(ValueError, match="operator attestation"):
        prepare_managed_workflow(
            load_settings({"RECASTROOM_DATA_DIR": str(tmp_path / "jobs")}), job_id="no-rights",
            source=SOURCE_FIXTURE, reference_1=REFERENCE_FIXTURE, reference_2=None,
            words_path=None, rights_attested=False, window=window, source_has_audio=True,
            with_audio=False, seed=1, workflow_template=template,
        )


def test_connected_http_api_and_vanilla_ui_resolve_without_enqueue(tmp_path: Path) -> None:
    workspace = tmp_path / "server-workspace"
    media = generate_media(tmp_path)
    server = FoundationServer(free_loopback_port(), workspace, tmp_path / "http-server.log")
    server.start()
    import requests
    try:
        with requests.Session() as http:
            project = http.post(f"{server.base_url}/api/projects", json={"name": "HTTP resolve"}, timeout=10).json()
            character = http.post(
                f"{server.base_url}/api/characters",
                data={"project_id": project["project_id"], "name": "HTTP performer", "description": ""},
                files={
                    "reference_1": (media["primary"].name, media["primary"].read_bytes(), "image/png"),
                    "reference_2": (media["secondary"].name, media["secondary"].read_bytes(), "image/png"),
                },
                timeout=10,
            ).json()["character"]
            timing = http.post(
                f"{server.base_url}/api/projects/{project['project_id']}/sources",
                files={"file": (media["source"].name, media["source"].read_bytes(), "video/mp4")},
                timeout=20,
            ).json()
            scene = http.post(
                f"{server.base_url}/api/projects/{project['project_id']}/scenes",
                json={"source_asset_id": timing["asset_id"], "shots": [{
                    "id": "first", "source_range": {"start": 0, "end": 8}, "kind": "render",
                }, {
                    "id": "second", "source_range": {"start": 8, "end": 16}, "kind": "render",
                }, {
                    "id": "tail", "source_range": {"start": 16, "end": 24}, "kind": "pass_through",
                }]},
                timeout=10,
            ).json()
            catalog = http.get(f"{server.base_url}/api/projects/{project['project_id']}/recipes", timeout=10).json()
            pin = catalog["profiles"][0]["pin"]
            body = {
                "scene_revision_id": scene["id"], "shot_id": "first", "pin": pin,
                "character_version": [character["character_id"], character["version"]], "seed": 117,
                "rights_attested": True,
            }
            resolved = http.post(
                f"{server.base_url}/api/projects/{project['project_id']}/operations/resolve",
                json=body, timeout=20,
            )
            assert resolved.status_code == 201, resolved.text
            operation = resolved.json()
            assert operation["pin"] == pin and operation["managed_job_id"].startswith("managed-")
            h3 = dict(pin, profile_id="h3_gpu")
            refused = http.post(
                f"{server.base_url}/api/projects/{project['project_id']}/operations/resolve",
                json=dict(body, pin=h3), timeout=10,
            )
            assert refused.status_code == 422 and "OWNER_BLOCKED" in refused.json()["detail"]
            invalid_payloads = [
                ("seed boolean", dict(body, seed=True)),
                ("seed string", dict(body, seed="117")),
                ("seed fractional", dict(body, seed=1.5)),
                ("seed unsafe integer", dict(body, seed=2 ** 53 + 1)),
                ("top-level graph", dict(body, workflow="caller.json")),
                ("pin graph", dict(body, pin=dict(pin, graph="caller.json"))),
                ("pin endpoint", dict(body, pin=dict(pin, endpoint="http://renderer"))),
                ("character version boolean", dict(body, character_version=[character["character_id"], True])),
                ("attestation omitted", {key: value for key, value in body.items() if key != "rights_attested"}),
                ("attestation false", dict(body, rights_attested=False)),
                ("attestation string", dict(body, rights_attested="true")),
                ("attestation number", dict(body, rights_attested=1)),
            ]
            for label, invalid in invalid_payloads:
                rejected = http.post(
                    f"{server.base_url}/api/projects/{project['project_id']}/operations/resolve",
                    json=invalid, timeout=10,
                )
                assert rejected.status_code == 422, (label, rejected.text)
            home = http.get(f"{server.base_url}/", timeout=10)
            script = http.get(f"{server.base_url}/m1.js", timeout=10)
            assert home.status_code == script.status_code == 200
            assert "m1-resolve" in script.text and "/operations/resolve" in script.text
            assert "getReferenceState" in script.text and "/run" not in script.text
            assert "Number.isSafeInteger" in script.text and "m1-rights" in script.text
            assert "rights_attested: $('m1-rights').checked" in script.text
            assert "manifest.graph.resolved_semantic_sha256" in script.text
            assert "manifest.graph.resolved_sha256" not in script.text
            assert "frozen references" in script.text and "overflowWrap" in script.text
            subprocess.run(["node", "--check", str(ROOT / "app/web/m1.js")], check=True, capture_output=True, text=True)
    finally:
        server.stop()
    with sqlite3.connect(workspace / "workspace.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 1
