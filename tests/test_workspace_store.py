# SPDX-License-Identifier: MIT
"""Real SQLite persistence and path-boundary regressions for workspace records."""
from dataclasses import FrozenInstanceError, asdict
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile

import pytest

from openjutsu.config import Settings
from openjutsu.pipeline import prepare_workflow
from openjutsu.workspace_store import AssetIntegrityError, UnsafePathError, WorkspaceStore, WorkspaceStoreError


ROOT = Path(__file__).resolve().parents[1]


def _settings(root: Path) -> Settings:
    return Settings(comfy_url="http://127.0.0.1:1", backend="dry_run", data_dir=root,
                    workflow=ROOT / "workflows/openjutsu_h3_lipsync_local.json", ffmpeg="ffmpeg",
                    ffprobe="ffprobe", whisper="whisper")


def _make_job(root: Path, job_id: str) -> tuple[Path, Path]:
    source = root / "uploads" / f"{job_id}-source.bin"
    reference = root / "imports" / f"{job_id}-reference.bin"
    source.write_bytes(f"{job_id} source".encode())
    reference.write_bytes(f"{job_id} reference".encode())
    prepare_workflow(_settings(root), job_id=job_id, source=source, reference_1=reference,
                     reference_2=None, words_path=None, rights_attested=True,
                     identity_description="test identity", seed=17)
    return source, reference


def test_records_reopen_immutably_and_a_failed_insert_is_atomic(tmp_path):
    store = WorkspaceStore(tmp_path)
    first = store.create_project("First project")
    second = store.create_project("Second project")
    source = tmp_path / "uploads" / "source.bin"
    reference = tmp_path / "imports" / "reference.bin"
    source.write_bytes(b"shared source")
    reference.write_bytes(b"shared reference")
    source_asset = store.register_asset(first.project_id, source, "source", protected=True)
    reference_asset = store.register_asset(first.project_id, reference, "reference")
    duplicate = store.stage_asset(second.project_id, "duplicate.bin", io.BytesIO(b"shared source"), role="source")
    assert source_asset.sha256 == duplicate.sha256
    assert source_asset.size_bytes == duplicate.size_bytes
    assert (source_asset.asset_id, source_asset.project_id) != (duplicate.asset_id, duplicate.project_id)
    version_one = store.create_character_version("Elaya", [source_asset.asset_id, reference_asset.asset_id])
    version_two = store.create_character_version("elaya ", [duplicate.asset_id], "Reused identity")
    assert version_two.character_id == version_one.character_id
    assert version_two.version == 2
    assert store.get_character_version(version_one.character_id, 1) == version_one
    job_one, job_reference = _make_job(tmp_path, "job000000001")
    job_dir = tmp_path / "jobs" / "job000000001"
    prepared = store.record_prepared_job(first.project_id, "job000000001",
                                         job_dir, (version_one.character_id, 1))
    _make_job(tmp_path, "job000000002")
    reused = store.record_prepared_job(second.project_id, "job000000002",
                                       tmp_path / "jobs" / "job000000002", (version_one.character_id, 1))
    _make_job(tmp_path, "legacy0000001")
    legacy = store.record_prepared_job("", "legacy0000001", tmp_path / "jobs" / "legacy0000001")
    assert prepared.character_version == 1
    assert reused.character_id == version_one.character_id
    assert legacy.project_id == ""
    assert prepared.source_sha256 == hashlib.sha256(job_one.read_bytes()).hexdigest()
    assert prepared.reference_sha256s == [hashlib.sha256(job_reference.read_bytes()).hexdigest()]
    assert prepared.workflow_sha256 == hashlib.sha256((job_dir / "workflow.json").read_bytes()).hexdigest()
    assert prepared.prompt_sha256 == hashlib.sha256((job_dir / "prompt.txt").read_bytes()).hexdigest()
    assert (prepared.seed, prepared.config) == (17, {
        "audio_mode": "auto", "reference_names": [job_reference.name],
        "scheduler_steps": 8, "seed": 17, "video_name": job_one.name, "with_audio": True,
    })
    assert prepared.config != json.loads((job_dir / "workflow.json").read_text())
    assert store.list_prepared_jobs(first.project_id) == [prepared]
    assert store.list_prepared_jobs("") == [legacy]
    new_source = tmp_path / "uploads" / "transaction-source.bin"
    new_source.write_bytes(b"transaction source")
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as db:
        db.execute("CREATE TRIGGER fail_asset BEFORE INSERT ON assets "
                   "BEGIN SELECT RAISE(ABORT, 'injected local failure'); END")
    with pytest.raises(WorkspaceStoreError):
        store.register_asset(first.project_id, new_source, "source")
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as db:
        db.execute("DROP TRIGGER fail_asset")
    reopened = WorkspaceStore(tmp_path)
    assert reopened.list_projects() == [first, second]
    assert reopened.get_character_version(version_one.character_id, 1) == version_one
    assert reopened.get_character_version(version_one.character_id, 2) == version_two
    assert reopened.list_character_versions() == [version_one, version_two]
    assert reopened.list_prepared_jobs(first.project_id) == [prepared]
    assert reopened.list_prepared_jobs(second.project_id) == [reused]
    assert reopened.list_prepared_jobs("") == [legacy]
    assert reopened.resolve_asset(source_asset.asset_id).record == source_asset
    with pytest.raises(FrozenInstanceError):
        prepared.seed = 18  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.name = "changed"  # type: ignore[misc]


def test_register_and_resolve_enforce_permitted_regular_files(tmp_path):
    store = WorkspaceStore(tmp_path)
    project = store.create_project("Imports")
    upload = tmp_path / "uploads" / "nested" / "source.bin"; upload.parent.mkdir()
    upload.write_bytes(b"stable bytes")
    original = upload.read_bytes()
    before_stat = upload.stat()
    asset = store.register_asset(project.project_id, upload, "source", protected=True)
    assert upload.read_bytes() == original
    assert upload.stat().st_mtime_ns == before_stat.st_mtime_ns
    assert (asset.filename, asset.media_type) == ("source.bin", "application/octet-stream")
    assert "path" not in asdict(asset)
    resolved = store.resolve_asset(asset.asset_id)
    assert resolved.path == upload.resolve()
    assert resolved.record == asset
    outside = tmp_path / "outside" / "secret.bin"; outside.parent.mkdir()
    outside.write_bytes(b"outside")
    with pytest.raises(UnsafePathError) as outside_error:
        store.register_asset(project.project_id, outside, "source")
    assert str(outside_error.value) == "asset path is outside a configured root"
    missing = tmp_path / "uploads" / "missing.bin"
    with pytest.raises(WorkspaceStoreError, match="asset file not found"):
        store.register_asset(project.project_id, missing, "source")
    with pytest.raises(WorkspaceStoreError, match="malformed project ID"):
        store.register_asset("../outside", upload, "source")
    with pytest.raises(UnsafePathError, match="traversal"):
        store.register_asset(project.project_id, tmp_path / "uploads" / ".." / "outside" / "secret.bin", "source")
    real = tmp_path / "uploads" / "real.bin"
    real.write_bytes(b"real target")
    internal = tmp_path / "uploads" / "internal-link"; internal.symlink_to("../real", target_is_directory=True)
    escape = tmp_path / "uploads" / "escape-link"; escape.symlink_to(outside, target_is_directory=True)
    for unsafe in (internal / "real.bin", escape / "secret.bin"):
        with pytest.raises(UnsafePathError):
            store.register_asset(project.project_id, unsafe, "source")

    duplicate = tmp_path / "uploads" / "duplicate.bin"
    duplicate.write_bytes(original)
    duplicate_asset = store.register_asset(project.project_id, duplicate, "reference")
    assert (duplicate_asset.sha256, duplicate_asset.asset_id, duplicate_asset.role) == (
        asset.sha256, duplicate_asset.asset_id, "reference") and duplicate_asset.asset_id != asset.asset_id
    upload.write_bytes(b"changed protected bytes")
    with pytest.raises(AssetIntegrityError) as integrity_error:
        store.resolve_asset(asset.asset_id)
    assert "protected asset bytes" in str(integrity_error.value)
    assert str(tmp_path) not in str(integrity_error.value)
    upload.write_bytes(original)
    assert store.resolve_asset(asset.asset_id).record == asset


def _assert_configured_root_alias_is_normalized(
    caller_alias: Path, canonical_root: Path, project_name: str
) -> None:
    assert caller_alias != canonical_root
    store = WorkspaceStore(caller_alias)
    assert caller_alias.resolve(strict=True) == canonical_root
    assert store.root == canonical_root
    project = store.create_project(project_name)
    source = caller_alias / "uploads" / "normalized.bin"
    content = b"normalized path bytes"
    source.write_bytes(content)
    asset = store.register_asset(project.project_id, source, "source", protected=True)
    resolved = store.resolve_asset(asset.asset_id)
    assert resolved.path == canonical_root / "uploads" / "normalized.bin"
    assert resolved.record == asset
    assert asset.protected is True
    assert (asset.size_bytes, asset.sha256) == (
        len(content), hashlib.sha256(content).hexdigest()
    )
    assert resolved.path.read_bytes() == content


def _native_tmp_alias_exists() -> bool:
    public_tmp, private_tmp = Path("/tmp"), Path("/private/tmp")
    try:
        return (
            public_tmp.is_dir()
            and private_tmp.is_dir()
            and public_tmp != private_tmp
            and public_tmp.samefile(private_tmp)
        )
    except OSError:
        return False


def test_workspace_root_alias_is_normalized_without_escaping(tmp_path):
    canonical_parent = tmp_path / "canonical-root"
    caller_parent = tmp_path / "caller-root"
    canonical_parent.mkdir()
    caller_parent.symlink_to(canonical_parent, target_is_directory=True)
    _assert_configured_root_alias_is_normalized(
        caller_parent / "workspace", canonical_parent / "workspace", "portable alias"
    )
    if _native_tmp_alias_exists():
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            caller_alias = Path(directory)
            _assert_configured_root_alias_is_normalized(
                caller_alias, caller_alias.resolve(strict=True), "native temp alias"
            )


def test_stage_asset_uses_generated_upload_location_and_safe_names(tmp_path):
    store = WorkspaceStore(tmp_path)
    project = store.create_project("Staging")
    content = io.BytesIO(b"multipart bytes")
    asset = store.stage_asset(project.project_id, "reference.bin", content, role="reference", protected=True)
    assert content.tell() == len(b"multipart bytes")
    assert (asset.size_bytes, asset.sha256, asset.filename) == (
        len(b"multipart bytes"), hashlib.sha256(b"multipart bytes").hexdigest(), "reference.bin")
    assert "path" not in asdict(asset)
    staged_paths = list((tmp_path / "uploads").glob("*/*")); assert len(staged_paths) == 1
    staged = staged_paths[0]; staging_id = staged.parent.name
    assert staged.name == "reference.bin" and len(staging_id) == 32 and int(staging_id, 16) >= 0
    assert staged.read_bytes() == b"multipart bytes"
    assert store.resolve_asset(asset.asset_id).path == staged.resolve()

    duplicate = store.stage_asset(project.project_id, "same.bin", io.BytesIO(b"multipart bytes"), role="source")
    assert (duplicate.asset_id, duplicate.role) != (asset.asset_id, asset.role)
    assert duplicate.sha256 == asset.sha256

    before = {path.parent.name for path in (tmp_path / "uploads").iterdir()}
    for bad_name in ("../escape.bin", "nested/reference.bin", "/tmp/x", ".", "..", "bad\0name"):
        with pytest.raises(WorkspaceStoreError, match="single safe filename"):
            store.stage_asset(project.project_id, bad_name, io.BytesIO(b"x"), role="source")
    assert {path.parent.name for path in (tmp_path / "uploads").iterdir()} == before


@pytest.mark.parametrize("two_references", [False, True])
def test_custom_graph_history_is_safe_and_artifacts_are_unchanged(tmp_path, two_references):
    store = WorkspaceStore(tmp_path)
    project = store.create_project("Custom workflow")
    source, reference = _make_job(tmp_path, "customjob")
    second = tmp_path / "imports" / "second.bin"
    second.write_bytes(b"synthetic second reference")
    template = json.loads(_settings(tmp_path).workflow.read_text())
    sentinels = ["SYNTHETIC_API_KEY_NOT_A_REAL_CREDENTIAL",
                 "/private/tmp/synthetic/private-input.mov", "SYNTHETIC_NESTED_MAP", "SYNTHETIC_LIST"]
    template["custom_metadata"] = {"nested": {"credential": sentinels[0], "path": sentinels[1],
                                              "marker": sentinels[2]}, "list": [sentinels[3]]}
    plan = json.loads(template["1189"]["inputs"]["plan"])
    plan["extra"] = template["custom_metadata"]
    template["1189"]["inputs"]["plan"] = json.dumps(plan)
    custom_path = tmp_path / "custom.json"
    custom_path.write_text(json.dumps(template))
    prepare_workflow(_settings(tmp_path), job_id="customjob", source=source, reference_1=reference,
                     reference_2=second if two_references else None, words_path=None,
                     rights_attested=True, identity_description="SYNTHETIC_PRIVATE_PROMPT", seed=17,
                     workflow_template=custom_path)
    job_dir = tmp_path / "jobs" / "customjob"
    before = {path: path.read_bytes() for path in [*job_dir.iterdir(), source, reference, second, custom_path]}
    assert set(path.name for path in job_dir.iterdir()) == {"job.json", "workflow.json", "prompt.txt"}
    full_graph = json.loads(before[job_dir / "workflow.json"])
    assert full_graph["custom_metadata"] == template["custom_metadata"]
    expected = {"audio_mode": "auto", "reference_names": [reference.name] + ([second.name] if two_references else []),
                "scheduler_steps": 8, "seed": 17, "video_name": source.name, "with_audio": True}
    record = store.record_prepared_job(project.project_id, "customjob", job_dir)
    assert record.config == expected and record.config != full_graph
    with sqlite3.connect(store.db_path) as db:
        persisted = db.execute("SELECT config_json FROM prepared_configs").fetchone()[0]
    assert json.loads(persisted) == expected
    for sentinel in [*sentinels, "SYNTHETIC_PRIVATE_PROMPT", str(tmp_path)]:
        assert sentinel not in persisted and sentinel not in json.dumps(record.config)
    assert WorkspaceStore(tmp_path).list_prepared_jobs(project.project_id) == [record]
    assert {path: path.read_bytes() for path in before} == before
    assert set(job_dir.iterdir()) == {path for path in before if path.parent == job_dir}
    assert record.workflow_sha256 == hashlib.sha256(before[job_dir / "workflow.json"]).hexdigest()
    assert record.prompt_sha256 == hashlib.sha256(before[job_dir / "prompt.txt"]).hexdigest()
    assert record.source_sha256 == hashlib.sha256(before[source]).hexdigest()
    assert record.reference_sha256s == [hashlib.sha256(before[path]).hexdigest()
                                       for path in ([reference, second] if two_references else [reference])]
    # A historical full graph is rejected, not returned or silently migrated.
    with sqlite3.connect(store.db_path) as db:
        db.execute("UPDATE prepared_configs SET config_json = ?", (json.dumps(full_graph),))
    with pytest.raises(WorkspaceStoreError, match="metadata is malformed"):
        WorkspaceStore(tmp_path).list_prepared_jobs(project.project_id)
    with sqlite3.connect(store.db_path) as db:
        assert json.loads(db.execute("SELECT config_json FROM prepared_configs").fetchone()[0]) == full_graph


@pytest.mark.parametrize("key,value", [
    ("audio_mode", None), ("audio_mode", "private"), ("audio_mode", {}),
    ("reference_names", []), ("reference_names", ["a", "b", "c"]),
    ("reference_names", "a"), ("reference_names", [""]), ("reference_names", [None]),
    ("reference_names", ["/private/tmp/ref"]), ("reference_names", ["../ref"]),
    ("reference_names", [{"secret": "synthetic"}]),
    ("scheduler_steps", True), ("scheduler_steps", "8"), ("scheduler_steps", 8.0),
    ("seed", True), ("seed", "17"), ("seed", 18), ("seed", 17.0),
    ("video_name", ""), ("video_name", "/private/tmp/input.mov"), ("video_name", ".."),
    ("video_name", "dir/file"), ("video_name", "dir\\file"), ("video_name", "bad\0name"),
    ("video_name", []), ("with_audio", 1), ("with_audio", "true"), ("with_audio", None),
])
def test_history_rejects_malformed_selected_fields(tmp_path, key, value):
    store = WorkspaceStore(tmp_path)
    project = store.create_project("Invalid metadata")
    _make_job(tmp_path, "schemajob")
    record = store.record_prepared_job(project.project_id, "schemajob", tmp_path / "jobs" / "schemajob")
    config = dict(record.config, **{key: value})
    with sqlite3.connect(store.db_path) as db:
        db.execute("UPDATE prepared_configs SET config_json = ?", (json.dumps(config),))
    with pytest.raises(WorkspaceStoreError):
        WorkspaceStore(tmp_path).list_prepared_jobs(project.project_id)


@pytest.mark.parametrize("field", ["audio_mode", "reference_names", "scheduler_steps", "seed", "video_name", "with_audio"])
@pytest.mark.parametrize("missing", [False, True])
def test_record_rejects_bad_graph_metadata_before_sql(tmp_path, field, missing):
    store = WorkspaceStore(tmp_path)
    project = store.create_project("Malformed graph")
    _make_job(tmp_path, "invalidjob")
    job_dir = tmp_path / "jobs" / "invalidjob"
    workflow_path = job_dir / "workflow.json"
    graph = json.loads(workflow_path.read_text())
    plan = json.loads(graph["1189"]["inputs"]["plan"])
    target, key = {
        "audio_mode": (plan, "audio_mode"), "reference_names": (plan, "global_ref"),
        "video_name": (plan, "video"), "scheduler_steps": (graph["181"]["inputs"], "steps"),
        "seed": (graph["13"]["inputs"], "noise_seed"), "with_audio": (graph["1177"]["inputs"], "with_audio"),
    }[field]
    if missing:
        del target[key]
    else:
        target[key] = {"synthetic_secret": ["not safe"]}
    graph["1189"]["inputs"]["plan"] = json.dumps(plan)
    workflow_path.write_text(json.dumps(graph))
    with pytest.raises(WorkspaceStoreError):
        store.record_prepared_job(project.project_id, "invalidjob", job_dir)
    with sqlite3.connect(store.db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM prepared_configs").fetchone()[0] == 0
    assert store.list_prepared_jobs(project.project_id) == []


@pytest.mark.parametrize("payload", ["{", "null", "[]", "42", "{}"])
def test_history_rejects_malformed_json_shapes(tmp_path, payload):
    store = WorkspaceStore(tmp_path)
    _make_job(tmp_path, "malformedjob")
    store.record_prepared_job("", "malformedjob", tmp_path / "jobs" / "malformedjob")
    with sqlite3.connect(store.db_path) as db:
        db.execute("UPDATE prepared_configs SET config_json = ?", (payload,))
    with pytest.raises(WorkspaceStoreError):
        WorkspaceStore(tmp_path).list_prepared_jobs("")


def test_history_projects_extras_and_rejects_each_missing_field(tmp_path):
    store = WorkspaceStore(tmp_path)
    _make_job(tmp_path, "historyjob")
    record = store.record_prepared_job("", "historyjob", tmp_path / "jobs" / "historyjob")
    extended = dict(record.config, arbitrary={"secret": ["SYNTHETIC_SECRET"]})
    with sqlite3.connect(store.db_path) as db:
        db.execute("UPDATE prepared_configs SET config_json = ?", (json.dumps(extended),))
    assert WorkspaceStore(tmp_path).list_prepared_jobs("") == [record]
    for field in record.config:
        incomplete = {key: value for key, value in record.config.items() if key != field}
        with sqlite3.connect(store.db_path) as db:
            db.execute("UPDATE prepared_configs SET config_json = ?", (json.dumps(incomplete),))
        with pytest.raises(WorkspaceStoreError):
            WorkspaceStore(tmp_path).list_prepared_jobs("")
