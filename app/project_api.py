# SPDX-License-Identifier: MIT
"""Safe HTTP projections for saved RecastRoom projects and characters."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from openjutsu.workspace_store import (
    AssetIntegrityError,
    CharacterVersionRecord,
    NotFoundError,
    UnsafePathError,
    ValidationError,
    WorkspaceStore,
    WorkspaceStoreError,
)


class ProjectCreate(BaseModel):
    name: str


_REFERENCE_SUFFIXES = {".jpeg", ".jpg", ".png"}
_REFERENCE_TYPES = {"image/jpeg", "image/png"}
_SIGNATURES = ((b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))


def _record(record: object) -> dict[str, object]:
    return asdict(record)  # type: ignore[arg-type]


def _store_error(error: WorkspaceStoreError) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, AssetIntegrityError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, (ValidationError, UnsafePathError)):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=503, detail="Workspace store operation failed.")


async def _active_store(request: Request, default: WorkspaceStore) -> WorkspaceStore:
    override = getattr(request.app.state, "workspace_store", None)
    return override if isinstance(override, WorkspaceStore) else default


def _character_payload(
    store: WorkspaceStore, character: CharacterVersionRecord
) -> dict[str, object]:
    references: list[dict[str, object]] = []
    for asset_id in character.reference_asset_ids:
        references.append(_record(store.resolve_asset(asset_id).record))
    return {"character": _record(character), "references": references}


def _prepared_payload(record: object) -> dict[str, object]:
    payload = _record(record)
    job_id = str(payload["job_id"])
    payload["workflow_url"] = f"/api/jobs/{job_id}/workflow"
    payload["prompt_url"] = f"/api/jobs/{job_id}/prompt"
    return payload


def _validated_reference(upload: UploadFile, field: str) -> str:
    filename = upload.filename or ""
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_type = (upload.content_type or "").split(";", 1)[0].lower()
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=422, detail=f"{field} must be a single safe filename")
    if f".{suffix}" not in _REFERENCE_SUFFIXES or content_type not in _REFERENCE_TYPES:
        raise HTTPException(status_code=422, detail=f"{field} must be a PNG or JPEG image")
    try:
        prefix = upload.file.read(8)
        upload.file.seek(0)
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"{field} could not be read") from error
    if not any(prefix.startswith(signature) for signature, _kind in _SIGNATURES):
        raise HTTPException(status_code=422, detail=f"{field} image bytes do not match PNG or JPEG")
    return filename


def create_project_router(store: WorkspaceStore) -> APIRouter:
    """Build the same-app project API around one public WorkspaceStore."""
    router = APIRouter()

    @router.post("/api/projects")
    async def create_project(payload: ProjectCreate, request: Request) -> dict[str, object]:
        active = await _active_store(request, store)
        try:
            return _record(active.create_project(payload.name))
        except WorkspaceStoreError as error:
            raise _store_error(error) from error

    @router.get("/api/projects")
    async def list_projects(request: Request) -> dict[str, object]:
        active = await _active_store(request, store)
        try:
            return {"projects": [_record(item) for item in active.list_projects()]}
        except WorkspaceStoreError as error:
            raise _store_error(error) from error

    @router.get("/api/projects/{project_id}")
    async def get_project(project_id: str, request: Request) -> dict[str, object]:
        active = await _active_store(request, store)
        try:
            return _record(active.get_project(project_id))
        except WorkspaceStoreError as error:
            raise _store_error(error) from error

    @router.get("/api/projects/{project_id}/jobs")
    async def list_project_jobs(project_id: str, request: Request) -> dict[str, object]:
        active = await _active_store(request, store)
        try:
            active.get_project(project_id)
            jobs = [_prepared_payload(item) for item in active.list_prepared_jobs(project_id)]
            return {"project_id": project_id, "jobs": jobs}
        except WorkspaceStoreError as error:
            raise _store_error(error) from error

    @router.post("/api/characters")
    async def create_character(
        request: Request,
        project_id: str = Form(...),
        name: str = Form(...),
        reference_1: UploadFile = File(...),
        reference_2: UploadFile | None = File(None),
        description: str = Form(""),
    ) -> dict[str, object]:
        active = await _active_store(request, store)
        first_name = _validated_reference(reference_1, "reference_1")
        second_name = (
            _validated_reference(reference_2, "reference_2")
            if reference_2 is not None and reference_2.filename
            else None
        )
        try:
            active.get_project(project_id)
            first = active.stage_asset(
                project_id, first_name, reference_1.file, role="reference_1", protected=True
            )
            second = None
            if second_name is not None and reference_2 is not None:
                second = active.stage_asset(
                    project_id,
                    second_name,
                    reference_2.file,
                    role="reference_2",
                    protected=True,
                )
            reference_ids = [first.asset_id] if second is None else [first.asset_id, second.asset_id]
            character = active.create_character_version(
                name,
                reference_ids,
                description,
            )
            return _character_payload(active, character)
        except WorkspaceStoreError as error:
            raise _store_error(error) from error

    @router.get("/api/characters")
    async def list_characters(request: Request) -> dict[str, object]:
        active = await _active_store(request, store)
        try:
            return {"characters": [_character_payload(active, item) for item in active.list_character_versions()]}
        except WorkspaceStoreError as error:
            raise _store_error(error) from error

    @router.get("/api/characters/{character_id}/versions/{version}")
    async def get_character(
        character_id: str, version: int, request: Request
    ) -> dict[str, object]:
        active = await _active_store(request, store)
        try:
            return _character_payload(active, active.get_character_version(character_id, version))
        except WorkspaceStoreError as error:
            raise _store_error(error) from error

    @router.get("/api/assets/{asset_id}")
    async def get_asset(asset_id: str, request: Request) -> FileResponse:
        active = await _active_store(request, store)
        try:
            resolved = active.resolve_asset(asset_id)
        except WorkspaceStoreError as error:
            raise _store_error(error) from error
        media_type = resolved.record.media_type
        if media_type not in _REFERENCE_TYPES:
            return FileResponse(
                resolved.path,
                media_type="application/octet-stream",
                headers={"Content-Disposition": "attachment; filename=reference-asset"},
            )
        return FileResponse(resolved.path, media_type=media_type)

    return router
