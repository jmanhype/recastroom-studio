# SPDX-License-Identifier: MIT
"""Persistent, path-safe workspace records for the connected M0 studio.

Records returned by this module are frozen dataclasses.  List and mapping
fields are freshly decoded on every read, but callers must still treat those
nested values as immutable.  ``AssetRecord`` is the only public asset
projection; ``ResolvedAsset.path`` is for server-side file access and must not
be serialized by API code.

The empty string is a reserved legacy project ID for existing jobs that predate
connected projects.  Character identity is stable for the same case/space-normalized
display name; each creation appends the next immutable version.  All IDs are
validated before SQL use, and files must resolve as regular files beneath
``uploads`` or ``imports`` without symlinked path components.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import fcntl
import json
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any, BinaryIO, Iterator
import uuid

from .m1_types import (
    AudioPolicy, EditItem, EditRevision, ExportRecord,
    AttemptEvent, AttemptRecord, AttemptState, ExecutionMode, Fence, Receipt,
    BoundSubmission, OutputEvidence,
    RecipePin,
    ReplayReceipt, ReviewRecord, ReviewVerdict,
    SelectionRecord,
    ResolvedOperation,
    SceneRevision,
    ShotSpec,
    SourceTiming,
    TakeRecord,
    Timebase,
    WindowMap,
    dto_json,
)
from .pipeline import _effective_workflow


class WorkspaceStoreError(Exception):
    """Deliberate workspace-store failure."""
class NotFoundError(WorkspaceStoreError):
    """Requested workspace record does not exist."""
class ValidationError(WorkspaceStoreError):
    """Input values or record state are invalid."""
class AttemptConflictError(WorkspaceStoreError):
    """Authorization or durable worker fence conflicts with current state."""
class UnsafePathError(WorkspaceStoreError):
    """Path is outside a configured boundary or uses a symlink."""
class AssetIntegrityError(WorkspaceStoreError):
    """Recorded bytes do not match their protected fingerprint."""
@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    name: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AssetRecord:
    asset_id: str
    project_id: str
    role: str
    filename: str
    media_type: str | None
    size_bytes: int
    sha256: str
    protected: bool
    created_at: str


@dataclass(frozen=True)
class CharacterVersionRecord:
    character_id: str
    version: int
    name: str
    description: str
    reference_asset_ids: list[str]
    created_at: str


@dataclass(frozen=True)
class PreparedConfigRecord:
    project_id: str
    job_id: str
    character_id: str | None
    character_version: int | None
    seed: int
    workflow_sha256: str
    prompt_sha256: str
    source_sha256: str | None
    reference_sha256s: list[str]
    config: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class ResolvedAsset:
    record: AssetRecord
    path: Path
_ASSET_OR_PROJECT_ID = re.compile(r"[0-9a-f]{32}\Z")
_CHARACTER_ID = re.compile(r"char_[0-9a-f]{24}\Z")
_EXTERNAL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
_LEGACY_PROJECT_ID = ""
def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open(mode="rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _text(value: object, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValidationError(f"{label} must be non-empty text of at most {maximum} characters")
    return value


def _m1_window_valid(value: object) -> int:
    """Private SQLite adapter for the frozen canonical WindowMap parser."""
    if not isinstance(value, str):
        return 0
    try:
        window = WindowMap.from_json(value)
        valid_bounds = (
            window.decoder_keep.start >= 0
            and window.decoder_keep.end <= window.expected_decoder_frames
        )
        return int(valid_bounds and value == window.to_json())
    except (TypeError, ValueError, json.JSONDecodeError):
        return 0


@dataclass(frozen=True)
class _AssetFile:
    root_kind: str; relative_path: str; resolved_path: Path; sha256: str; size_bytes: int


_M1_MIGRATION_STATEMENTS = (
    """CREATE TABLE scene_revisions (
        scene_revision_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        source_asset_id TEXT NOT NULL REFERENCES assets(asset_id),
        source_sha256 TEXT NOT NULL, frame_count INTEGER NOT NULL CHECK (frame_count > 0),
        timebase_num INTEGER NOT NULL CHECK (timebase_num > 0),
        timebase_den INTEGER NOT NULL CHECK (timebase_den > 0),
        cfr INTEGER NOT NULL CHECK (cfr = 1), has_audio INTEGER NOT NULL,
        revision INTEGER NOT NULL CHECK (revision > 0), created_at TEXT NOT NULL,
        UNIQUE (project_id, revision), UNIQUE (project_id, source_asset_id, revision))""",
    """CREATE TABLE shots (
        scene_revision_id TEXT NOT NULL REFERENCES scene_revisions(scene_revision_id),
        shot_id TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
        start_frame INTEGER NOT NULL CHECK (start_frame >= 0),
        end_frame INTEGER NOT NULL CHECK (end_frame > start_frame),
        kind TEXT NOT NULL CHECK (kind IN ('render', 'pass_through')),
        PRIMARY KEY (scene_revision_id, shot_id), UNIQUE (scene_revision_id, ordinal))""",
    """CREATE TABLE operations (
        operation_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        scene_revision_id TEXT NOT NULL REFERENCES scene_revisions(scene_revision_id),
        shot_id TEXT NOT NULL, window_json TEXT NOT NULL, pin_json TEXT NOT NULL,
        character_id TEXT, character_version INTEGER, seed INTEGER NOT NULL,
        canonical_json TEXT NOT NULL, fingerprint TEXT NOT NULL,
        managed_job_id TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
        UNIQUE (scene_revision_id, shot_id, managed_job_id),
        CHECK ((character_id IS NULL) = (character_version IS NULL)))""",
    """CREATE TABLE attempts (
        attempt_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        operation_id TEXT NOT NULL REFERENCES operations(operation_id),
        client_request_id TEXT NOT NULL, mode TEXT NOT NULL
          CHECK (mode IN ('dry_run', 'retained_replay', 'comfy', 'sdk')),
        challenger_of TEXT, state TEXT NOT NULL
          CHECK (state IN ('prepared', 'ready', 'submitting', 'submitted', 'running',
                           'downloading', 'completed', 'failed', 'reconcile_needed',
                           'cancel_requested', 'provider_confirmed_cancelled')),
        provider_id TEXT, revision INTEGER NOT NULL CHECK (revision > 0),
        created_at TEXT NOT NULL, UNIQUE (project_id, client_request_id))""",
    """CREATE TABLE attempt_events (
        event_id TEXT PRIMARY KEY,
        attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
        sequence INTEGER NOT NULL CHECK (sequence >= 0), kind TEXT NOT NULL,
        payload_json TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE (attempt_id, sequence))""",
    """CREATE TABLE provider_receipts (
        attempt_id TEXT PRIMARY KEY REFERENCES attempts(attempt_id),
        provider_id TEXT NOT NULL, request_key TEXT NOT NULL,
        adapter_version TEXT NOT NULL, endpoint_fingerprint TEXT NOT NULL,
        receipt_asset_id TEXT NOT NULL REFERENCES assets(asset_id),
        receipt_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL,
        UNIQUE (provider_id, request_key))""",
    """CREATE TABLE takes (
        take_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        shot_id TEXT NOT NULL, attempt_id TEXT REFERENCES attempts(attempt_id),
        operation_id TEXT REFERENCES operations(operation_id),
        output_asset_id TEXT NOT NULL REFERENCES assets(asset_id),
        output_sha256 TEXT NOT NULL, frame_count INTEGER NOT NULL CHECK (frame_count > 0),
        timebase_num INTEGER NOT NULL CHECK (timebase_num > 0),
        timebase_den INTEGER NOT NULL CHECK (timebase_den > 0),
        origin TEXT NOT NULL CHECK (origin IN ('dry_run', 'retained_replay', 'provider')),
        qualified INTEGER NOT NULL, created_at TEXT NOT NULL,
        UNIQUE (project_id, output_asset_id), UNIQUE (attempt_id, output_asset_id))""",
    """CREATE TABLE reviews (
        review_id TEXT PRIMARY KEY,
        take_id TEXT NOT NULL REFERENCES takes(take_id),
        verdict TEXT NOT NULL CHECK (verdict IN ('keeper', 'reject', 'needs_review')),
        note TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE (take_id, review_id))""",
    """CREATE TABLE selection_events (
        selection_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        shot_id TEXT NOT NULL, take_id TEXT REFERENCES takes(take_id),
        revision INTEGER NOT NULL CHECK (revision > 0), created_at TEXT NOT NULL,
        UNIQUE (project_id, shot_id, revision))""",
    """CREATE TABLE edit_revisions (
        edit_revision_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        scene_revision_id TEXT NOT NULL REFERENCES scene_revisions(scene_revision_id),
        items_json TEXT NOT NULL, audio TEXT NOT NULL
          CHECK (audio IN ('source_edit_map', 'mute', 'source_stream_copy')),
        timebase_num INTEGER NOT NULL CHECK (timebase_num > 0),
        timebase_den INTEGER NOT NULL CHECK (timebase_den > 0), created_at TEXT NOT NULL,
        UNIQUE (project_id, edit_revision_id))""",
    """CREATE TABLE exports (
        export_id TEXT PRIMARY KEY,
        edit_revision_id TEXT NOT NULL REFERENCES edit_revisions(edit_revision_id),
        state TEXT NOT NULL CHECK (state IN ('completed', 'failed')),
        asset_id TEXT REFERENCES assets(asset_id), sha256 TEXT,
        checks_json TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE (edit_revision_id, export_id))""",
    """CREATE TABLE worker_epochs (
        epoch INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL, acquired_at TEXT NOT NULL,
        released_at TEXT, CHECK (released_at IS NULL OR released_at >= acquired_at))""",
    "CREATE INDEX scene_revisions_project_idx ON scene_revisions(project_id, revision DESC)",
    "CREATE INDEX attempts_project_idx ON attempts(project_id, created_at DESC)",
    "CREATE INDEX takes_project_shot_idx ON takes(project_id, shot_id, created_at DESC)",
)


_SCOPED_TAKES_SQL = """CREATE TABLE takes_v2 (
    take_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
    scene_revision_id TEXT, shot_id TEXT NOT NULL,
    attempt_id TEXT REFERENCES attempts(attempt_id),
    operation_id TEXT REFERENCES operations(operation_id),
    output_asset_id TEXT NOT NULL REFERENCES assets(asset_id), output_sha256 TEXT NOT NULL,
    frame_count INTEGER NOT NULL CHECK (frame_count > 0),
    timebase_num INTEGER NOT NULL CHECK (timebase_num > 0),
    timebase_den INTEGER NOT NULL CHECK (timebase_den > 0),
    origin TEXT NOT NULL CHECK (origin IN ('dry_run', 'retained_replay', 'provider')),
    qualified INTEGER NOT NULL CHECK (qualified IN (0, 1)), created_at TEXT NOT NULL,
    CHECK (scene_revision_id IS NOT NULL OR
           (qualified = 0 AND operation_id IS NULL AND attempt_id IS NULL
            AND origin = 'retained_replay')),
    FOREIGN KEY (scene_revision_id, shot_id) REFERENCES shots(scene_revision_id, shot_id),
    FOREIGN KEY (scene_revision_id, project_id) REFERENCES scene_revisions(scene_revision_id, project_id),
    FOREIGN KEY (project_id, output_asset_id) REFERENCES assets(project_id, asset_id),
    UNIQUE (project_id, output_asset_id), UNIQUE (attempt_id, output_asset_id),
    UNIQUE (project_id, scene_revision_id, shot_id, take_id))"""

_SCOPED_SELECTIONS_SQL = """CREATE TABLE selection_events (
    selection_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
    scene_revision_id TEXT NOT NULL, shot_id TEXT NOT NULL,
    take_id TEXT REFERENCES takes(take_id), revision INTEGER NOT NULL CHECK (revision > 0),
    created_at TEXT NOT NULL,
    FOREIGN KEY (scene_revision_id, shot_id) REFERENCES shots(scene_revision_id, shot_id),
    FOREIGN KEY (scene_revision_id, project_id) REFERENCES scene_revisions(scene_revision_id, project_id),
    FOREIGN KEY (project_id, scene_revision_id, shot_id, take_id)
      REFERENCES takes(project_id, scene_revision_id, shot_id, take_id),
    UNIQUE (project_id, scene_revision_id, shot_id, revision))"""


_PREPARATION_BINDINGS_SQL = """CREATE TABLE IF NOT EXISTS preparation_bindings (
    operation_id TEXT PRIMARY KEY REFERENCES operations(operation_id),
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    binding_asset_id TEXT NOT NULL REFERENCES assets(asset_id),
    binding_sha256 TEXT NOT NULL, operation_fingerprint TEXT NOT NULL,
    graph_asset_id TEXT NOT NULL REFERENCES assets(asset_id), graph_sha256 TEXT NOT NULL,
    source_asset_id TEXT NOT NULL REFERENCES assets(asset_id), source_sha256 TEXT NOT NULL,
    reference_asset_ids_json TEXT NOT NULL, reference_sha256s_json TEXT NOT NULL,
    cpu_input_asset_id TEXT REFERENCES assets(asset_id), cpu_input_sha256 TEXT NOT NULL,
    substitutions_json TEXT NOT NULL, prompt_sha256 TEXT NOT NULL,
    word_schedule_sha256 TEXT NOT NULL, adapter_version TEXT NOT NULL,
    endpoint_fingerprint TEXT NOT NULL, created_at TEXT NOT NULL,
    UNIQUE (project_id, binding_asset_id))"""


_PREPARATION_BINDING_UPDATE_TRIGGER = """CREATE TRIGGER IF NOT EXISTS preparation_binding_immutable_update
    BEFORE UPDATE ON preparation_bindings BEGIN
    SELECT RAISE(ABORT, 'preparation binding is immutable'); END"""
_PREPARATION_BINDING_DELETE_TRIGGER = """CREATE TRIGGER IF NOT EXISTS preparation_binding_immutable_delete
    BEFORE DELETE ON preparation_bindings BEGIN
    SELECT RAISE(ABORT, 'preparation binding is immutable'); END"""


_QUALIFIED_REPLAY_RECEIPTS_SQL = """CREATE TABLE qualified_replay_receipts (
    take_id TEXT PRIMARY KEY REFERENCES takes(take_id),
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    scene_revision_id TEXT NOT NULL, shot_id TEXT NOT NULL,
    source_sha256 TEXT NOT NULL, input_sha256 TEXT NOT NULL,
    recipe_id TEXT NOT NULL, recipe_version TEXT NOT NULL,
    raw_graph_sha256 TEXT NOT NULL, resolved_graph_sha256 TEXT NOT NULL,
    output_sha256 TEXT NOT NULL, window_json TEXT NOT NULL,
    historical_verdict TEXT CHECK (historical_verdict IS NULL
      OR historical_verdict IN ('keeper', 'reject', 'needs_review')),
    operation_id TEXT REFERENCES operations(operation_id), created_at TEXT NOT NULL,
    FOREIGN KEY (scene_revision_id, shot_id) REFERENCES shots(scene_revision_id, shot_id),
    FOREIGN KEY (scene_revision_id, project_id) REFERENCES scene_revisions(scene_revision_id, project_id),
    FOREIGN KEY (project_id, scene_revision_id, shot_id, take_id)
      REFERENCES takes(project_id, scene_revision_id, shot_id, take_id))"""

_UNQUALIFIED_IMPORT_EVIDENCE_SQL = """CREATE TABLE unqualified_import_evidence (
    take_id TEXT PRIMARY KEY REFERENCES takes(take_id),
    project_id TEXT NOT NULL REFERENCES projects(project_id), shot_id TEXT NOT NULL,
    imported_content_sha256 TEXT NOT NULL, marker_json TEXT NOT NULL,
    marker_sha256 TEXT NOT NULL, created_at TEXT NOT NULL)"""

_UNQUALIFIED_MARKER = (
    '{"historical_metadata_state":"absent","import_contract_version":1}'
)
_UNQUALIFIED_MARKER_SHA256 = hashlib.sha256(_UNQUALIFIED_MARKER.encode("utf-8")).hexdigest()
_V4_REVERSE_TRIGGERS = (
    "takes_v4_qualified_receipt_parent_immutable",
    "takes_v4_unqualified_evidence_parent_immutable",
    "takes_v4_qualified_receipt_parent_delete",
    "takes_v4_unqualified_evidence_parent_delete",
    "operations_v4_qualified_receipt_parent_immutable",
    "operations_v4_qualified_receipt_parent_delete",
    "scene_revisions_v4_qualified_receipt_parent_immutable",
    "scene_revisions_v4_qualified_receipt_parent_delete",
    "shots_v4_qualified_receipt_parent_immutable",
    "shots_v4_qualified_receipt_parent_delete",
    "assets_v4_qualified_receipt_parent_immutable",
    "assets_v4_unqualified_evidence_parent_immutable",
    "assets_v4_qualified_receipt_parent_delete",
    "assets_v4_unqualified_evidence_parent_delete",
)
_TAKE_PARENT_FIELDS = (
    "take_id", "project_id", "scene_revision_id", "shot_id", "attempt_id",
    "operation_id", "output_asset_id", "output_sha256", "frame_count",
    "timebase_num", "timebase_den", "origin", "qualified", "created_at",
)
_OPERATION_PARENT_FIELDS = (
    "operation_id", "project_id", "scene_revision_id", "shot_id", "window_json",
    "pin_json", "character_id", "character_version", "seed", "canonical_json",
    "fingerprint", "managed_job_id", "created_at",
)
_SCENE_PARENT_FIELDS = (
    "scene_revision_id", "project_id", "source_asset_id", "source_sha256",
    "frame_count", "timebase_num", "timebase_den", "cfr", "has_audio",
    "revision", "created_at",
)
_SHOT_PARENT_FIELDS = (
    "scene_revision_id", "shot_id", "ordinal", "start_frame", "end_frame",
    "kind",
)
_ASSET_PARENT_FIELDS = (
    "asset_id", "project_id", "role", "filename", "media_type", "size_bytes",
    "sha256", "protected", "created_at", "root_kind", "relative_path",
)


def _parent_changed(fields: tuple[str, ...]) -> str:
    return " OR ".join(f"NEW.{field} IS NOT OLD.{field}" for field in fields)




def _evidence_triggers(db: sqlite3.Connection) -> None:
    """Install the fail-closed v4 private-carrier invariants."""
    take_changed = _parent_changed(_TAKE_PARENT_FIELDS)
    operation_changed = _parent_changed(_OPERATION_PARENT_FIELDS)
    scene_changed = _parent_changed(_SCENE_PARENT_FIELDS)
    shot_changed = _parent_changed(_SHOT_PARENT_FIELDS)
    asset_changed = _parent_changed(_ASSET_PARENT_FIELDS)
    db.execute(_QUALIFIED_REPLAY_RECEIPTS_SQL)
    db.execute(_UNQUALIFIED_IMPORT_EVIDENCE_SQL)
    carriers = {
        "qualified_replay_receipts": "qualified_replay_receipt",
        "unqualified_import_evidence": "unqualified_import_evidence",
    }
    for table, label in carriers.items():
        db.execute(f"""CREATE TRIGGER {table}_v4_duplicate_insert BEFORE INSERT ON {table}
            WHEN EXISTS (SELECT 1 FROM {table} WHERE take_id = NEW.take_id)
            BEGIN SELECT RAISE(ABORT, '{label} is append-once'); END""")
        for action in ("UPDATE", "DELETE"):
            db.execute(f"""CREATE TRIGGER {table}_v4_immutable_{action.lower()}
                BEFORE {action} ON {table}
                BEGIN SELECT RAISE(ABORT, '{label} is immutable'); END""")

    db.execute(f"""CREATE TRIGGER qualified_replay_receipts_v4_scope_insert
        BEFORE INSERT ON qualified_replay_receipts WHEN NOT EXISTS (
          SELECT 1 FROM takes t WHERE t.take_id = NEW.take_id AND t.project_id = NEW.project_id
            AND t.scene_revision_id = NEW.scene_revision_id AND t.shot_id = NEW.shot_id
            AND t.attempt_id IS NULL AND t.operation_id IS NEW.operation_id
            AND t.output_sha256 = NEW.output_sha256 AND t.origin = 'retained_replay'
            AND t.qualified = 1)
          OR NEW.operation_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM operations o WHERE o.operation_id = NEW.operation_id
              AND o.project_id = NEW.project_id AND o.scene_revision_id = NEW.scene_revision_id
              AND o.shot_id = NEW.shot_id)
          OR EXISTS (SELECT 1 FROM unqualified_import_evidence WHERE take_id = NEW.take_id)
          OR json_valid(NEW.window_json) = 0
          OR m1_window_valid(NEW.window_json) = 0
          OR NEW.historical_verdict NOT IN (NULL, 'keeper', 'reject', 'needs_review')
          OR NOT (length(NEW.source_sha256) = 64 AND length(NEW.input_sha256) = 64
                  AND length(NEW.raw_graph_sha256) = 64 AND length(NEW.resolved_graph_sha256) = 64
                  AND length(NEW.output_sha256) = 64
                  AND NEW.source_sha256 NOT GLOB '*[^0-9a-f]*'
                  AND NEW.input_sha256 NOT GLOB '*[^0-9a-f]*'
                  AND NEW.raw_graph_sha256 NOT GLOB '*[^0-9a-f]*'
                  AND NEW.resolved_graph_sha256 NOT GLOB '*[^0-9a-f]*'
                  AND NEW.output_sha256 NOT GLOB '*[^0-9a-f]*')
        BEGIN SELECT RAISE(ABORT, 'qualified replay receipt scope is invalid'); END""")
    db.execute("""CREATE TRIGGER unqualified_import_evidence_v4_scope_insert
        BEFORE INSERT ON unqualified_import_evidence WHEN NOT EXISTS (
          SELECT 1 FROM takes t WHERE t.take_id = NEW.take_id AND t.project_id = NEW.project_id
            AND t.scene_revision_id IS NULL AND t.shot_id = NEW.shot_id
            AND t.attempt_id IS NULL AND t.operation_id IS NULL
            AND t.output_sha256 = NEW.imported_content_sha256
            AND t.origin = 'retained_replay' AND t.qualified = 0)
          OR EXISTS (SELECT 1 FROM qualified_replay_receipts WHERE take_id = NEW.take_id)
          OR NEW.marker_json != '{"historical_metadata_state":"absent","import_contract_version":1}'
          OR NEW.marker_sha256 != '5bb4de2fde14152f8197333d12f2ca4fd2f66a9e6869e9d5aad0e43dbd245005'
          OR length(NEW.imported_content_sha256) != 64
          OR NEW.imported_content_sha256 GLOB '*[^0-9a-f]*'
        BEGIN SELECT RAISE(ABORT, 'unqualified import evidence scope is invalid'); END""")

    db.execute(f"""CREATE TRIGGER takes_v4_qualified_receipt_parent_immutable
        BEFORE UPDATE ON takes WHEN EXISTS (
          SELECT 1 FROM qualified_replay_receipts e WHERE e.take_id = OLD.take_id)
          AND ({take_changed})
        BEGIN SELECT RAISE(ABORT, 'qualified replay take is immutable'); END""")
    db.execute(f"""CREATE TRIGGER takes_v4_unqualified_evidence_parent_immutable
        BEFORE UPDATE ON takes WHEN EXISTS (
          SELECT 1 FROM unqualified_import_evidence e WHERE e.take_id = OLD.take_id)
          AND ({take_changed})
        BEGIN SELECT RAISE(ABORT, 'unqualified import take is immutable'); END""")
    db.execute("""CREATE TRIGGER takes_v4_qualified_receipt_parent_delete BEFORE DELETE ON takes
        WHEN EXISTS (SELECT 1 FROM qualified_replay_receipts WHERE take_id = OLD.take_id)
        BEGIN SELECT RAISE(ABORT, 'qualified replay receipt parent is immutable'); END""")
    db.execute("""CREATE TRIGGER takes_v4_unqualified_evidence_parent_delete BEFORE DELETE ON takes
        WHEN EXISTS (SELECT 1 FROM unqualified_import_evidence WHERE take_id = OLD.take_id)
        BEGIN SELECT RAISE(ABORT, 'unqualified import evidence parent is immutable'); END""")
    db.execute(f"""CREATE TRIGGER operations_v4_qualified_receipt_parent_immutable
        BEFORE UPDATE ON operations WHEN EXISTS (
          SELECT 1 FROM qualified_replay_receipts e WHERE e.operation_id = OLD.operation_id)
          AND ({operation_changed})
        BEGIN SELECT RAISE(ABORT, 'replay operation is immutable'); END""")
    db.execute("""CREATE TRIGGER operations_v4_qualified_receipt_parent_delete
        BEFORE DELETE ON operations WHEN EXISTS (
          SELECT 1 FROM qualified_replay_receipts e WHERE e.operation_id = OLD.operation_id)
        BEGIN SELECT RAISE(ABORT, 'replay operation cannot be deleted'); END""")
    db.execute(f"""CREATE TRIGGER scene_revisions_v4_qualified_receipt_parent_immutable
        BEFORE UPDATE ON scene_revisions
          WHEN EXISTS (SELECT 1 FROM qualified_replay_receipts e
            WHERE e.scene_revision_id = OLD.scene_revision_id)
          AND ({scene_changed})
        BEGIN SELECT RAISE(ABORT, 'replay scene is immutable'); END""")
    db.execute("""CREATE TRIGGER scene_revisions_v4_qualified_receipt_parent_delete
        BEFORE DELETE ON scene_revisions WHEN EXISTS (
          SELECT 1 FROM qualified_replay_receipts e WHERE e.scene_revision_id = OLD.scene_revision_id)
        BEGIN SELECT RAISE(ABORT, 'replay scene cannot be deleted'); END""")
    db.execute(f"""CREATE TRIGGER shots_v4_qualified_receipt_parent_immutable
        BEFORE UPDATE ON shots
        WHEN EXISTS (SELECT 1 FROM qualified_replay_receipts e
          WHERE e.scene_revision_id = OLD.scene_revision_id AND e.shot_id = OLD.shot_id)
          AND ({shot_changed})
        BEGIN SELECT RAISE(ABORT, 'replay shot is immutable'); END""")
    db.execute("""CREATE TRIGGER shots_v4_qualified_receipt_parent_delete
        BEFORE DELETE ON shots WHEN EXISTS (
          SELECT 1 FROM qualified_replay_receipts e
          WHERE e.scene_revision_id = OLD.scene_revision_id AND e.shot_id = OLD.shot_id)
        BEGIN SELECT RAISE(ABORT, 'replay shot cannot be deleted'); END""")
    db.execute(f"""CREATE TRIGGER assets_v4_qualified_receipt_parent_immutable
        BEFORE UPDATE ON assets WHEN EXISTS (
          SELECT 1 FROM qualified_replay_receipts e JOIN takes t USING(take_id)
          WHERE t.output_asset_id = OLD.asset_id
          AND ({asset_changed}))
        BEGIN SELECT RAISE(ABORT, 'replay output asset is immutable'); END""")
    db.execute(f"""CREATE TRIGGER assets_v4_unqualified_evidence_parent_immutable
        BEFORE UPDATE ON assets WHEN EXISTS (
          SELECT 1 FROM unqualified_import_evidence e JOIN takes t USING(take_id)
          WHERE t.output_asset_id = OLD.asset_id
          AND ({asset_changed}))
        BEGIN SELECT RAISE(ABORT, 'unqualified output asset is immutable'); END""")
    db.execute("""CREATE TRIGGER assets_v4_qualified_receipt_parent_delete BEFORE DELETE ON assets
        WHEN EXISTS (SELECT 1 FROM qualified_replay_receipts e JOIN takes t USING(take_id)
          WHERE t.output_asset_id = OLD.asset_id)
        BEGIN SELECT RAISE(ABORT, 'qualified replay output asset cannot be deleted'); END""")
    db.execute("""CREATE TRIGGER assets_v4_unqualified_evidence_parent_delete BEFORE DELETE ON assets
        WHEN EXISTS (SELECT 1 FROM unqualified_import_evidence e JOIN takes t USING(take_id)
          WHERE t.output_asset_id = OLD.asset_id)
        BEGIN SELECT RAISE(ABORT, 'unqualified output asset cannot be deleted'); END""")


def _take_lineage_valid(db: sqlite3.Connection, take: dict[str, Any], scene: str | None) -> bool:
    """Verify both nullable lineage references, including attempt-only history."""
    operation_ids = [take["operation_id"]] if take["operation_id"] is not None else []
    if take["attempt_id"] is not None:
        attempt = db.execute("SELECT * FROM attempts WHERE attempt_id = ?", (take["attempt_id"],)).fetchone()
        if attempt is None or attempt["project_id"] != take["project_id"]:
            return False
        if operation_ids and attempt["operation_id"] != operation_ids[0]:
            return False
        operation_ids.append(attempt["operation_id"])
    for operation_id in operation_ids:
        operation = db.execute("SELECT * FROM operations WHERE operation_id = ?", (operation_id,)).fetchone()
        if operation is None or (operation["project_id"], operation["scene_revision_id"], operation["shot_id"]) != (
            take["project_id"], scene, take["shot_id"]
        ):
            return False
    return True


def _scope_backfill(db: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    takes = [dict(row) for row in db.execute("SELECT * FROM takes")]
    selections = [dict(row) for row in db.execute("SELECT * FROM selection_events")]
    by_id = {}
    for take in takes:
        operation_id = take["operation_id"]
        if operation_id is None and take["attempt_id"] is not None:
            attempt = db.execute("SELECT operation_id FROM attempts WHERE attempt_id = ?", (take["attempt_id"],)).fetchone()
            operation_id = attempt[0] if attempt else None
        operation = db.execute("SELECT scene_revision_id FROM operations WHERE operation_id = ?", (operation_id,)).fetchone()
        scene = operation[0] if operation else None
        attached = db.execute("""SELECT 1 FROM shots JOIN scene_revisions USING(scene_revision_id)
            WHERE scene_revision_id = ? AND project_id = ? AND shot_id = ?""",
            (scene, take["project_id"], take["shot_id"])).fetchone()
        # v1 has no persisted validated ReplayReceipt field. Never infer one from
        # output filenames, arbitrary event JSON, or a same-named/latest shot.
        unattached = scene is None and not take["qualified"] and take["origin"] == "retained_replay"
        if not _take_lineage_valid(db, take, scene) or not (attached or unattached):
            raise ValidationError(f"scope migration v2: take {take['take_id']} lacks consistent verified lineage; "
                                  "repair authoritative operation/attempt evidence before retrying; database unchanged")
        take["scene_revision_id"] = scene
        by_id[take["take_id"]] = take
    streams: dict[tuple[str, str], set[str]] = {}
    for event in selections:
        take = by_id.get(event["take_id"])
        if (take is None or not take["qualified"] or take["scene_revision_id"] is None
                or (event["project_id"], event["shot_id"]) != (take["project_id"], take["shot_id"])):
            raise ValidationError(f"scope migration v2: selection {event['selection_id']} has NULL or unverified take; "
                                  "recover authoritative scene evidence before retrying; database unchanged")
        event["scene_revision_id"] = take["scene_revision_id"]
        streams.setdefault((event["project_id"], event["shot_id"]), set()).add(take["scene_revision_id"])
    if any(len(scenes) != 1 for scenes in streams.values()):
        raise ValidationError("scope migration v2: legacy selection stream spans scenes; "
                              "resolve ambiguous history from authoritative evidence; database unchanged")
    return takes, selections


def _insert_rows(db: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        db.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))


def _scope_triggers(db: sqlite3.Connection) -> None:
    # These are storage invariants, not the future TakeService selection/CAS API.
    lineage = """(NEW.operation_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM operations o WHERE o.operation_id = NEW.operation_id
        AND o.project_id = NEW.project_id AND o.scene_revision_id = NEW.scene_revision_id
        AND o.shot_id = NEW.shot_id)) OR (NEW.attempt_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM attempts a JOIN operations o USING(operation_id)
        WHERE a.attempt_id = NEW.attempt_id AND a.project_id = NEW.project_id
        AND o.project_id = NEW.project_id AND o.scene_revision_id = NEW.scene_revision_id
        AND o.shot_id = NEW.shot_id AND (NEW.operation_id IS NULL OR o.operation_id = NEW.operation_id)))"""
    for action in ("INSERT", "UPDATE"):
        db.execute(f"""CREATE TRIGGER takes_scope_{action.lower()} BEFORE {action} ON takes
            WHEN {lineage} BEGIN SELECT RAISE(ABORT, 'take lineage scope mismatch'); END""")
        db.execute(f"""CREATE TRIGGER selection_qualified_{action.lower()} BEFORE {action} ON selection_events
            WHEN NEW.take_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM takes WHERE take_id = NEW.take_id AND qualified = 1)
            BEGIN SELECT RAISE(ABORT, 'selection requires qualified scoped take'); END""")
    db.execute("""CREATE TRIGGER selected_take_qualification BEFORE UPDATE OF qualified ON takes
        WHEN NEW.qualified != 1 AND EXISTS (SELECT 1 FROM selection_events WHERE take_id = OLD.take_id)
        BEGIN SELECT RAISE(ABORT, 'historically selected take must remain qualified'); END""")
    db.execute("""CREATE TRIGGER referenced_operation_scope BEFORE UPDATE OF operation_id, project_id,
        scene_revision_id, shot_id ON operations WHEN EXISTS (SELECT 1 FROM takes t
        LEFT JOIN attempts a ON a.attempt_id = t.attempt_id
        WHERE t.operation_id = OLD.operation_id OR a.operation_id = OLD.operation_id)
        BEGIN SELECT RAISE(ABORT, 'referenced operation scope is immutable'); END""")
    db.execute("""CREATE TRIGGER referenced_attempt_scope BEFORE UPDATE OF attempt_id, project_id, operation_id
        ON attempts WHEN EXISTS (SELECT 1 FROM takes WHERE attempt_id = OLD.attempt_id)
        BEGIN SELECT RAISE(ABORT, 'referenced attempt scope is immutable'); END""")


def _migrate_scope(db: sqlite3.Connection) -> None:
    takes, selections = _scope_backfill(db)
    reviews = [dict(row) for row in db.execute("SELECT * FROM reviews")]
    for table, columns in (("scene_revisions", "scene_revision_id,project_id"), ("assets", "project_id,asset_id")):
        db.execute(f"CREATE UNIQUE INDEX {table}_scope_key ON {table}({columns})")
    db.execute(_SCOPED_TAKES_SQL)
    _insert_rows(db, "takes_v2", takes)
    # Rebuild inbound children too: foreign_keys stays ON throughout. No rename
    # of the old parent that would silently retarget their REFERENCES clauses.
    db.execute("DROP TABLE selection_events")
    db.execute("DROP TABLE reviews")
    db.execute("DROP TABLE takes")
    db.execute("ALTER TABLE takes_v2 RENAME TO takes")
    db.execute(_M1_MIGRATION_STATEMENTS[7])  # unchanged reviews schema
    db.execute(_SCOPED_SELECTIONS_SQL)
    _scope_triggers(db)
    _insert_rows(db, "reviews", reviews)
    _insert_rows(db, "selection_events", selections)
    db.execute("CREATE INDEX takes_project_shot_idx ON takes(project_id,scene_revision_id,shot_id,created_at DESC)")
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValidationError("scope migration v2: foreign key integrity failure; repair legacy references; database unchanged")


class WorkspaceStore:
    """SQLite-backed project, asset, identity, and prepared-job history."""

    def __init__(self, root: Path) -> None:
        if not isinstance(root, Path):
            raise ValidationError("workspace root must be a Path")
        root.mkdir(parents=True, exist_ok=True)
        self._caller_root = root.absolute()
        self.root = root.resolve(strict=True)
        self.uploads_root = self.root / "uploads"
        self.imports_root = self.root / "imports"
        self.db_path = self.root / "workspace.sqlite3"
        for configured_root in (self.uploads_root, self.imports_root):
            configured_root.mkdir(exist_ok=True)
            if configured_root.is_symlink() or not configured_root.is_dir():
                raise UnsafePathError("configured asset root is not a safe directory")
        self._initialize()
        self._worker_identity = None

    @staticmethod
    def _attempt(row: sqlite3.Row) -> AttemptRecord:
        return AttemptRecord(row["attempt_id"], row["project_id"], row["operation_id"],
            row["client_request_id"], ExecutionMode(row["mode"]), row["challenger_of"],
            AttemptState(row["state"]), row["provider_id"], row["revision"])

    def _lookup_attempt(self, attempt_id: str) -> AttemptRecord:
        self._validate_id(attempt_id, "attempt", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
        if row is None:
            raise NotFoundError("attempt not found")
        return self._attempt(row)

    def get_attempt(self, project_id: str, attempt_id: str) -> AttemptRecord:
        self.get_project(project_id)
        attempt = self._lookup_attempt(attempt_id)
        if attempt.project_id != project_id:
            raise NotFoundError("attempt not found")
        return attempt

    def list_attempts(self, project_id: str) -> list[AttemptRecord]:
        self.get_project(project_id)
        with self._connect() as db:
            return [self._attempt(row) for row in db.execute(
                "SELECT * FROM attempts WHERE project_id=? ORDER BY created_at,attempt_id", (project_id,))]

    def authorize_attempt(self, op: ResolvedOperation, client_request_id: str,
                          mode: ExecutionMode, challenger_of: str | None) -> AttemptRecord:
        return self._authorize_attempt(op, client_request_id, mode, challenger_of)[0]

    def _authorize_attempt(self, op: ResolvedOperation, client_request_id: str,
                           mode: ExecutionMode, challenger_of: str | None) -> tuple[AttemptRecord, bool]:
        self._validate_id(client_request_id, "request", _EXTERNAL_ID)
        if not isinstance(mode, ExecutionMode) or self.get_operation(op.project_id, op.id) != op:
            raise ValidationError("invalid authorization")
        if challenger_of is not None:
            self.get_attempt(op.project_id, challenger_of)
        with self._transaction() as db:
            row = db.execute("SELECT * FROM attempts WHERE project_id=? AND client_request_id=?",
                             (op.project_id, client_request_id)).fetchone()
            if row:
                if (row["operation_id"], row["mode"], row["challenger_of"]) != (op.id, mode.value, challenger_of):
                    raise AttemptConflictError("REQUEST_KEY_CONFLICT")
                return self._attempt(row), False
            attempt = AttemptRecord("attempt-" + uuid.uuid4().hex, op.project_id, op.id,
                client_request_id, mode, challenger_of, AttemptState.PREPARED, None, 1)
            db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)", (
                attempt.id, op.project_id, op.id, client_request_id, mode.value, challenger_of,
                attempt.state.value, None, 1, _timestamp()))
            return attempt, True

    @contextmanager
    def worker_lock(self, owner_id: str) -> Iterator[int]:
        """Nonblocking lifetime flock; hold this context across ALL adapter calls.

        Epochs are durable history, never timed leases. Inherited objects cannot
        write after fork and another thread cannot borrow a worker's fence.
        """
        self._validate_id(owner_id, "owner", _EXTERNAL_ID)
        if self._worker_identity is not None:
            raise AttemptConflictError("WORKER_BUSY")
        fd = os.open(self.root / "worker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        locked = False
        epoch = None
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except BlockingIOError as error:
                raise AttemptConflictError("WORKER_BUSY") from error
            with self._transaction() as db:
                epoch = db.execute("INSERT INTO worker_epochs(owner_id,acquired_at) VALUES (?,?)",
                                   (owner_id, _timestamp())).lastrowid
            self._worker_identity = (owner_id, epoch, os.getpid(), threading.get_ident())
            yield epoch
        finally:
            try:
                if locked:
                    self._worker_identity = None
                    if epoch is not None:
                        with self._transaction() as db:
                            db.execute("UPDATE worker_epochs SET released_at=? WHERE epoch=?", (_timestamp(), epoch))
            finally:
                if locked:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)

    @staticmethod
    def _event(db: sqlite3.Connection, attempt_id: str, kind: str, payload: dict[str, Any]) -> None:
        db.execute("INSERT INTO attempt_events VALUES (?,?,?,?,?,?)", (uuid.uuid4().hex,
            attempt_id, db.execute("SELECT COALESCE(MAX(sequence),-1)+1 FROM attempt_events WHERE attempt_id=?",
                                  (attempt_id,)).fetchone()[0],
            kind, json.dumps(payload, sort_keys=True, separators=(",", ":")), _timestamp()))

    def _fenced(self, db: sqlite3.Connection, fence: Fence, expected: AttemptState) -> AttemptRecord:
        if self._worker_identity != (fence.owner_id, fence.epoch, os.getpid(), threading.get_ident()):
            raise AttemptConflictError("STALE_FENCE")
        epoch = db.execute("SELECT * FROM worker_epochs ORDER BY epoch DESC LIMIT 1").fetchone()
        claim = db.execute("SELECT payload_json FROM attempt_events WHERE attempt_id=? AND kind='claimed' "
                           "ORDER BY sequence DESC LIMIT 1", (fence.attempt_id,)).fetchone()
        row = db.execute("SELECT * FROM attempts WHERE attempt_id=?", (fence.attempt_id,)).fetchone()
        if (epoch is None or epoch["epoch"] != fence.epoch or epoch["owner_id"] != fence.owner_id
                or epoch["released_at"] is not None or claim is None
                or json.loads(claim[0]) != {"owner_id": fence.owner_id, "epoch": fence.epoch}
                or row is None or row["state"] != expected.value):
            raise AttemptConflictError("STALE_FENCE_OR_STATE")
        return self._attempt(row)

    def claim_attempt(self, owner_id: str) -> Fence | None:
        """Claim each eligible attempt at most once in this epoch."""
        return self._next_attempt(owner_id, continuation=False)

    def _next_attempt(self, owner_id: str, *, continuation: bool) -> Fence | None:
        identity = self._worker_identity
        if identity is None or identity[0] != owner_id or identity[2:] != (os.getpid(), threading.get_ident()):
            raise AttemptConflictError("WORKER_LOCK_REQUIRED")
        with self._transaction() as db:
            rows = db.execute("SELECT * FROM attempts WHERE state NOT IN "
                """('completed','failed','provider_confirmed_cancelled')
                   ORDER BY CASE WHEN provider_id IS NOT NULL THEN 0
                     WHEN state IN ('submitting','reconcile_needed','cancel_requested') THEN 1
                     ELSE 2 END, created_at, attempt_id""").fetchall()
            deferred: Fence | None = None
            for row in rows:
                previous = db.execute(
                    "SELECT sequence,payload_json FROM attempt_events WHERE attempt_id=? AND kind='claimed' "
                    "ORDER BY sequence DESC LIMIT 1", (row["attempt_id"],)).fetchone()
                controls = db.execute(
                    "SELECT sequence,kind,payload_json FROM attempt_events WHERE attempt_id=? "
                    "AND kind IN ('cancel_intent','reconcile_intent','reconcile_paused') "
                    "ORDER BY sequence", (row["attempt_id"],)
                ).fetchall()
                paused = max((item["sequence"] for item in controls
                              if item["kind"] == "reconcile_paused"), default=-1)
                intents = max((item["sequence"] for item in controls
                               if item["kind"] != "reconcile_paused"), default=-1)
                cancel_pending = any(item["kind"] == "cancel_intent" and item["sequence"] > paused
                                     for item in controls)
                if ((row["provider_id"] is None
                        and (row["state"] == "cancel_requested" or
                             (row["state"] == "reconcile_needed" and not cancel_pending)))
                        or (paused >= 0 and paused >= intents)):
                    continue
                if previous and json.loads(previous["payload_json"]).get("epoch") == identity[1]:
                    if continuation:
                        deferred = deferred or Fence(row["attempt_id"], owner_id, identity[1])
                    continue
                self._event(db, row["attempt_id"], "claimed", {"owner_id": owner_id, "epoch": identity[1]})
                fence = Fence(row["attempt_id"], owner_id, identity[1])
                # A prior SUBMITTING mark may already have caused a charge. Never enqueue again.
                if row["state"] == "submitting":
                    self._write_state(db, fence, AttemptState.SUBMITTING, "reconcile_needed", {})
                return fence
            return deferred
        return None

    def _write_state(self, db: sqlite3.Connection, fence: Fence, expected: AttemptState,
                     target: str, payload: dict[str, Any]) -> AttemptRecord:
        self._fenced(db, fence, expected)
        changed = db.execute("UPDATE attempts SET state=?,revision=revision+1 WHERE attempt_id=? AND state=?",
                             (target, fence.attempt_id, expected.value)).rowcount
        if changed != 1:
            raise AttemptConflictError("STALE_STATE")
        self._event(db, fence.attempt_id, target, payload)
        return self._attempt(db.execute("SELECT * FROM attempts WHERE attempt_id=?", (fence.attempt_id,)).fetchone())

    def transition_attempt(self, fence: Fence, expected_state: AttemptState, event: AttemptEvent) -> AttemptRecord:
        """Fenced, per-kind observations; uncertainty never grants terminal failure.

        Post-submit failure requires the immutable receipt digest. Output rejection
        additionally names protected candidate bytes and a bounded validation check;
        the consuming worker performs media validation, not this storage kernel.
        """
        allowed = {"prepared": {"ready", "failed", "provider_confirmed_cancelled"},
            "ready": {"submitting", "failed", "provider_confirmed_cancelled"},
            "submitting": {"reconcile_needed", "cancel_requested"},
            "submitted": {"running", "downloading", "failed", "reconcile_needed", "cancel_requested"},
            "running": {"downloading", "failed", "reconcile_needed", "cancel_requested"},
            "downloading": {"completed", "failed", "reconcile_needed", "cancel_requested"},
            "reconcile_needed": {"running", "downloading", "completed", "failed", "cancel_requested"},
            "cancel_requested": {"provider_confirmed_cancelled", "reconcile_needed", "downloading", "completed", "failed"}}
        payload = json.loads(event.payload_json)
        if not isinstance(payload, dict):
            raise ValidationError("INVALID_ATTEMPT_EVENT")
        required = {"supported": True, "confirmed": True} if (
            event.kind == "provider_confirmed_cancelled" and expected_state == AttemptState.CANCEL_REQUESTED) else {}
        known_failure = event.kind == "failed" and expected_state not in {AttemptState.PREPARED, AttemptState.READY}
        cancel_completion = event.kind == "downloading" and expected_state == AttemptState.CANCEL_REQUESTED
        if ((not known_failure and not cancel_completion and payload != required) or (required and any(value is not True for value in payload.values()))
                or event.kind not in allowed.get(expected_state.value, set())):
            raise ValidationError("INVALID_ATTEMPT_EVENT")
        with self._transaction() as db:
            attempt = self._fenced(db, fence, expected_state)
            if event.kind == "submitting" and db.execute("SELECT 1 FROM attempt_events WHERE attempt_id=? "
                    "AND kind='cancel_intent'", (attempt.id,)).fetchone():
                raise AttemptConflictError("CANCEL_PENDING")
            if event.kind in {"running", "downloading"} and attempt.provider_id is None:
                raise AttemptConflictError("RECEIPT_REQUIRED")
            if known_failure:
                self._validate_failure(attempt, payload)
            if cancel_completion and payload != {"remote_state": "completed",
                    "receipt_sha256": self._receipt(attempt).receipt_sha256}:
                raise ValidationError("INVALID_COMPLETION_OBSERVATION")
            if event.kind in {"running", "downloading", "provider_confirmed_cancelled"} and attempt.provider_id:
                self._receipt(attempt)
            if event.kind == "provider_confirmed_cancelled" and expected_state == AttemptState.CANCEL_REQUESTED:
                self._receipt(attempt)  # No-ID uncertainty is not confirmed cancellation.
            if event.kind == "completed":
                row = db.execute("SELECT payload_json FROM attempt_events WHERE attempt_id=? "
                    "AND kind='output' ORDER BY sequence DESC LIMIT 1", (attempt.id,)).fetchone()
                if row is None:
                    raise AttemptConflictError("OUTPUT_REQUIRED")
                output = OutputEvidence.from_json(row[0])
                if output.receipt != self._receipt(attempt):
                    raise ValidationError("OUTPUT_RECEIPT_MISMATCH")
                self._protected_binding_asset(attempt.project_id, output.asset_id, output.sha256, {"attempt_output"})
            return self._write_state(db, fence, expected_state, event.kind, payload)

    def _validate_failure(self, attempt: AttemptRecord, payload: dict[str, Any]) -> None:
        """Authenticate a known observation; no arbitrary diagnostic text or URLs."""
        if not isinstance(payload, dict):
            raise ValidationError("INVALID_FAILURE_EVENT")
        fields = {"reason", "receipt_sha256"}
        reason = payload.get("reason")
        if not isinstance(reason, str):
            raise ValidationError("INVALID_FAILURE_EVENT")
        if reason in {"output_bytes", "output_hash", "output_frames", "output_pts", "output_pixels"}:
            fields |= {"asset_id", "sha256"}
        elif reason != "remote_failed":
            raise ValidationError("INVALID_FAILURE_EVENT")
        if set(payload) != fields or any(not isinstance(value, str) for value in payload.values()):
            raise ValidationError("INVALID_FAILURE_EVENT")
        if payload["receipt_sha256"] != self._receipt(attempt).receipt_sha256:
            raise ValidationError("FAILURE_RECEIPT_MISMATCH")
        if "asset_id" in fields:
            self._protected_binding_asset(attempt.project_id, payload["asset_id"], payload["sha256"], {"attempt_output"})

    def _record_intent(self, attempt_id: str, kind: str) -> AttemptRecord:
        """Web requests append control intent, never borrow the active worker fence."""
        attempt = self._lookup_attempt(attempt_id)
        if kind not in {"cancel_intent", "reconcile_intent"}:
            raise ValidationError("INVALID_INTENT")
        with self._transaction() as db:
            self._event(db, attempt_id, kind, {})
        return self._lookup_attempt(attempt.id)

    def apply_cancel_intent(self, fence: Fence) -> AttemptRecord:
        """Consume queued/in-flight cancellation under the actual worker fence."""
        attempt = self._lookup_attempt(fence.attempt_id)
        with self._transaction() as db:
            self._fenced(db, fence, attempt.state)
            pending = db.execute("SELECT MAX(sequence) FROM attempt_events WHERE attempt_id=? AND kind='cancel_intent'",
                                 (attempt.id,)).fetchone()
            consumed = db.execute("SELECT payload_json FROM attempt_events WHERE attempt_id=? "
                "AND kind='cancel_intent_consumed' ORDER BY sequence DESC LIMIT 1", (attempt.id,)).fetchone()
            if pending[0] is None or (consumed and json.loads(consumed[0])["through_sequence"] >= pending[0]):
                return attempt
            self._event(db, attempt.id, "cancel_intent_consumed", {"through_sequence": pending[0]})
            if attempt.state in {AttemptState.COMPLETED, AttemptState.FAILED,
                    AttemptState.CANCEL_REQUESTED, AttemptState.PROVIDER_CONFIRMED_CANCELLED}:
                return attempt
            target = "provider_confirmed_cancelled" if attempt.state in {
                AttemptState.PREPARED, AttemptState.READY} else "cancel_requested"
            return self._write_state(db, fence, attempt.state, target, {})

    def _receipt(self, attempt: AttemptRecord) -> Receipt:
        with self._connect() as db:
            row = db.execute("SELECT * FROM provider_receipts WHERE attempt_id=?", (attempt.id,)).fetchone()
        if row is None:
            raise NotFoundError("RECEIPT_LOOKUP_PENDING")
        receipt = Receipt(*(row[key] for key in ("attempt_id", "provider_id", "request_key", "adapter_version",
            "endpoint_fingerprint", "receipt_asset_id", "receipt_sha256")))
        self._validate_receipt(attempt, receipt)
        return receipt

    def _validate_receipt(self, attempt: AttemptRecord, receipt: Receipt) -> None:
        op = self.get_operation(attempt.project_id, attempt.operation_id)
        if (receipt.attempt_id, receipt.request_key, receipt.adapter_version, receipt.endpoint_fingerprint) != (
                attempt.id, attempt.client_request_id, op.pin.adapter_version, op.pin.endpoint_fingerprint):
            raise ValidationError("RECEIPT_OWNERSHIP_MISMATCH")
        if attempt.provider_id is not None and attempt.provider_id != receipt.provider_id:
            raise AttemptConflictError("IMMUTABLE_PROVIDER_ID_CONFLICT")
        self._protected_binding_asset(attempt.project_id, receipt.receipt_asset_id,
                                      receipt.receipt_sha256, {"provider_receipt"})
        body = json.loads(self.resolve_asset(receipt.receipt_asset_id).path.read_bytes())
        if body != {"attempt_id": attempt.id, "provider_id": receipt.provider_id,
                    "request_key": receipt.request_key, "adapter_version": receipt.adapter_version,
                    "endpoint_fingerprint": receipt.endpoint_fingerprint}:
            raise ValidationError("RECEIPT_CONTENT_MISMATCH")

    def record_receipt(self, fence: Fence, receipt: Receipt) -> AttemptRecord:
        attempt = self._lookup_attempt(fence.attempt_id)
        self._validate_receipt(attempt, receipt)
        with self._transaction() as db:
            self._fenced(db, fence, attempt.state)
            row = db.execute("SELECT * FROM provider_receipts WHERE attempt_id=?", (attempt.id,)).fetchone()
            if row:
                if self._receipt(attempt) != receipt:
                    raise AttemptConflictError("IMMUTABLE_RECEIPT_CONFLICT")
                return attempt
            if attempt.state not in {AttemptState.SUBMITTING, AttemptState.RECONCILE_NEEDED, AttemptState.CANCEL_REQUESTED}:
                raise AttemptConflictError("RECEIPT_STATE_CONFLICT")
            db.execute("INSERT INTO provider_receipts VALUES (?,?,?,?,?,?,?,?)", (
                receipt.attempt_id, receipt.provider_id, receipt.request_key, receipt.adapter_version,
                receipt.endpoint_fingerprint, receipt.receipt_asset_id, receipt.receipt_sha256, _timestamp()))
            db.execute("UPDATE attempts SET provider_id=? WHERE attempt_id=?", (receipt.provider_id, attempt.id))
            target = "cancel_requested" if attempt.state == AttemptState.CANCEL_REQUESTED else "submitted"
            return self._write_state(db, fence, attempt.state, target, {})

    @staticmethod
    def _take(db: sqlite3.Connection, row: sqlite3.Row) -> TakeRecord:
        receipt = None
        if row["attempt_id"] is not None:
            receipt_row = db.execute("SELECT * FROM provider_receipts WHERE attempt_id=?",
                                     (row["attempt_id"],)).fetchone()
            if receipt_row is not None:
                receipt = Receipt(*(receipt_row[key] for key in (
                    "attempt_id", "provider_id", "request_key", "adapter_version",
                    "endpoint_fingerprint", "receipt_asset_id", "receipt_sha256")))
        output = OutputEvidence(str(row["output_asset_id"]), str(row["output_sha256"]),
            int(row["frame_count"]), Timebase(int(row["timebase_num"]), int(row["timebase_den"])), receipt)
        return TakeRecord(str(row["take_id"]), str(row["project_id"]),
            str(row["scene_revision_id"]) if row["scene_revision_id"] is not None else None,
            str(row["shot_id"]), str(row["attempt_id"]) if row["attempt_id"] is not None else None,
            str(row["operation_id"]) if row["operation_id"] is not None else None,
            output, str(row["origin"]), bool(row["qualified"]))

    def register_take(self, fence: Fence, evidence: OutputEvidence) -> TakeRecord:
        """Atomically derive the only qualified take scope from verified execution."""
        if not isinstance(fence, Fence) or not isinstance(evidence, OutputEvidence):
            raise ValidationError("take registration requires a typed fence and output evidence")
        attempt = self._lookup_attempt(fence.attempt_id)
        operation = self.get_operation(attempt.project_id, attempt.operation_id)
        scene = self.get_scene_revision(operation.project_id, operation.scene_revision_id)
        character = self.get_character_version(*operation.character_version)
        self.verify_preparation_binding(operation.project_id, operation.id, operation.fingerprint,
            source_asset_id=scene.source.asset_id,
            reference_asset_ids=tuple(character.reference_asset_ids))
        if (attempt.mode != ExecutionMode.DRY_RUN or self._receipt(attempt) != evidence.receipt
                or evidence.frame_count != operation.window.expected_decoder_frames
                or evidence.timebase != Timebase(1, 24)
                or operation.shot_id not in {shot.id for shot in scene.shots}):
            raise ValidationError("take output does not match its dry-run attempt")
        self._protected_binding_asset(attempt.project_id, evidence.asset_id, evidence.sha256,
                                      {"attempt_output"})
        with self._transaction() as db:
            fenced = self._fenced(db, fence, AttemptState.DOWNLOADING)
            if (fenced.project_id, fenced.operation_id) != (attempt.project_id, attempt.operation_id):
                raise ValidationError("take attempt scope mismatch")
            existing = db.execute("SELECT * FROM takes WHERE attempt_id=?", (attempt.id,)).fetchone()
            if existing is not None:
                take = self._take(db, existing)
                if take.output != evidence:
                    raise AttemptConflictError("attempt output is immutable")
                self._write_state(db, fence, AttemptState.DOWNLOADING, "completed", {})
                return take
            take_id = "take-" + uuid.uuid4().hex
            db.execute("INSERT INTO takes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                take_id, attempt.project_id, operation.scene_revision_id, operation.shot_id,
                attempt.id, operation.id, evidence.asset_id, evidence.sha256, evidence.frame_count,
                evidence.timebase.num, evidence.timebase.den, "dry_run", 1, _timestamp()))
            self._write_state(db, fence, AttemptState.DOWNLOADING, "completed", {})
            return self._take(db, db.execute("SELECT * FROM takes WHERE take_id=?", (take_id,)).fetchone())

    def get_take(self, project_id: str, take_id: str) -> TakeRecord:
        self.get_project(project_id)
        self._validate_id(take_id, "take", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute("SELECT * FROM takes WHERE project_id=? AND take_id=?",
                             (project_id, take_id)).fetchone()
            if row is None:
                raise NotFoundError("take not found")
            return self._take(db, row)

    def list_attached_takes(
        self, project_id: str, scene_revision_id: str, shot_id: str
    ) -> list[TakeRecord]:
        """List exactly one project/scene/shot take stream."""
        self.get_scene_revision(project_id, scene_revision_id)
        if not isinstance(shot_id, str) or not shot_id:
            raise ValidationError("shot_id must be non-empty text")
        with self._connect() as db:
            rows = db.execute(
                """SELECT * FROM takes WHERE project_id=? AND scene_revision_id=?
                   AND shot_id=? ORDER BY created_at,take_id""",
                (project_id, scene_revision_id, shot_id),
            ).fetchall()
            return [self._take(db, row) for row in rows]

    def list_unqualified_takes(self, project_id: str) -> list[TakeRecord]:
        """List only explicitly unattached historical imports."""
        self.get_project(project_id)
        with self._connect() as db:
            rows = db.execute(
                """SELECT t.* FROM takes t
                   LEFT JOIN unqualified_import_evidence e USING(take_id)
                   WHERE t.project_id=? AND t.scene_revision_id IS NULL
                     AND t.qualified=0 AND e.take_id IS NOT NULL
                   ORDER BY t.created_at,t.take_id""",
                (project_id,),
            ).fetchall()
            return [self._take(db, row) for row in rows]

    @staticmethod
    def _review(row: sqlite3.Row) -> ReviewRecord:
        return ReviewRecord(str(row["review_id"]), str(row["take_id"]),
                            ReviewVerdict(str(row["verdict"])), str(row["note"]))

    def append_review(self, review: ReviewRecord) -> ReviewRecord:
        """Append one human review; this never changes a take's qualification."""
        if not isinstance(review, ReviewRecord):
            raise ValidationError("review must be a typed ReviewRecord")
        with self._transaction() as db:
            take = db.execute("SELECT project_id FROM takes WHERE take_id=?",
                              (review.take_id,)).fetchone()
            if take is None:
                raise NotFoundError("take not found")
            db.execute("INSERT INTO reviews VALUES (?,?,?,?,?)", (
                review.id, review.take_id, review.verdict.value, review.note, _timestamp()))
        return review

    def list_reviews(self, take_id: str) -> list[ReviewRecord]:
        self._validate_id(take_id, "take", _EXTERNAL_ID)
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM reviews WHERE take_id=? ORDER BY created_at,review_id",
                (take_id,),
            ).fetchall()
            return [self._review(row) for row in rows]

    def get_unqualified_import_evidence(self, take_id: str) -> str:
        """Return only the canonical absent-metadata marker after restart."""
        self._validate_id(take_id, "take", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute(
                "SELECT marker_json FROM unqualified_import_evidence WHERE take_id=?",
                (take_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("unqualified import evidence not found")
        marker = str(row[0])
        if marker != _UNQUALIFIED_MARKER:
            raise ValidationError("unqualified import marker is malformed")
        return marker

    def append_unqualified_import_evidence(
        self, take_id: str, project_id: str, shot_id: str, imported_content_sha256: str
    ) -> None:
        """Append the one server-generated absence marker in its import transaction."""
        self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        self._validate_id(take_id, "take", _EXTERNAL_ID)
        if not isinstance(shot_id, str) or not shot_id:
            raise ValidationError("shot_id must be non-empty text")
        if not isinstance(imported_content_sha256, str):
            raise ValidationError("imported content hash must be text")
        with self._transaction() as db:
            take = db.execute(
                """SELECT project_id,scene_revision_id,shot_id,attempt_id,operation_id,
                          output_sha256,origin,qualified FROM takes WHERE take_id=?""",
                (take_id,),
            ).fetchone()
            if take is None or (
                take["project_id"], take["scene_revision_id"], take["shot_id"],
                take["attempt_id"], take["operation_id"], take["output_sha256"],
                take["origin"], take["qualified"],
            ) != (project_id, None, shot_id, None, None, imported_content_sha256,
                  "retained_replay", 0):
                raise ValidationError("unqualified evidence take scope mismatch")
            db.execute(
                "INSERT INTO unqualified_import_evidence VALUES (?,?,?,?,?,?,?)",
                (take_id, project_id, shot_id, imported_content_sha256,
                 _UNQUALIFIED_MARKER, _UNQUALIFIED_MARKER_SHA256, _timestamp()),
            )

    def select_take(
        self,
        project_id: str,
        scene_revision_id: str,
        shot_id: str,
        take_id: str | None,
        expected_revision: int,
    ) -> SelectionRecord:
        """Apply explicit compare-and-swap selection for one exact shot stream."""
        scene = self.get_scene_revision(project_id, scene_revision_id)
        if shot_id not in {shot.id for shot in scene.shots}:
            raise ValidationError("shot is not in the exact scene revision")
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 0:
            raise ValidationError("expected revision must be a non-negative integer")
        with self._transaction() as db:
            if take_id is not None:
                take = db.execute(
                    """SELECT * FROM takes WHERE project_id=? AND scene_revision_id=?
                       AND shot_id=? AND take_id=?""",
                    (project_id, scene_revision_id, shot_id, take_id),
                ).fetchone()
                if take is None or not take["qualified"]:
                    raise ValidationError("selection requires the exact qualified take")
            current = db.execute(
                """SELECT COALESCE(MAX(revision),0) FROM selection_events
                   WHERE project_id=? AND scene_revision_id=? AND shot_id=?""",
                (project_id, scene_revision_id, shot_id),
            ).fetchone()[0]
            if int(current) != expected_revision:
                raise AttemptConflictError(
                    "SELECTION_REVISION_CONFLICT"
                )
            revision = expected_revision + 1
            db.execute(
                "INSERT INTO selection_events VALUES (?,?,?,?,?,?,?)",
                ("selection-" + uuid.uuid4().hex, project_id, scene_revision_id,
                 shot_id, take_id, revision, _timestamp()),
            )
            return SelectionRecord(project_id, scene_revision_id, shot_id, take_id, revision)

    def list_selections(
        self, project_id: str, scene_revision_id: str, shot_id: str
    ) -> list[SelectionRecord]:
        """Expose durable selection history without public path data."""
        self.get_scene_revision(project_id, scene_revision_id)
        with self._connect() as db:
            rows = db.execute(
                """SELECT * FROM selection_events WHERE project_id=? AND scene_revision_id=?
                   AND shot_id=? ORDER BY revision""",
                (project_id, scene_revision_id, shot_id),
            ).fetchall()
            return [SelectionRecord(str(row["project_id"]), str(row["scene_revision_id"]),
                                    str(row["shot_id"]), str(row["take_id"]) if row["take_id"] is not None else None,
                                    int(row["revision"])) for row in rows]

    @staticmethod
    def _edit_revision(row: sqlite3.Row) -> EditRevision:
        try:
            items = tuple(EditItem.from_json(item) for item in json.loads(str(row["items_json"])))
            return EditRevision(
                str(row["edit_revision_id"]), str(row["project_id"]), str(row["scene_revision_id"]),
                items, AudioPolicy(str(row["audio"])),
                Timebase(int(row["timebase_num"]), int(row["timebase_den"])),
            )
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            raise ValidationError("edit revision record is malformed") from error

    def save_edit_revision(self, revision: EditRevision) -> EditRevision:
        """Persist the frozen caller revision without consulting current selections."""
        if not isinstance(revision, EditRevision):
            raise ValidationError("edit revision must be a typed EditRevision")
        scene = self.get_scene_revision(revision.project_id, revision.scene_revision_id)
        if not revision.items:
            raise ValidationError("edit revision requires at least one item")
        encoded = _canonical_json([dto_json(item) for item in revision.items])
        edit_id = "edit-" + uuid.uuid4().hex
        with self._transaction() as db:
            db.execute(
                "INSERT INTO edit_revisions VALUES (?,?,?,?,?,?,?,?)",
                (edit_id, revision.project_id, revision.scene_revision_id, encoded,
                 revision.audio.value, revision.timebase.num, revision.timebase.den, _timestamp()),
            )
        saved = replace(revision, id=edit_id)
        assert saved.items == revision.items and saved.scene_revision_id == scene.id
        return saved

    def get_edit_revision(self, project_id: str, revision_id: str) -> EditRevision:
        self.get_project(project_id)
        self._validate_id(revision_id, "edit revision", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM edit_revisions WHERE project_id=? AND edit_revision_id=?",
                (project_id, revision_id),
            ).fetchone()
            if row is None:
                raise NotFoundError("edit revision not found")
            return self._edit_revision(row)

    def complete_export(self, export: ExportRecord) -> ExportRecord:
        """Commit only measured, protected output bytes for a completed edit."""
        if not isinstance(export, ExportRecord) or export.state != "completed":
            raise ValidationError("only a measured completed export can be committed")
        revision = self.get_edit_revision_by_id(export.revision_id)
        if export.asset_id is None or export.sha256 is None:
            raise ValidationError("completed export requires output evidence")
        resolved = self.resolve_asset(export.asset_id)
        if (not resolved.record.protected or resolved.record.project_id != revision.project_id
                or resolved.record.role != "edit_export"
                or resolved.record.sha256 != export.sha256):
            raise ValidationError("export asset is not a protected project output")
        export_id = "export-" + uuid.uuid4().hex
        with self._transaction() as db:
            db.execute(
                "INSERT INTO exports VALUES (?,?,?,?,?,?,?)",
                (export_id, export.revision_id, "completed", export.asset_id,
                 export.sha256, export.checks_json, _timestamp()),
            )
        return replace(export, id=export_id)

    def get_edit_revision_by_id(self, revision_id: str) -> EditRevision:
        self._validate_id(revision_id, "edit revision", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM edit_revisions WHERE edit_revision_id=?", (revision_id,)
            ).fetchone()
            if row is None:
                raise NotFoundError("edit revision not found")
            return self._edit_revision(row)

    def get_export(self, project_id: str, export_id: str) -> ExportRecord:
        self.get_project(project_id)
        self._validate_id(export_id, "export", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute(
                """SELECT x.* FROM exports x JOIN edit_revisions e
                   USING(edit_revision_id) WHERE x.export_id=? AND e.project_id=?""",
                (export_id, project_id),
            ).fetchone()
            if row is None:
                raise NotFoundError("export not found")
            return ExportRecord(
                str(row["export_id"]), str(row["edit_revision_id"]), str(row["state"]),
                str(row["asset_id"]) if row["asset_id"] is not None else None,
                str(row["sha256"]) if row["sha256"] is not None else None,
                str(row["checks_json"]),
            )

    def _export_revision_id(self, export_id: str) -> str:
        self._validate_id(export_id, "export", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute(
                "SELECT edit_revision_id FROM exports WHERE export_id=?", (export_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError("export not found")
        return str(row[0])

    def _qualified_replay_carrier(
        self, project_id: str, scene_revision_id: str, shot_id: str, take_id: str
    ) -> tuple[WindowMap, RecipePin]:
        """Reconcile one append-only retained carrier to its immutable operation."""
        self.get_project(project_id)
        with self._connect() as db:
            row = db.execute(
                """SELECT q.window_json AS q_window,q.recipe_id AS q_recipe_id,
                          q.recipe_version AS q_recipe_version,
                          q.raw_graph_sha256 AS q_raw_graph,q.source_sha256 AS q_source,
                          q.input_sha256 AS q_input,
                          q.resolved_graph_sha256 AS q_resolved,
                          q.output_sha256 AS q_output,q.operation_id AS q_operation,
                          q.project_id AS q_project,q.scene_revision_id AS q_scene,
                          q.shot_id AS q_shot,
                          t.project_id AS take_project,t.scene_revision_id AS take_scene,
                          t.shot_id AS take_shot,t.attempt_id AS take_attempt,
                          t.operation_id AS take_operation,
                          t.output_asset_id AS take_asset,
                          t.output_sha256 AS take_output,t.origin AS take_origin,
                          t.qualified AS take_qualified,
                          a.project_id AS asset_project,a.sha256 AS asset_sha256,
                          a.protected AS asset_protected,a.role AS asset_role,
                          o.operation_id AS op_id,o.pin_json AS op_pin,
                          o.project_id AS op_project,o.scene_revision_id AS op_scene,
                          o.shot_id AS op_shot
                   FROM qualified_replay_receipts q JOIN takes t ON(t.take_id=q.take_id)
                   JOIN assets a ON(a.asset_id=t.output_asset_id)
                   LEFT JOIN operations o ON(o.operation_id=q.operation_id)
                   WHERE q.take_id=? AND q.project_id=? AND q.scene_revision_id=?
                     AND q.shot_id=?""",
                (take_id, project_id, scene_revision_id, shot_id),
            ).fetchone()
        if row is None:
            raise ValidationError("qualified replay carrier is missing or cross-scope")
        if row["q_operation"] is None or row["take_operation"] is None or row["op_id"] is None:
            raise ValidationError("qualified replay carrier lacks a non-null linked operation")
        if (row["op_project"], row["op_scene"], row["op_shot"]) != (
                project_id, scene_revision_id, shot_id):
            raise ValidationError("qualified replay carrier operation scope drifted")
        if (row["take_project"], row["take_scene"], row["take_shot"],
                row["take_operation"]) != (
                project_id, scene_revision_id, shot_id, row["q_operation"]):
            raise ValidationError("qualified replay carrier take scope drifted")
        if (row["take_origin"], row["take_qualified"], row["take_attempt"]) != (
                "retained_replay", 1, None):
            raise ValidationError("qualified replay carrier lineage is invalid")
        if (row["asset_project"] != project_id or not row["asset_protected"]
                or row["asset_role"] != "retained_replay_output"
                or row["asset_sha256"] != row["q_output"]
                or row["take_output"] != row["q_output"]):
            raise ValidationError("qualified replay output asset hash or protection drifted")
        try:
            operation = self.get_operation(project_id, str(row["q_operation"]))
            manifest = json.loads(operation.canonical_json)
            carrier_window = WindowMap.from_json(str(row["q_window"]))
            canonical_window = _canonical_json(dto_json(carrier_window))
        except (
            TypeError, ValueError, KeyError, IndexError, json.JSONDecodeError,
            WorkspaceStoreError,
        ) as error:
            raise ValidationError("qualified replay carrier is malformed") from error
        if canonical_window != str(row["q_window"]) or carrier_window != operation.window:
            raise ValidationError("qualified replay carrier window is noncanonical or drifted")
        if (row["q_recipe_id"], row["q_recipe_version"], row["q_raw_graph"]) != (
                operation.pin.recipe_id, operation.pin.version, operation.pin.raw_graph_sha256):
            raise ValidationError("qualified replay carrier pin identity drifted")
        if (row["q_source"], row["q_input"], row["q_resolved"], row["q_output"]) != (
                manifest["source"]["sha256"], manifest["source"]["proxy_sha256"],
                manifest["graph"]["resolved_semantic_sha256"], row["q_output"]):
            raise ValidationError("qualified replay carrier provenance hashes drifted")
        try:
            resolved_output = self.resolve_asset(str(row["take_asset"]))
        except AssetIntegrityError as error:
            raise ValidationError("qualified replay output bytes fail their protected hash") from error
        if (resolved_output.record.sha256 != row["q_output"]
                or resolved_output.record.role != "retained_replay_output"):
            raise ValidationError("qualified replay output bytes fail their protected hash")
        return carrier_window, operation.pin

    def _stage_import_content(
        self, project_id: str, filename: str, content: BinaryIO, *, role: str
    ) -> tuple[str, str, str, Path, str]:
        """Stage trusted bytes without committing an asset row."""
        self.get_project(project_id)
        if (not isinstance(filename, str) or not filename or "/" in filename
                or "\\" in filename or Path(filename).parts != (filename,)):
            raise ValidationError("import filename must be one safe component")
        staging_id = uuid.uuid4().hex
        directory = self.uploads_root / staging_id
        directory.mkdir()
        temporary = directory / f".{staging_id}.tmp"
        destination = directory / filename
        digest = hashlib.sha256()
        try:
            with temporary.open(mode="xb") as output:
                while chunk := content.read(1024 * 1024):
                    if not isinstance(chunk, bytes):
                        raise ValidationError("import content must be binary")
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
            os.replace(temporary, destination)
            return (staging_id, digest.hexdigest(), role, destination, filename)
        except BaseException:
            self._remove_staging_directory(directory)
            raise

    @staticmethod
    def _insert_staged_asset(
        db: sqlite3.Connection, project_id: str, staged: tuple[str, str, str, Path, str]
    ) -> str:
        staging_id, sha256, role, path, filename = staged
        asset_id = uuid.uuid4().hex
        db.execute("INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
            asset_id, project_id, role, filename,
            mimetypes.guess_type(filename)[0], path.stat().st_size, sha256, 1,
            _timestamp(), "uploads", f"{staging_id}/{filename}",
        ))
        return asset_id

    def _atomic_unqualified_import(
        self, project_id: str, shot_id: str, content: BinaryIO,
        *, frame_count: int, timebase: Timebase,
    ) -> TakeRecord:
        staged = self._stage_import_content(
            project_id, "retained-historical-output.bin", content, role="historical_output"
        )
        directory = staged[3].parent
        try:
            with self._transaction() as db:
                self._require_project(db, project_id)
                shot = db.execute(
                    """SELECT 1 FROM shots s JOIN scene_revisions r USING(scene_revision_id)
                       WHERE r.project_id=? AND s.shot_id=?""",
                    (project_id, shot_id),
                ).fetchone()
                if shot is None:
                    raise ValidationError("shot_id is not present in this project")
                asset_id = self._insert_staged_asset(db, project_id, staged)
                take_id = "take-" + uuid.uuid4().hex
                db.execute("INSERT INTO takes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                    take_id, project_id, None, shot_id, None, None, asset_id, staged[1],
                    frame_count, timebase.num, timebase.den,
                    "retained_replay", 0, _timestamp()))
                db.execute(
                    "INSERT INTO unqualified_import_evidence VALUES (?,?,?,?,?,?,?)",
                    (take_id, project_id, shot_id, staged[1], _UNQUALIFIED_MARKER,
                     _UNQUALIFIED_MARKER_SHA256, _timestamp()),
                )
        except BaseException:
            self._remove_staging_directory(directory)
            raise
        return self.get_take(project_id, take_id)

    def _atomic_replay_import(
        self,
        project_id: str,
        receipt: ReplayReceipt,
        content: BinaryIO,
        *,
        frame_count: int,
        timebase: Timebase,
        operation_id: str | None,
    ) -> TakeRecord:
        scene_project = self._project_id_for_scene(receipt.scene_revision_id)
        if scene_project != project_id:
            raise ValidationError("replay receipt belongs to another project")
        staged = self._stage_import_content(
            project_id, "retained-replay-output.nut", content, role="retained_replay_output"
        )
        directory = staged[3].parent
        try:
            with self._transaction() as db:
                attached = db.execute(
                    """SELECT r.project_id FROM scene_revisions r JOIN shots s
                       USING(scene_revision_id) WHERE r.scene_revision_id=? AND s.shot_id=?""",
                    (receipt.scene_revision_id, receipt.shot_id),
                ).fetchone()
                if attached is None or attached["project_id"] != project_id:
                    raise ValidationError("replay scene revision or shot scope mismatch")
                operation = None
                if operation_id is not None:
                    operation = db.execute(
                        """SELECT project_id,scene_revision_id,shot_id FROM operations
                           WHERE operation_id=?""",
                        (operation_id,),
                    ).fetchone()
                    if operation is None or tuple(operation) != (
                        project_id, receipt.scene_revision_id, receipt.shot_id
                    ):
                        raise ValidationError("replay operation scope mismatch")
                asset_id = self._insert_staged_asset(db, project_id, staged)
                take_id = "take-" + uuid.uuid4().hex
                db.execute("INSERT INTO takes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                    take_id, project_id, receipt.scene_revision_id, receipt.shot_id,
                    None, operation_id, asset_id, receipt.output_sha256, frame_count,
                    timebase.num, timebase.den, "retained_replay", 1, _timestamp()))
                db.execute(
                    """INSERT INTO qualified_replay_receipts VALUES (
                       ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (take_id, project_id, receipt.scene_revision_id, receipt.shot_id,
                     receipt.source_sha256, receipt.input_sha256, receipt.recipe_id,
                     receipt.recipe_version, receipt.raw_graph_sha256,
                     receipt.resolved_graph_sha256, receipt.output_sha256,
                     json.dumps(dto_json(receipt.window), sort_keys=True, separators=(",", ":")),
                     receipt.historical_verdict.value if receipt.historical_verdict is not None else None,
                     operation_id, _timestamp()),
                )
        except BaseException:
            self._remove_staging_directory(directory)
            raise
        return self.get_take(project_id, take_id)

    def _project_id_for_scene(self, scene_revision_id: str) -> str:
        self._validate_id(scene_revision_id, "scene revision", _EXTERNAL_ID)
        with self._connect() as db:
            row = db.execute(
                "SELECT project_id FROM scene_revisions WHERE scene_revision_id=?",
                (scene_revision_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("scene revision not found")
        return str(row[0])

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.db_path, timeout=30.0)
        db.row_factory = sqlite3.Row
        db.create_function("m1_window_valid", 1, _m1_window_valid, deterministic=True)
        try:
            db.execute("PRAGMA foreign_keys = ON"); db.execute("PRAGMA busy_timeout = 30000")
            yield db
        except sqlite3.Error as error:
            raise self._database_error(error) from error
        finally:
            db.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
            except BaseException:
                db.rollback(); raise
            else:
                db.commit()

    @staticmethod
    def _database_error(error: sqlite3.Error) -> WorkspaceStoreError:
        if isinstance(error, sqlite3.IntegrityError):
            return ValidationError("record already exists or violates a workspace invariant")
        return WorkspaceStoreError("workspace database operation failed")

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(project_id),
                    role TEXT NOT NULL, filename TEXT NOT NULL, media_type TEXT,
                    size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
                    protected INTEGER NOT NULL, created_at TEXT NOT NULL,
                    root_kind TEXT NOT NULL CHECK (root_kind IN ('uploads', 'imports')),
                    relative_path TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS character_versions (
                    character_id TEXT NOT NULL, version INTEGER NOT NULL,
                    name TEXT NOT NULL, description TEXT NOT NULL,
                    reference_asset_ids TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (character_id, version)
                );
                CREATE TABLE IF NOT EXISTS prepared_configs (
                    project_id TEXT NOT NULL, job_id TEXT NOT NULL, character_id TEXT,
                    character_version INTEGER, seed INTEGER NOT NULL,
                    workflow_sha256 TEXT NOT NULL, prompt_sha256 TEXT NOT NULL,
                    source_sha256 TEXT, reference_sha256s TEXT NOT NULL,
                    config_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (project_id, job_id),
                    CHECK ((character_id IS NULL) = (character_version IS NULL))
                );
                """
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                    applied_at TEXT NOT NULL)"""
            )
            with self._transaction() as db:
                self._migrate(db)

    @staticmethod
    def _migrate(db: sqlite3.Connection) -> None:
        """Apply only unapplied versioned migrations inside one write transaction."""
        row = db.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()
        current = int(row[0])
        for version in range(current + 1, 5):
            statements = _M1_MIGRATION_STATEMENTS if version == 1 else ()
            for statement in statements:
                db.execute(statement)
            if version == 2:
                try:
                    _migrate_scope(db)
                except sqlite3.Error as error:
                    raise ValidationError("scope migration v2: legacy rows violate scoped integrity; "
                                          "repair ownership/references before retrying; database unchanged") from error
            if version == 3:
                db.execute(_PREPARATION_BINDINGS_SQL)
                db.execute(_PREPARATION_BINDING_UPDATE_TRIGGER)
                db.execute(_PREPARATION_BINDING_DELETE_TRIGGER)
            if version == 4:
                _evidence_triggers(db)
            db.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, {1: "managed_milestone_one_schema", 2: "scene_scoped_take_contract",
                           3: "concrete_preparation_bindings",
                           4: "replay_and_unqualified_import_evidence"}[version], _timestamp()),
            )

    def save_scene_revision(self, scene: SceneRevision) -> SceneRevision:
        """Persist one complete, immutable project/source partition."""
        if not isinstance(scene, SceneRevision):
            raise ValidationError("scene revision must be a typed record")
        self._validate_id(scene.project_id, "project", _ASSET_OR_PROJECT_ID)
        source = scene.source
        if not isinstance(source, SourceTiming) or not isinstance(source.timebase, Timebase):
            raise ValidationError("scene source timing is malformed")
        if source.frame_count < 1 or source.cfr is not True:
            raise ValidationError("scene source must be decoded constant-frame-rate media")
        shots = scene.shots
        if not isinstance(shots, tuple) or not shots:
            raise ValidationError("scene revision requires at least one shot")
        cursor = 0
        seen: set[str] = set()
        for shot in shots:
            if not isinstance(shot, ShotSpec) or shot.id in seen:
                raise ValidationError("scene shots must have distinct IDs")
            seen.add(shot.id)
            if shot.source_range.start != cursor or shot.source_range.end > source.frame_count:
                raise ValidationError(
                    "scene shots must exactly partition [0, source_frame_count) without gaps or overlap"
                )
            cursor = shot.source_range.end
        if cursor != source.frame_count:
            raise ValidationError(
                "scene shots must exactly partition [0, source_frame_count) without gaps or overlap"
            )

        scene_id = "scene_" + uuid.uuid4().hex
        now = _timestamp()
        with self._transaction() as db:
            self._require_project(db, scene.project_id)
            source_row = db.execute(
                "SELECT project_id, sha256, protected, role FROM assets WHERE asset_id = ?",
                (source.asset_id,),
            ).fetchone()
            if source_row is None:
                raise NotFoundError("source asset not found")
            if str(source_row["project_id"]) != scene.project_id or not bool(source_row["protected"]):
                raise ValidationError("source asset is not owned by the requested project")
            if str(source_row["sha256"]) != source.sha256 or source_row["role"] != "source":
                raise ValidationError("source timing does not match the protected source asset")
            revision = int(
                db.execute(
                    "SELECT COALESCE(MAX(revision), 0) + 1 FROM scene_revisions WHERE project_id = ?",
                    (scene.project_id,),
                ).fetchone()[0]
            )
            db.execute(
                """INSERT INTO scene_revisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (scene_id, scene.project_id, source.asset_id, source.sha256,
                 source.frame_count, source.timebase.num, source.timebase.den,
                 int(source.cfr), int(source.has_audio), revision, now),
            )
            for ordinal, shot in enumerate(shots):
                db.execute(
                    "INSERT INTO shots VALUES (?, ?, ?, ?, ?, ?)",
                    (scene_id, shot.id, ordinal, shot.source_range.start,
                     shot.source_range.end, shot.kind),
                )
        return SceneRevision(
            id=scene_id,
            project_id=scene.project_id,
            source=source,
            shots=shots,
            revision=revision,
        )

    def get_scene_revision(self, project_id: str, revision_id: str) -> SceneRevision:
        self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        self._validate_id(revision_id, "scene revision", _EXTERNAL_ID)
        with self._connect() as db:
            self._require_project(db, project_id)
            row = db.execute(
                "SELECT * FROM scene_revisions WHERE project_id = ? AND scene_revision_id = ?",
                (project_id, revision_id),
            ).fetchone()
            if row is None:
                raise NotFoundError("scene revision not found")
            shot_rows = db.execute(
                "SELECT * FROM shots WHERE scene_revision_id = ? ORDER BY ordinal",
                (revision_id,),
            ).fetchall()
        return self._scene(row, shot_rows)

    def list_scene_revisions(self, project_id: str) -> list[SceneRevision]:
        self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        with self._connect() as db:
            self._require_project(db, project_id)
            rows = db.execute(
                "SELECT * FROM scene_revisions WHERE project_id = ? ORDER BY revision DESC",
                (project_id,),
            ).fetchall()
            result: list[SceneRevision] = []
            for row in rows:
                shots = db.execute(
                    "SELECT * FROM shots WHERE scene_revision_id = ? ORDER BY ordinal",
                    (row["scene_revision_id"],),
                ).fetchall()
                result.append(self._scene(row, shots))
        return result

    def save_operation(self, operation: ResolvedOperation) -> ResolvedOperation:
        """Persist one immutable resolved operation scoped to its scene and shot."""
        if not isinstance(operation, ResolvedOperation):
            raise ValidationError("resolved operation must be a typed record")
        self._validate_id(operation.project_id, "project", _ASSET_OR_PROJECT_ID)
        self._validate_id(operation.id, "operation", _EXTERNAL_ID)
        self._validate_id(operation.scene_revision_id, "scene revision", _EXTERNAL_ID)
        self._validate_id(operation.managed_job_id, "managed job", _EXTERNAL_ID)
        if operation.character_version[1] < 1:
            raise ValidationError("resolved character version must be positive")
        expected_fingerprint = hashlib.sha256(operation.canonical_json.encode("utf-8")).hexdigest()
        if operation.fingerprint != expected_fingerprint:
            raise ValidationError("operation fingerprint does not match its canonical manifest")
        now = _timestamp()
        with self._transaction() as db:
            self._insert_operation(db, operation, now)
        return self.get_operation(operation.project_id, operation.id)

    def _insert_operation(
        self, db: sqlite3.Connection, operation: ResolvedOperation, now: str
    ) -> None:
        self._require_project(db, operation.project_id)
        attached = db.execute(
            """SELECT 1 FROM shots JOIN scene_revisions USING(scene_revision_id)
               WHERE scene_revision_id = ? AND project_id = ? AND shot_id = ?""",
            (operation.scene_revision_id, operation.project_id, operation.shot_id),
        ).fetchone()
        if attached is None:
            raise ValidationError("operation scene revision or shot is not project-scoped")
        character_id, character_version = operation.character_version
        db.execute(
            """INSERT INTO operations (
                   operation_id, project_id, scene_revision_id, shot_id, window_json,
                   pin_json, character_id, character_version, seed, canonical_json,
                   fingerprint, managed_job_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (operation.id, operation.project_id, operation.scene_revision_id,
             operation.shot_id, json.dumps(dto_json(operation.window), sort_keys=True),
             json.dumps(dto_json(operation.pin), sort_keys=True), character_id,
             character_version, operation.seed, operation.canonical_json,
             operation.fingerprint, operation.managed_job_id, now),
        )

    def get_operation(self, project_id: str, operation_id: str) -> ResolvedOperation:
        self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        self._validate_id(operation_id, "operation", _EXTERNAL_ID)
        with self._connect() as db:
            self._require_project(db, project_id)
            row = db.execute(
                "SELECT * FROM operations WHERE project_id = ? AND operation_id = ?",
                (project_id, operation_id),
            ).fetchone()
        if row is None:
            raise NotFoundError("resolved operation not found")
        try:
            return ResolvedOperation(
                id=str(row["operation_id"]),
                project_id=str(row["project_id"]),
                scene_revision_id=str(row["scene_revision_id"]),
                shot_id=str(row["shot_id"]),
                window=WindowMap.from_json(str(row["window_json"])),
                pin=RecipePin.from_json(str(row["pin_json"])),
                character_version=(str(row["character_id"]), int(row["character_version"])),
                seed=int(row["seed"]),
                canonical_json=str(row["canonical_json"]),
                fingerprint=str(row["fingerprint"]),
                managed_job_id=str(row["managed_job_id"]),
            )
        except (TypeError, ValueError) as error:
            raise ValidationError("resolved operation record is malformed") from error

    def _protected_binding_asset(
        self, project_id: str, asset_id: str, expected_sha256: str, roles: set[str]
    ) -> AssetRecord:
        resolved = self.resolve_asset(asset_id)
        record = resolved.record
        if (
            record.project_id != project_id
            or not record.protected
            or record.role not in roles
            or record.sha256 != expected_sha256
        ):
            raise ValidationError("preparation binding asset role, ownership, or hash is invalid")
        return record

    def save_preparation_binding(
        self,
        operation: ResolvedOperation,
        binding: BoundSubmission,
        *,
        source_asset_id: str,
        reference_asset_ids: tuple[str, ...],
    ) -> BoundSubmission:
        return self._save_preparation_binding_internal(
            operation, binding, source_asset_id=source_asset_id,
            reference_asset_ids=reference_asset_ids,
        )

    def _binding_context(
        self, operation: ResolvedOperation, binding: BoundSubmission,
        source_asset_id: str, reference_asset_ids: tuple[str, ...],
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any],
               AssetRecord, AssetRecord, AssetRecord, list[AssetRecord], dict[str, Any], tuple[str, str]]:
        binding_asset = self._protected_binding_asset(
            operation.project_id, binding.binding_asset_id, binding.binding_sha256,
            {"preparation_binding"},
        )
        envelope = json.loads(self.resolve_asset(binding_asset.asset_id).path.read_bytes())
        graph = envelope.get("graph", {})
        cpu_input = envelope.get("cpu_input", {})
        references = envelope.get("references", [])
        if (
            envelope.get("schema_version") != 1 or envelope.get("operation_id") != operation.id
            or envelope.get("operation_fingerprint") != operation.fingerprint
            or envelope.get("source", {}).get("asset_id") != source_asset_id
            or [item.get("asset_id") for item in references] != list(reference_asset_ids)
            or not isinstance(cpu_input, dict)
        ):
            raise ValidationError("binding envelope does not match operation or typed roles")
        manifest = json.loads(operation.canonical_json)
        if (
            graph.get("semantic_sha256") != manifest["graph"]["resolved_semantic_sha256"]
            or envelope["source"].get("sha256") != manifest["source"]["sha256"]
            or [item.get("sha256") for item in references] != manifest["character"]["reference_hashes"]
            or cpu_input.get("sha256") != manifest["source"]["proxy_sha256"]
            or envelope.get("prompt_sha256") != manifest["prompt"]["sha256"]
            or envelope.get("word_schedule_sha256") != manifest["prompt"]["word_schedule_sha256"]
            or envelope.get("adapter_version") != manifest["adapter"]["version"]
            or envelope.get("endpoint_fingerprint") != manifest["adapter"]["endpoint_fingerprint"]
        ):
            raise ValidationError("binding envelope does not match canonical effective inputs")
        graph_asset = self._protected_binding_asset(
            operation.project_id, graph.get("asset_id", ""), graph.get("sha256", ""), {"managed_graph"}
        )
        source_asset = self._protected_binding_asset(
            operation.project_id, source_asset_id, envelope["source"].get("sha256", ""), {"source"}
        )
        cpu_asset = self._protected_binding_asset(
            operation.project_id, cpu_input.get("asset_id", ""), cpu_input.get("sha256", ""),
            {"cpu_input", "source"},
        )
        reference_assets = [self._protected_binding_asset(
            operation.project_id, item.get("asset_id", ""), item.get("sha256", ""),
            {"reference_1", "reference_2"},
        ) for item in references]
        substitutions = envelope.get("substitutions")
        digests = (envelope.get("prompt_sha256"), envelope.get("word_schedule_sha256"))
        if (
            not isinstance(substitutions, dict) or not isinstance(envelope.get("prompt_content"), str)
            or not isinstance(envelope.get("word_schedule_content"), str)
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in digests)
            or not isinstance(envelope.get("adapter_version"), str)
            or not isinstance(envelope.get("endpoint_fingerprint"), str)
        ):
            raise ValidationError("binding envelope metadata is malformed")
        return (envelope, graph, references, manifest, graph_asset, source_asset,
                cpu_asset, reference_assets, substitutions, digests)

    def _validate_concrete_binding(
        self, operation: ResolvedOperation, envelope: dict[str, Any], graph: dict[str, Any],
        cpu_input: dict[str, Any], manifest: dict[str, Any], graph_asset: AssetRecord,
        cpu_asset: AssetRecord, reference_assets: list[AssetRecord],
        reference_asset_ids: tuple[str, ...], substitutions: dict[str, Any],
    ) -> None:
        actual_graph = json.loads(self.resolve_asset(graph_asset.asset_id).path.read_bytes())
        actual_semantic = hashlib.sha256(json.dumps(
            _effective_workflow(actual_graph), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")).hexdigest()
        actual_plan = json.loads(actual_graph["1189"]["inputs"]["plan"])
        expected_outputs = {
            "primary": f"openjutsu/{operation.managed_job_id}",
            "comparison": f"openjutsu/{operation.managed_job_id}_compare",
        }
        if (
            actual_semantic != manifest["graph"]["resolved_semantic_sha256"]
            or graph.get("semantic_sha256") != actual_semantic
            or actual_plan["video"] != cpu_asset.filename
            or actual_plan["global_ref"] != reference_assets[0].filename
            or actual_plan["global_ref2"] != reference_assets[1].filename
            or substitutions.get("planner") != {
                "video": actual_plan["video"], "global_ref": actual_plan["global_ref"],
                "global_ref2": actual_plan["global_ref2"], "source_asset_id": cpu_asset.asset_id,
                "reference_asset_ids": list(reference_asset_ids),
            }
            or substitutions.get("outputs") != expected_outputs
            or actual_graph["751"]["inputs"]["filename_prefix"] != expected_outputs["primary"]
            or actual_graph["1110"]["inputs"]["filename_prefix"] != expected_outputs["comparison"]
            or cpu_input.get("original_range") != [operation.window.source_range.start, operation.window.source_range.end]
            or cpu_input.get("render_range") != [operation.window.render_range.start, operation.window.render_range.end]
            or hashlib.sha256(envelope["prompt_content"].encode()).hexdigest() != envelope["prompt_sha256"]
            or hashlib.sha256(envelope["word_schedule_content"].encode()).hexdigest() != envelope["word_schedule_sha256"]
        ):
            raise ValidationError("binding concrete graph, roles, outputs, map, or prompt bytes are invalid")

    def _save_preparation_binding_internal(
        self,
        operation: ResolvedOperation,
        binding: BoundSubmission,
        *,
        source_asset_id: str,
        reference_asset_ids: tuple[str, ...],
        _operation_transaction: sqlite3.Connection | None = None,
    ) -> BoundSubmission:
        """Persist the sole immutable concrete association for one operation."""
        if not isinstance(operation, ResolvedOperation) or not isinstance(binding, BoundSubmission):
            raise ValidationError("preparation binding inputs must be typed records")
        if binding.operation_id != operation.id or binding.charge_bearing:
            raise ValidationError("offline preparation binding must be non-charge-bearing")
        envelope, graph, _references, manifest, graph_asset, source_asset, cpu_asset, reference_assets, substitutions, digests = self._binding_context(
            operation, binding, source_asset_id, reference_asset_ids
        )
        self._validate_concrete_binding(
            operation, envelope, graph, envelope["cpu_input"], manifest, graph_asset,
            cpu_asset, reference_assets, reference_asset_ids, substitutions,
        )
        values = (
            operation.id, operation.project_id, binding.binding_asset_id, binding.binding_sha256,
            operation.fingerprint, graph_asset.asset_id, graph_asset.sha256,
            source_asset.asset_id, source_asset.sha256,
            json.dumps(reference_asset_ids, separators=(",", ":")),
            json.dumps([item.sha256 for item in reference_assets], separators=(",", ":")),
            cpu_asset.asset_id, cpu_asset.sha256,
            json.dumps(substitutions, sort_keys=True, separators=(",", ":")),
            digests[0], digests[1], envelope["adapter_version"], envelope["endpoint_fingerprint"],
            _timestamp(),
        )
        def persist(db: sqlite3.Connection) -> BoundSubmission:
            self._require_project(db, operation.project_id)
            operation_row = db.execute(
                "SELECT project_id,fingerprint FROM operations WHERE operation_id = ?",
                (operation.id,),
            ).fetchone()
            if operation_row is None or tuple(operation_row) != (operation.project_id, operation.fingerprint):
                raise ValidationError("preparation binding operation is missing or changed")
            existing = db.execute(
                "SELECT * FROM preparation_bindings WHERE operation_id = ?", (operation.id,)
            ).fetchone()
            if existing is not None:
                persisted = tuple(existing[column] for column in existing.keys()[:-1])
                if persisted != values[:-1]:
                    raise ValidationError("preparation binding is immutable")
                return binding
            db.execute("INSERT INTO preparation_bindings VALUES (" + ",".join("?" for _ in values) + ")", values)
            return binding
        if _operation_transaction is not None:
            return persist(_operation_transaction)
        with self._transaction() as db:
            return persist(db)

    def _save_operation_and_preparation(
        self,
        operation: ResolvedOperation,
        binding: BoundSubmission,
        *,
        source_asset_id: str,
        reference_asset_ids: tuple[str, ...],
    ) -> ResolvedOperation:
        expected = hashlib.sha256(operation.canonical_json.encode("utf-8")).hexdigest()
        if operation.fingerprint != expected:
            raise ValidationError("operation fingerprint does not match its canonical manifest")
        with self._transaction() as db:
            self._insert_operation(db, operation, _timestamp())
            self._save_preparation_binding_internal(
                operation,
                binding,
                source_asset_id=source_asset_id,
                reference_asset_ids=reference_asset_ids,
                _operation_transaction=db,
            )
        return self.get_operation(operation.project_id, operation.id)

    def _binding_row(self, project_id: str, operation_id: str) -> sqlite3.Row:
        self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        self._validate_id(operation_id, "operation", _EXTERNAL_ID)
        with self._connect() as db:
            self._require_project(db, project_id)
            row = db.execute(
                """SELECT p.* FROM preparation_bindings p JOIN operations o USING(operation_id)
                   WHERE p.project_id = ? AND o.project_id = ? AND p.operation_id = ?""",
                (project_id, project_id, operation_id),
            ).fetchone()
        if row is None:
            raise NotFoundError("preparation binding not found")
        return row

    def _revalidate_binding(self, row: sqlite3.Row) -> BoundSubmission:
        binding_asset = self._protected_binding_asset(
            str(row["project_id"]), str(row["binding_asset_id"]), str(row["binding_sha256"]),
            {"preparation_binding"},
        )
        envelope = json.loads(self.resolve_asset(binding_asset.asset_id).path.read_bytes())
        if (
            envelope.get("schema_version") != 1
            or envelope.get("operation_id") != str(row["operation_id"])
            or envelope.get("operation_fingerprint") != str(row["operation_fingerprint"])
            or envelope.get("graph", {}).get("asset_id") != str(row["graph_asset_id"])
            or envelope.get("graph", {}).get("sha256") != str(row["graph_sha256"])
            or envelope.get("source", {}).get("asset_id") != str(row["source_asset_id"])
            or envelope.get("cpu_input", {}).get("asset_id") != str(row["cpu_input_asset_id"])
            or envelope.get("prompt_sha256") != str(row["prompt_sha256"])
            or envelope.get("word_schedule_sha256") != str(row["word_schedule_sha256"])
        ):
            raise ValidationError("persisted binding envelope association mismatch")
        operation = self.get_operation(str(row["project_id"]), str(row["operation_id"]))
        manifest = json.loads(operation.canonical_json)
        graph_asset = self._protected_binding_asset(
            str(row["project_id"]), str(row["graph_asset_id"]), str(row["graph_sha256"]), {"managed_graph"}
        )
        source_asset = self._protected_binding_asset(
            str(row["project_id"]), str(row["source_asset_id"]), str(row["source_sha256"]), {"source"}
        )
        cpu_asset = self._protected_binding_asset(
            str(row["project_id"]), str(row["cpu_input_asset_id"]), str(row["cpu_input_sha256"]),
            {"cpu_input", "source"},
        )
        reference_ids = tuple(json.loads(str(row["reference_asset_ids_json"])))
        reference_hashes = json.loads(str(row["reference_sha256s_json"]))
        if len(reference_ids) != len(reference_hashes):
            raise ValidationError("preparation binding reference roles are malformed")
        reference_assets = []
        for asset_id, sha256 in zip(reference_ids, reference_hashes):
            reference_assets.append(self._protected_binding_asset(
                str(row["project_id"]), asset_id, sha256, {"reference_1", "reference_2"}
            ))
        actual_graph = json.loads(self.resolve_asset(graph_asset.asset_id).path.read_bytes())
        actual_semantic = hashlib.sha256(json.dumps(
            _effective_workflow(actual_graph), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")).hexdigest()
        actual_plan = json.loads(actual_graph["1189"]["inputs"]["plan"])
        expected_outputs = {
            "primary": f"openjutsu/{operation.managed_job_id}",
            "comparison": f"openjutsu/{operation.managed_job_id}_compare",
        }
        substitutions = envelope.get("substitutions")
        if (
            actual_semantic != manifest["graph"]["resolved_semantic_sha256"]
            or envelope.get("graph", {}).get("semantic_sha256") != actual_semantic
            or actual_plan["video"] != cpu_asset.filename
            or actual_plan["global_ref"] != reference_assets[0].filename
            or actual_plan["global_ref2"] != reference_assets[1].filename
            or substitutions != {
                "planner": {"video": actual_plan["video"], "global_ref": actual_plan["global_ref"],
                    "global_ref2": actual_plan["global_ref2"], "source_asset_id": cpu_asset.asset_id,
                    "reference_asset_ids": list(reference_ids)},
                "outputs": expected_outputs,
            }
            or json.dumps(substitutions, sort_keys=True, separators=(",", ":")) != str(row["substitutions_json"])
            or hashlib.sha256(str(envelope.get("prompt_content", "")).encode()).hexdigest() != str(row["prompt_sha256"])
            or hashlib.sha256(str(envelope.get("word_schedule_content", "")).encode()).hexdigest() != str(row["word_schedule_sha256"])
        ):
            raise ValidationError("persisted concrete graph, roles, outputs, or prompt bytes are invalid")
        if not (binding_asset.sha256 and graph_asset.sha256 and source_asset.sha256 and cpu_asset.sha256):
            raise ValidationError("preparation binding hashes are malformed")
        return BoundSubmission(
            str(row["operation_id"]), binding_asset.asset_id, binding_asset.sha256, False
        )

    def get_preparation_binding(self, project_id: str, operation_id: str) -> BoundSubmission:
        return self._revalidate_binding(self._binding_row(project_id, operation_id))

    def verify_preparation_binding(
        self,
        project_id: str,
        operation_id: str,
        operation_fingerprint: str,
        *,
        source_asset_id: str,
        reference_asset_ids: tuple[str, ...],
    ) -> BoundSubmission:
        row = self._binding_row(project_id, operation_id)
        reference_json = json.dumps(reference_asset_ids, separators=(",", ":"))
        if (
            str(row["operation_fingerprint"]) != operation_fingerprint
            or str(row["source_asset_id"]) != source_asset_id
            or str(row["reference_asset_ids_json"]) != reference_json
        ):
            raise ValidationError("preparation binding verification mismatch")
        return self._revalidate_binding(row)

    def create_project(self, name: str) -> ProjectRecord:
        safe_name = _text(name, "project name", maximum=200)
        project_id = uuid.uuid4().hex
        now = _timestamp()
        with self._transaction() as db:
            db.execute("INSERT INTO projects VALUES (?, ?, ?, ?)", (project_id, safe_name, now, now))
        return ProjectRecord(project_id, safe_name, now, now)
    def list_projects(self) -> list[ProjectRecord]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM projects ORDER BY created_at, project_id").fetchall()
        return [self._project(row) for row in rows]
    def get_project(self, project_id: str) -> ProjectRecord:
        self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        with self._connect() as db:
            row = db.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        if row is None:
            raise NotFoundError("project not found")
        return self._project(row)
    def register_asset(
        self, project_id: str, path: Path, role: str, *, protected: bool = False) -> AssetRecord:
        self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        safe_role = _text(role, "asset role", maximum=120)
        if not isinstance(path, Path):
            raise UnsafePathError("asset path must be a Path")
        asset_file = self._permitted_file(path)
        asset_id = uuid.uuid4().hex
        now = _timestamp()
        media_type = mimetypes.guess_type(asset_file.resolved_path.name)[0]
        with self._transaction() as db:
            self._require_project(db, project_id)
            db.execute("INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                asset_id, project_id, safe_role, asset_file.resolved_path.name,
                media_type, asset_file.size_bytes, asset_file.sha256, int(protected),
                now, asset_file.root_kind, asset_file.relative_path,
            ))
        return AssetRecord(asset_id, project_id, safe_role, asset_file.resolved_path.name,
                           media_type, asset_file.size_bytes, asset_file.sha256, protected, now)
    def stage_asset(
        self, project_id: str, filename: str, content: BinaryIO, *,
        role: str, protected: bool = False) -> AssetRecord:
        self.get_project(project_id)
        safe_role = _text(role, "asset role", maximum=120)
        if (not isinstance(filename, str) or not filename or filename in {".", ".."} or "/" in filename
                or "\\" in filename or "\x00" in filename or len(filename.encode("utf-8")) > 255
                or Path(filename).parts != (filename,)):
            raise ValidationError("staged filename must be a single safe filename component")

        staging_id = uuid.uuid4().hex
        staging_dir = self.uploads_root / staging_id
        staging_dir.mkdir()
        temporary = staging_dir / f".{staging_id}.tmp"
        destination = staging_dir / filename
        try:
            with temporary.open(mode="xb") as output:
                while chunk := content.read(1024 * 1024):
                    if not isinstance(chunk, bytes):
                        raise ValidationError("staged content must be binary")
                    output.write(chunk)
            os.replace(temporary, destination)
            return self.register_asset(project_id, destination, safe_role, protected=protected)
        except BaseException:
            self._remove_staging_directory(staging_dir)
            raise
    def resolve_asset(self, asset_id: str) -> ResolvedAsset:
        self._validate_id(asset_id, "asset", _ASSET_OR_PROJECT_ID)
        with self._connect() as db:
            row = db.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,)).fetchone()
        if row is None:
            raise NotFoundError("asset not found")
        record = self._asset(row)
        resolved = self._recorded_file(row["root_kind"], row["relative_path"])
        if record.protected:
            fingerprint, _ = _sha256(resolved)
            if fingerprint != record.sha256:
                raise AssetIntegrityError("protected asset bytes do not match the recorded fingerprint")
        return ResolvedAsset(record, resolved)
    def create_character_version(
        self, name: str, reference_asset_ids: list[str], description: str = "") -> CharacterVersionRecord:
        safe_name = _text(name, "character name", maximum=200)
        if not isinstance(description, str) or len(description) > 2000:
            raise ValidationError("character description must be text of at most 2000 characters")
        if not isinstance(reference_asset_ids, list) or not 1 <= len(reference_asset_ids) <= 2:
            raise ValidationError("character version requires one or two reference assets")
        for reference_asset_id in reference_asset_ids:
            self._validate_id(reference_asset_id, "asset", _ASSET_OR_PROJECT_ID)
        if len(set(reference_asset_ids)) != len(reference_asset_ids):
            raise ValidationError("character reference assets must be distinct")

        character_id = "char_" + hashlib.sha256(safe_name.strip().casefold().encode()).hexdigest()[:24]
        now = _timestamp()
        reference_json = json.dumps(reference_asset_ids, separators=(",", ":"))
        with self._transaction() as db:
            for reference_asset_id in reference_asset_ids:
                if db.execute("SELECT 1 FROM assets WHERE asset_id = ?", (reference_asset_id,)).fetchone() is None:
                    raise NotFoundError("character reference asset not found")
            row = db.execute("SELECT MAX(version) FROM character_versions WHERE character_id = ?", (character_id,)).fetchone()
            version = 1 if row[0] is None else int(row[0]) + 1
            db.execute("INSERT INTO character_versions VALUES (?, ?, ?, ?, ?, ?)",
                       (character_id, version, safe_name, description, reference_json, now))
        return CharacterVersionRecord(character_id, version, safe_name, description,
                                      list(reference_asset_ids), now)
    def get_character_version(self, character_id: str, version: int) -> CharacterVersionRecord:
        self._validate_id(character_id, "character", _CHARACTER_ID)
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise ValidationError("character version must be a positive integer")
        with self._connect() as db:
            row = db.execute("SELECT * FROM character_versions WHERE character_id = ? AND version = ?",
                             (character_id, version)).fetchone()
        if row is None:
            raise NotFoundError("character version not found")
        return self._character(row)
    def list_character_versions(self) -> list[CharacterVersionRecord]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM character_versions ORDER BY character_id, version").fetchall()
        return [self._character(row) for row in rows]
    def record_prepared_job(
        self, project_id: str, job_id: str, job_dir: Path,
        character_version: tuple[str, int] | None = None) -> PreparedConfigRecord:
        if project_id != _LEGACY_PROJECT_ID:
            self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        self._validate_id(job_id, "job", _EXTERNAL_ID)
        if character_version is not None:
            character = self.get_character_version(*character_version)
        prepared = self._prepared_artifacts(job_id, job_dir)
        now = _timestamp()
        reference_json = json.dumps(prepared["reference_sha256s"], separators=(",", ":"))
        config_json = json.dumps(prepared["config"], sort_keys=True, separators=(",", ":"))
        with self._transaction() as db:
            if project_id != _LEGACY_PROJECT_ID:
                self._require_project(db, project_id)
            db.execute("INSERT INTO prepared_configs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                project_id, job_id, character.character_id if character_version else None,
                character.version if character_version else None, prepared["seed"],
                prepared["workflow_sha256"], prepared["prompt_sha256"], prepared["source_sha256"],
                reference_json, config_json, now,
            ))
        return PreparedConfigRecord(project_id, job_id, character.character_id if character_version else None,
                                   character.version if character_version else None, int(prepared["seed"]),
                                   str(prepared["workflow_sha256"]), str(prepared["prompt_sha256"]),
                                   str(prepared["source_sha256"]), list(prepared["reference_sha256s"]),
                                   dict(prepared["config"]), now)
    def list_prepared_jobs(self, project_id: str) -> list[PreparedConfigRecord]:
        if project_id != _LEGACY_PROJECT_ID:
            self._validate_id(project_id, "project", _ASSET_OR_PROJECT_ID)
        with self._connect() as db:
            rows = db.execute("SELECT * FROM prepared_configs WHERE project_id = ? "
                              "ORDER BY created_at DESC, job_id DESC", (project_id,)).fetchall()
        return [self._prepared(row) for row in rows]
    @staticmethod
    def _validate_id(value: object, label: str, pattern: re.Pattern[str]) -> None:
        if not isinstance(value, str) or pattern.fullmatch(value) is None:
            raise ValidationError(f"malformed {label} ID")

    @staticmethod
    def _require_project(db: sqlite3.Connection, project_id: str) -> None:
        if db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,)).fetchone() is None:
            raise NotFoundError("project not found")

    def _aliases(self, name: str) -> tuple[Path, Path]:
        return self._caller_root / name, self.root / name

    @staticmethod
    def _within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    @staticmethod
    def _reject_symlink_components(path: Path, root: Path) -> None:
        current = path
        while True:
            if current.is_symlink():
                raise UnsafePathError("asset path contains a symlink")
            if current == root:
                return
            parent = current.parent
            if parent == current:
                raise UnsafePathError("asset path is outside a configured root")
            current = parent

    def _permitted_file(self, path: Path) -> _AssetFile:
        if not path.is_absolute():
            lexical = self.root / path
        else:
            lexical = path
        if ".." in lexical.parts:
            raise UnsafePathError("asset path traversal is not permitted")

        matched_alias: Path | None = None
        matched_root: Path | None = None
        matched_kind: str | None = None
        for kind in ("uploads", "imports"):
            resolved_root = self.uploads_root if kind == "uploads" else self.imports_root
            for alias in self._aliases(kind):
                if self._within(lexical, alias):
                    matched_alias = alias
                    matched_root = resolved_root
                    matched_kind = kind
                    break
            if matched_alias is not None:
                break
        if matched_alias is None or matched_root is None or matched_kind is None:
            raise UnsafePathError("asset path is outside a configured root")
        self._reject_symlink_components(lexical, matched_alias)

        try:
            resolved = lexical.resolve(strict=True)
            permitted = matched_root.resolve(strict=True)
            relative = resolved.relative_to(permitted).as_posix()
        except FileNotFoundError as error:
            raise NotFoundError("asset file not found") from error
        except (OSError, ValueError) as error:
            raise UnsafePathError("asset path leaves a configured root") from error
        if not resolved.is_file():
            raise UnsafePathError("asset path is not a regular file")
        fingerprint, size = self._stable_hash(resolved)
        return _AssetFile(matched_kind, relative, resolved, fingerprint, size)

    def _recorded_file(self, root_kind: str, relative_text: object) -> Path:
        relative = Path(relative_text) if isinstance(relative_text, str) else Path()
        if (root_kind not in {"uploads", "imports"} or not relative_text or relative.is_absolute()
                or any(part in {".", ".."} for part in relative.parts)):
            raise UnsafePathError("recorded asset location is malformed")
        return self._permitted_file(self.root / root_kind / relative).resolved_path

    def _stable_hash(self, path: Path) -> tuple[str, int]:
        try:
            before = path.stat()
            if not before.st_mode & 0o170000 == 0o100000:
                raise UnsafePathError("asset path is not a regular file")
            fingerprint, size = _sha256(path)
            after = path.stat()
        except OSError as error:
            raise WorkspaceStoreError("asset could not be read") from error
        if (
            size != before.st_size
            or size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ino != after.st_ino
        ):
            raise AssetIntegrityError("asset changed while being read")
        return fingerprint, size

    def _prepared_dir(self, job_id: str, job_dir: Path) -> Path:
        if not isinstance(job_dir, Path):
            raise UnsafePathError("prepared job path must be a Path")
        lexical = job_dir if job_dir.is_absolute() else self.root / job_dir
        if ".." in lexical.parts:
            raise UnsafePathError("prepared job path traversal is not permitted")
        alias = None
        resolved_jobs = self.root / "jobs"
        for candidate_alias in self._aliases("jobs"):
            if self._within(lexical, candidate_alias):
                alias = candidate_alias
                break
        if alias is None:
            raise UnsafePathError("prepared job path is outside the workspace jobs root")
        self._reject_symlink_components(lexical, alias)
        try:
            resolved_dir = lexical.resolve(strict=True)
            relative = resolved_dir.relative_to(resolved_jobs.resolve(strict=True))
        except (OSError, ValueError) as error:
            raise UnsafePathError("prepared job path is unsafe") from error
        if relative.as_posix() != job_id or not resolved_dir.is_dir():
            raise UnsafePathError("prepared job path does not match its job ID")
        return resolved_dir

    def _prepared_artifacts(self, job_id: str, job_dir: Path) -> dict[str, Any]:
        resolved_dir = self._prepared_dir(job_id, job_dir)
        payloads: dict[str, Any] = {}
        fingerprints: dict[str, str] = {}
        for filename in ("job.json", "workflow.json", "prompt.txt"):
            path = resolved_dir / filename
            self._reject_symlink_components(path, resolved_dir)
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(resolved_dir)
                if not resolved.is_file():
                    raise UnsafePathError("prepared job artifact is not a regular file")
                payloads[filename], fingerprints[filename] = self._json_or_text(resolved, filename)
            except FileNotFoundError as error:
                raise NotFoundError(f"prepared job artifact not found: {filename}") from error
            except (OSError, ValueError) as error:
                raise UnsafePathError("prepared job artifact path is unsafe") from error
        manifest = payloads["job.json"]
        if not isinstance(manifest, dict):
            raise ValidationError("prepared job manifest must be a JSON object")
        if manifest.get("job_id") != job_id or manifest.get("rights_attested") is not True:
            raise ValidationError("prepared job manifest does not match the requested job")
        seed = manifest.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValidationError("prepared job seed is malformed")
        if not isinstance(payloads["workflow.json"], dict):
            raise ValidationError("prepared workflow must be a JSON object")

        source_hash = self._manifest_fingerprint(manifest, "source")
        references: list[str] = []
        for key in ("reference_1", "reference_2"):
            value = manifest.get(key)
            if value is not None:
                references.append(self._manifest_fingerprint(manifest, key))
        return {
            "seed": seed,
            "workflow_sha256": fingerprints["workflow.json"],
            "prompt_sha256": fingerprints["prompt.txt"],
            "source_sha256": source_hash,
            "reference_sha256s": references,
            "config": self._workflow_config(payloads["workflow.json"], seed),
        }

    @staticmethod
    def _workflow_config(workflow: dict[str, Any], seed: int) -> dict[str, Any]:
        """Select known runtime metadata, never copy an uploaded graph."""
        try:
            plan = json.loads(workflow["1189"]["inputs"]["plan"])
            references = [plan["global_ref"]]
            if plan["global_ref2"] != "":
                references.append(plan["global_ref2"])
            config = {
                "audio_mode": plan["audio_mode"],
                "reference_names": references,
                "scheduler_steps": workflow["181"]["inputs"]["steps"],
                "seed": workflow["13"]["inputs"]["noise_seed"],
                "video_name": plan["video"],
                "with_audio": workflow["1177"]["inputs"]["with_audio"],
            }
        except (KeyError, TypeError, ValueError) as error:
            raise ValidationError("prepared workflow metadata is malformed") from error
        return WorkspaceStore._safe_config(config, seed)

    @staticmethod
    def _safe_config(config: object, seed: object) -> dict[str, Any]:
        """Fail closed on old full-graph rows and malformed selected values."""
        keys = ("audio_mode", "reference_names", "scheduler_steps", "seed", "video_name", "with_audio")
        if not isinstance(config, dict) or any(key not in config for key in keys):
            raise ValidationError("prepared config metadata is malformed")
        references = WorkspaceStore._config_filenames(config["video_name"], config["reference_names"])
        if (type(seed) is not int or type(config["seed"]) is not int or config["seed"] != seed
                or type(config["scheduler_steps"]) is not int
                or type(config["with_audio"]) is not bool or config["audio_mode"] != "auto"):
            raise ValidationError("prepared config settings are malformed")
        return {key: list(references) if key == "reference_names" else config[key] for key in keys}

    @staticmethod
    def _config_filenames(video: object, references: object) -> list[str]:
        if not isinstance(references, list) or not 1 <= len(references) <= 2:
            raise ValidationError("prepared config references are malformed")
        for name in [video, *references]:
            if (not isinstance(name, str) or not name or name in {".", ".."}
                    or Path(name).name != name or "\\" in name or "\0" in name):
                raise ValidationError("prepared config filenames are malformed")
        return list(references)

    def _json_or_text(self, path: Path, filename: str) -> tuple[Any, str]:
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise WorkspaceStoreError("prepared job artifact could not be read") from error
        fingerprint = hashlib.sha256(raw).hexdigest()
        if filename == "prompt.txt":
            return raw.decode("utf-8"), fingerprint
        try:
            return json.loads(raw), fingerprint
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError(f"prepared job artifact is malformed: {filename}") from error

    def _manifest_fingerprint(self, manifest: dict[str, Any], key: str) -> str:
        value = manifest.get(key)
        if not isinstance(value, str) or not value:
            raise ValidationError(f"prepared job manifest has no {key} path")
        return self._permitted_file(Path(value)).sha256

    @staticmethod
    def _remove_staging_directory(directory: Path) -> None:
        try:
            for child in directory.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink()
            directory.rmdir()
        except OSError:
            return None

    @staticmethod
    def _project(row: sqlite3.Row) -> ProjectRecord:
        return ProjectRecord(str(row["project_id"]), str(row["name"]), str(row["created_at"]), str(row["updated_at"]))

    @staticmethod
    def _asset(values: sqlite3.Row | dict[str, Any]) -> AssetRecord:
        return AssetRecord(str(values["asset_id"]), str(values["project_id"]), str(values["role"]),
                           str(values["filename"]), values["media_type"], int(values["size_bytes"]),
                           str(values["sha256"]), bool(values["protected"]), str(values["created_at"]))

    @staticmethod
    def _character(row: sqlite3.Row) -> CharacterVersionRecord:
        return CharacterVersionRecord(str(row["character_id"]), int(row["version"]), str(row["name"]),
                                      str(row["description"]), list(json.loads(str(row["reference_asset_ids"]))),
                                      str(row["created_at"]))

    @staticmethod
    def _prepared(row: sqlite3.Row) -> PreparedConfigRecord:
        try:
            config = json.loads(row["config_json"])
        except (TypeError, ValueError) as error:
            raise ValidationError("prepared config metadata is malformed") from error
        config = WorkspaceStore._safe_config(config, row["seed"])
        return PreparedConfigRecord(str(row["project_id"]), str(row["job_id"]),
            str(row["character_id"]) if row["character_id"] is not None else None,
            int(row["character_version"]) if row["character_version"] is not None else None,
            int(row["seed"]), str(row["workflow_sha256"]), str(row["prompt_sha256"]),
            str(row["source_sha256"]) if row["source_sha256"] is not None else None,
            list(json.loads(str(row["reference_sha256s"]))), config,
            str(row["created_at"]))

    @staticmethod
    def _scene(row: sqlite3.Row, shot_rows: list[sqlite3.Row]) -> SceneRevision:
        source = SourceTiming(
            asset_id=str(row["source_asset_id"]),
            sha256=str(row["source_sha256"]),
            frame_count=int(row["frame_count"]),
            timebase=Timebase(int(row["timebase_num"]), int(row["timebase_den"])),
            cfr=bool(row["cfr"]),
            has_audio=bool(row["has_audio"]),
        )
        shots = tuple(
            ShotSpec(
                id=str(shot["shot_id"]),
                source_range={"start": int(shot["start_frame"]), "end": int(shot["end_frame"])},
                kind=str(shot["kind"]),
            )
            for shot in shot_rows
        )
        return SceneRevision(
            id=str(row["scene_revision_id"]),
            project_id=str(row["project_id"]),
            source=source,
            shots=shots,
            revision=int(row["revision"]),
        )
