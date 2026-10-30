# SPDX-License-Identifier: MIT
"""Typed HTTP boundary for M1 source upload and immutable scene confirmation."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal
from fractions import Fraction

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator
from fastapi.responses import JSONResponse

from openjutsu.m1_types import (
    AudioPolicy, EditItem, ExecutionMode, FrameRange, RecipePin, ShotSpec,
    Timebase, WordTiming, dto_json,
)
from openjutsu.attempt_service import AttemptService
from openjutsu.edit_service import EditService
from openjutsu.recipe_service import RecipeResolutionError, RecipeService, recipe_catalog
from openjutsu.scene_service import SceneService, SceneServiceError, UnsupportedSourceError
from openjutsu.m1_types import ReplayReceipt, ReviewVerdict, WindowMap
from openjutsu.take_service import TakeService
from openjutsu.workspace_store import (
    AssetIntegrityError,
    AttemptConflictError,
    NotFoundError,
    UnsafePathError,
    ValidationError,
    WorkspaceStore,
    WorkspaceStoreError,
)


def _active_store(request: Request, default: WorkspaceStore) -> WorkspaceStore:
    active = getattr(request.app.state, "workspace_store", None)
    return active if isinstance(active, WorkspaceStore) else default


def _error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(
        error,
        (
            ValidationError,
            UnsafePathError,
            SceneServiceError,
            RecipeResolutionError,
            ValueError,
        ),
    ):
        return HTTPException(status_code=422, detail=str(error))
    if isinstance(error, AssetIntegrityError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=503, detail="Managed scene operation failed.")


def _service(store: WorkspaceStore, ffprobe: str) -> SceneService:
    try:
        return SceneService(store, ffprobe=ffprobe)
    except WorkspaceStoreError as error:
        raise _error(error) from error


def _comparison_geometry(window: WindowMap) -> tuple[int, int, int, int, str]:
    """Return the immutable typed-window source/decoder projection for FFmpeg."""
    TakeService._validated_window(window)
    rate = Fraction(window.source_timebase.den, window.source_timebase.num)
    return (
        window.source_range.start, window.source_range.end,
        window.decoder_keep.start, window.decoder_keep.end,
        f"{rate.numerator}/{rate.denominator}",
    )


def _comparison_window(store: WorkspaceStore, take: object) -> WindowMap:
    from openjutsu.m1_types import TakeRecord
    if not isinstance(take, TakeRecord) or take.scene_revision_id is None:
        raise ValidationError("comparison requires an attached take")
    with store._connect() as db:
        row = db.execute(
            """SELECT window_json FROM qualified_replay_receipts
               WHERE take_id=? AND project_id=? AND scene_revision_id=? AND shot_id=?""",
            (take.id, take.project_id, take.scene_revision_id, take.shot_id),
        ).fetchone()
    if row is None:
        if take.operation_id is None or take.origin != "dry_run":
            raise ValidationError("attached take lacks immutable qualified window authority")
        operation = store.get_operation(take.project_id, take.operation_id)
        if (operation.scene_revision_id, operation.shot_id) != (
            take.scene_revision_id, take.shot_id
        ):
            raise ValidationError("comparison operation scope mismatch")
        return operation.window
    if take.operation_id is None:
        raise ValidationError(
            "EVIDENCE_UNAVAILABLE: NULL-operation carrier storage is not a "
            "trusted historical comparison verifier"
        )
    try:
        carrier_window = WindowMap.from_json(str(row["window_json"]))
    except (TypeError, ValueError) as error:
        raise ValidationError("qualified replay window authority is malformed") from error
    if take.operation_id is None:
        return carrier_window
    operation = store.get_operation(take.project_id, take.operation_id)
    if (operation.scene_revision_id, operation.shot_id) != (
        take.scene_revision_id, take.shot_id
    ) or operation.window != carrier_window:
        raise ValidationError("comparison operation and carrier windows disagree")
    return carrier_window


class RecipePinPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    recipe_id: StrictStr = Field(min_length=1, max_length=128)
    version: StrictStr = Field(min_length=1, max_length=128)
    raw_graph_sha256: StrictStr = Field(min_length=64, max_length=64, pattern=r"[0-9a-f]{64}")
    profile_id: StrictStr = Field(min_length=1, max_length=128)
    adapter_version: StrictStr = Field(min_length=1, max_length=128)
    endpoint_fingerprint: StrictStr = Field(min_length=64, max_length=64, pattern=r"[0-9a-f]{64}")


class WordTimingIntervalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    start: float
    end: float
    word: StrictStr


class WordTimingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_asset_id: StrictStr
    source_sha256: StrictStr
    words: list[WordTimingIntervalPayload]

    @model_validator(mode="before")
    @classmethod
    def validate_domain(cls, value: Any) -> dict[str, Any]:
        try:
            return dto_json(WordTiming.from_json(value))
        except (TypeError, ValueError, OverflowError) as error:
            # Do not reflect malformed text or non-JSON finite numbers in errors.
            raise HTTPException(422, "Invalid word timing payload") from error


class ResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_revision_id: StrictStr = Field(min_length=1, max_length=128)
    shot_id: StrictStr = Field(min_length=1, max_length=128)
    pin: RecipePinPayload
    character_version: tuple[StrictStr, StrictInt]
    seed: StrictInt = Field(ge=0, le=2**53 - 1)
    rights_attested: StrictBool = False
    word_timing: WordTimingPayload | None = None


class AuthorizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: StrictStr = Field(min_length=1, max_length=128)
    client_request_id: StrictStr = Field(min_length=1, max_length=128)
    mode: Literal["dry_run", "retained_replay", "comfy", "sdk"]
    challenger_of: StrictStr | None = None


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    verdict: Literal["keeper", "reject", "needs_review"]
    note: StrictStr = Field(min_length=1, max_length=4000)


class SelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    take_id: StrictStr | None = None
    expected_revision: StrictInt = Field(ge=0)


class FrameRangePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    start: StrictInt = Field(ge=0)
    end: StrictInt = Field(gt=0)


class EditItemPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    shot_id: StrictStr = Field(min_length=1, max_length=128)
    take_id: StrictStr | None = Field(default=None, min_length=1, max_length=128)
    source_range: FrameRangePayload
    decoder_keep: FrameRangePayload | None = None
    timeline_range: FrameRangePayload


class TimebasePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    num: StrictInt = Field(ge=1)
    den: StrictInt = Field(ge=1)


class EditRevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scene_revision_id: StrictStr = Field(min_length=1, max_length=128)
    items: list[EditItemPayload] = Field(min_length=1)
    audio: Literal["source_edit_map", "mute", "source_stream_copy"]
    timebase: TimebasePayload | None = None


def _attempt_error(error: Exception) -> HTTPException:
    # No raw exception, path, credentials, transport body, or arbitrary event payload.
    status, code = (503, "ATTEMPT_UNAVAILABLE")
    if isinstance(error, NotFoundError):
        status, code = 404, "ATTEMPT_OR_OPERATION_NOT_FOUND"
    elif isinstance(error, (AttemptConflictError, AssetIntegrityError)):
        status, code = 409, "ATTEMPT_CONFLICT"
    elif isinstance(error, (ValidationError, ValueError)):
        status, code = 422, "INVALID_ATTEMPT_REQUEST"
    return HTTPException(status_code=status, detail=code)


def create_m1_router(store: WorkspaceStore, *, ffprobe: str = "ffprobe") -> APIRouter:
    """Mount the active-store M1 scene API without exposing local paths."""
    router = APIRouter()

    @router.post("/api/projects/{project_id}/attempts")
    def authorize_attempt(project_id: str, request: Request, payload: AuthorizeRequest) -> JSONResponse:
        active = _active_store(request, store)
        try:
            operation = active.get_operation(project_id, payload.operation_id)
            attempt, created = active._authorize_attempt(operation, payload.client_request_id,
                ExecutionMode(payload.mode), payload.challenger_of)
        except (WorkspaceStoreError, ValueError) as error:
            raise _attempt_error(error) from error
        return JSONResponse(dto_json(attempt), status_code=201 if created else 200)

    @router.get("/api/projects/{project_id}/attempts")
    def list_attempts(project_id: str, request: Request) -> JSONResponse:
        try:
            return JSONResponse([dto_json(item) for item in _active_store(request, store).list_attempts(project_id)])
        except WorkspaceStoreError as error:
            raise _attempt_error(error) from error

    @router.post("/api/projects/{project_id}/attempts/{attempt_id}/{action}")
    def control_attempt(project_id: str, attempt_id: str, action: Literal["cancel", "reconcile"],
                        request: Request) -> JSONResponse:
        active = _active_store(request, store)
        try:
            active.get_attempt(project_id, attempt_id)
            service = AttemptService(active)
            result = service.request_cancel(attempt_id) if action == "cancel" else service.reconcile(attempt_id)
        except (WorkspaceStoreError, ValueError) as error:
            raise _attempt_error(error) from error
        return JSONResponse(dto_json(result))

    @router.post("/api/projects/{project_id}/sources")
    async def upload_source(
        project_id: str,
        request: Request,
        file: UploadFile = File(...),
    ) -> JSONResponse:
        active = _active_store(request, store)
        filename = file.filename or ""
        if not filename:
            raise HTTPException(status_code=422, detail="A source video file is required.")
        try:
            active.get_project(project_id)
            staged = active.stage_asset(
                project_id,
                filename,
                file.file,
                role="source",
                protected=True,
            )
            timing = _service(active, ffprobe).probe_source(staged.asset_id)
        except (WorkspaceStoreError, SceneServiceError) as error:
            raise _error(error) from error
        finally:
            await file.close()
        return JSONResponse(dto_json(timing), status_code=201)

    @router.get("/api/projects/{project_id}/scenes")
    async def list_scenes(project_id: str, request: Request) -> JSONResponse:
        active = _active_store(request, store)
        try:
            scenes = active.list_scene_revisions(project_id)
        except WorkspaceStoreError as error:
            raise _error(error) from error
        return JSONResponse([dto_json(scene) for scene in scenes])

    @router.post("/api/projects/{project_id}/scenes")
    async def confirm_scene(project_id: str, request: Request, payload: dict[str, Any]) -> JSONResponse:
        active = _active_store(request, store)
        source_asset_id = payload.get("source_asset_id")
        raw_shots = payload.get("shots")
        if not isinstance(source_asset_id, str):
            raise HTTPException(status_code=422, detail="source_asset_id is required.")
        if not isinstance(raw_shots, list) or not raw_shots:
            raise HTTPException(status_code=422, detail="shots must be a non-empty array.")
        shots: list[ShotSpec] = []
        for index, raw_shot in enumerate(raw_shots):
            try:
                shots.append(ShotSpec.from_json(raw_shot))
            except (TypeError, ValueError) as error:
                raise HTTPException(
                    status_code=422,
                    detail=f"shots[{index}] is invalid: {error}",
                ) from error
        try:
            scene = _service(active, ffprobe).confirm_shots(
                project_id,
                source_asset_id,
                tuple(shots),
            )
        except (WorkspaceStoreError, SceneServiceError) as error:
            raise _error(error) from error
        return JSONResponse(dto_json(scene), status_code=201)

    @router.get("/api/projects/{project_id}/recipes")
    async def recipes(project_id: str, request: Request) -> JSONResponse:
        active = _active_store(request, store)
        try:
            active.get_project(project_id)
        except WorkspaceStoreError as error:
            raise _error(error) from error
        return JSONResponse(recipe_catalog())

    @router.post("/api/projects/{project_id}/operations/resolve")
    async def resolve_operation(
        project_id: str, request: Request, payload: ResolveRequest
    ) -> JSONResponse:
        active = _active_store(request, store)
        try:
            pin = RecipePin(
                payload.pin.recipe_id,
                payload.pin.version,
                payload.pin.raw_graph_sha256,
                payload.pin.profile_id,
                payload.pin.adapter_version,
                payload.pin.endpoint_fingerprint,
            )
            operation = RecipeService(active).resolve(
                project_id,
                payload.scene_revision_id,
                payload.shot_id,
                pin,
                payload.character_version,
                payload.seed,
                rights_attested=payload.rights_attested,
                word_timing=(WordTiming.from_json(payload.word_timing.model_dump())
                             if payload.word_timing is not None else None),
            )
        except (ValueError, WorkspaceStoreError, RecipeResolutionError) as error:
            raise _error(error) from error
        return JSONResponse(dto_json(operation), status_code=201)

    @router.post("/api/projects/{project_id}/replay-import")
    async def replay_import(project_id: str, request: Request) -> JSONResponse:
        active = _active_store(request, store)
        form = await request.form()
        items = form.multi_items()
        if (len(items) != 2 or [name for name, _value in items].count("file") != 1
                or [name for name, _value in items].count("receipt") != 1):
            raise HTTPException(status_code=422, detail="Exactly one file and one receipt part are required.")
        values = {name: value for name, value in items}
        upload = values.get("file")
        receipt_text = values.get("receipt")
        if (not callable(getattr(upload, "read", None)) or not getattr(upload, "filename", "")
                or not isinstance(receipt_text, str)):
            raise HTTPException(status_code=422, detail="Replay file and strict UTF-8 receipt are required.")
        try:
            receipt = ReplayReceipt.from_json(receipt_text)
            take = TakeService(active).import_replay(project_id, receipt, upload.file)
        except (WorkspaceStoreError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
            raise _error(error) from error
        finally:
            await upload.close()
        return JSONResponse(dto_json(take), status_code=201)

    @router.post("/api/projects/{project_id}/unqualified-import")
    async def unqualified_import(project_id: str, request: Request) -> JSONResponse:
        active = _active_store(request, store)
        form = await request.form()
        items = form.multi_items()
        names = [name for name, _value in items]
        if len(items) != 2 or names.count("file") != 1 or names.count("shot_id") != 1:
            raise HTTPException(status_code=422, detail="Exactly one file and one shot_id part are required; historical metadata is forbidden.")
        values = {name: value for name, value in items}
        upload = values.get("file")
        shot_id = values.get("shot_id")
        if (not callable(getattr(upload, "read", None)) or not getattr(upload, "filename", "")
                or not isinstance(shot_id, str) or not shot_id):
            raise HTTPException(status_code=422, detail="Binary file and strict UTF-8 shot_id are required.")
        try:
            take = TakeService(active).import_unqualified(
                project_id, shot_id, None, upload.file
            )
        except (WorkspaceStoreError, ValueError, UnicodeError) as error:
            raise _error(error) from error
        finally:
            await upload.close()
        return JSONResponse(dto_json(take), status_code=201)

    @router.get("/api/projects/{project_id}/scene-revisions/{scene_revision_id}/takes")
    def list_attached_takes(
        project_id: str, scene_revision_id: str, shot_id: str, request: Request
    ) -> JSONResponse:
        active = _active_store(request, store)
        try:
            takes = active.list_attached_takes(project_id, scene_revision_id, shot_id)
        except WorkspaceStoreError as error:
            raise _error(error) from error
        return JSONResponse([dto_json(take) for take in takes])

    @router.get("/api/projects/{project_id}/takes/unqualified")
    def list_unqualified_takes(project_id: str, request: Request) -> JSONResponse:
        active = _active_store(request, store)
        try:
            takes = active.list_unqualified_takes(project_id)
        except WorkspaceStoreError as error:
            raise _error(error) from error
        return JSONResponse([dto_json(take) for take in takes])

    @router.get("/api/projects/{project_id}/takes/{take_id}/comparison")
    def comparison_video(project_id: str, take_id: str, request: Request) -> Response:
        active = _active_store(request, store)
        try:
            take = active.get_take(project_id, take_id)
            scene = active.get_scene_revision(project_id, str(take.scene_revision_id))
            source = active.resolve_asset(scene.source.asset_id)
            output = active.resolve_asset(take.output.asset_id)
            shot = next((item for item in scene.shots if item.id == take.shot_id), None)
            window = _comparison_window(active, take)
            if shot is None or window.source_range != shot.source_range:
                raise ValidationError("typed comparison window does not match the scene shot")
            authority_pin = (
                active.get_operation(take.project_id, take.operation_id).pin
                if take.operation_id is not None else None
            )
            TakeService._validated_current_cpu_window(
                active, shot, window, pin=authority_pin
            )
            if take.output.frame_count != window.expected_decoder_frames:
                raise ValidationError("typed comparison output decoder count mismatch")
            if take.output.timebase != window.render_timebase:
                raise ValidationError("typed comparison output timebase mismatch")
            start, end, keep_start, keep_end, rate = _comparison_geometry(window)
            with tempfile.TemporaryDirectory(prefix="comparison-") as temporary_directory:
                comparison_path = Path(temporary_directory) / "comparison.mp4"
                video = subprocess.run(
                    ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(source.path),
                     "-i", str(output.path), "-filter_complex",
                     f"[0:v]trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS,"
                     f"fps={rate}[source];"
                     f"[1:v]trim=start_frame={keep_start}:end_frame={keep_end},"
                     f"setpts=PTS-STARTPTS,fps={rate}[candidate];"
                     f"[source][candidate]hstack[v]",
                     "-map", "[v]", "-frames:v", str(end - start), "-c:v", "libx264",
                     "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", str(comparison_path)],
                    check=True, capture_output=True, timeout=30,
                )
                video_bytes = comparison_path.read_bytes()
        except (WorkspaceStoreError, ValueError, subprocess.SubprocessError, OSError) as error:
            raise _error(error) from error
        return Response(video_bytes, media_type="video/mp4")

    @router.post("/takes/{take_id}/reviews")
    def review_take(take_id: str, payload: ReviewRequest, request: Request) -> JSONResponse:
        try:
            record = TakeService(_active_store(request, store)).review(
                take_id, ReviewVerdict(payload.verdict), payload.note
            )
        except (WorkspaceStoreError, ValueError) as error:
            raise _error(error) from error
        return JSONResponse(dto_json(record), status_code=201)

    @router.put("/api/projects/{project_id}/scene-revisions/{scene_revision_id}/shots/{shot_id}/selection")
    def select_take(
        project_id: str, scene_revision_id: str, shot_id: str,
        payload: SelectionRequest,
        request: Request,
    ) -> JSONResponse:
        try:
            record = TakeService(_active_store(request, store)).select(
                project_id, scene_revision_id, shot_id, payload.take_id,
                payload.expected_revision,
            )
        except (WorkspaceStoreError, ValueError) as error:
            error_value = _error(error)
            if isinstance(error, AttemptConflictError):
                error_value.status_code = 409
                error_value.detail = "SELECTION_REVISION_CONFLICT"
            raise error_value from error
        return JSONResponse(dto_json(record))

    @router.post("/api/projects/{project_id}/edit-revisions")
    def create_edit_revision(
        project_id: str, payload: EditRevisionRequest, request: Request
    ) -> JSONResponse:
        active = _active_store(request, store)
        try:
            scene = active.get_scene_revision(project_id, payload.scene_revision_id)
            if payload.timebase is not None:
                requested_timebase = Timebase(payload.timebase.num, payload.timebase.den)
                if requested_timebase != scene.source.timebase:
                    raise ValidationError("edit timebase must match the frozen scene source")
            items = tuple(
                EditItem(
                    item.shot_id, item.take_id,
                    FrameRange(item.source_range.start, item.source_range.end),
                    None if item.decoder_keep is None else FrameRange(
                        item.decoder_keep.start, item.decoder_keep.end),
                    FrameRange(item.timeline_range.start, item.timeline_range.end),
                ) for item in payload.items
            )
            revision = EditService(active).create_revision(
                project_id, payload.scene_revision_id, items, AudioPolicy(payload.audio)
            )
        except (WorkspaceStoreError, ValueError) as error:
            raise _error(error) from error
        return JSONResponse(dto_json(revision), status_code=201)

    @router.post("/edit-revisions/{revision_id}/exports")
    def export_edit_revision(revision_id: str, request: Request) -> JSONResponse:
        active = _active_store(request, store)
        try:
            exported = EditService(active).export_revision(revision_id)
        except (WorkspaceStoreError, ValueError, subprocess.SubprocessError, OSError) as error:
            raise _error(error) from error
        return JSONResponse(dto_json(exported), status_code=200)

    @router.get("/exports/{export_id}")
    def get_export(export_id: str, request: Request) -> JSONResponse:
        active = _active_store(request, store)
        try:
            revision = active.get_edit_revision_by_id(
                active._export_revision_id(export_id)
            )
            exported = active.get_export(revision.project_id, export_id)
        except WorkspaceStoreError as error:
            raise _error(error) from error
        return JSONResponse(dto_json(exported))

    @router.get("/exports/{export_id}/artifact")
    def export_artifact(export_id: str, request: Request) -> Response:
        active = _active_store(request, store)
        try:
            revision = active.get_edit_revision_by_id(
                active._export_revision_id(export_id)
            )
            exported = active.get_export(revision.project_id, export_id)
            if exported.state != "completed" or exported.asset_id is None:
                raise ValidationError("export artifact is unavailable")
            content = active.resolve_asset(exported.asset_id).path.read_bytes()
        except (WorkspaceStoreError, OSError) as error:
            raise _error(error) from error
        return Response(
            content, media_type="video/mp4",
            headers={"Content-Disposition": 'attachment; filename="managed-edit-export.mp4"'},
        )

    return router
