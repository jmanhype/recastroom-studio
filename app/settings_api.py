# SPDX-License-Identifier: MIT
"""Runtime renderer connection endpoints: view, plain-language test, save and use.

Secrets never come back to the browser: the API key is reported only as a
boolean and a last-characters hint. Connectivity failures are plain-language
answers, never HTTP errors, so the settings screen can always show a verdict.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from openjutsu.config import Settings, SUPPORTED_BACKENDS
from openjutsu.connection_store import (
    ConnectionFileError,
    load_connection,
    locked_fields,
    merge_current,
    save_connection,
    validate_connection,
)
from openjutsu.readiness import renderer_readiness

ACTIVE_STATES = frozenset({"queued", "uploading", "generating", "downloading"})
_KEY_HINT_LENGTH = 4
CONNECTION_VIEW_NAME = "connection.json"


class ConnectionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: str | None = None
    comfy_url: str | None = None
    comfy_api_key: str | None = None


def _editable_values(payload: dict) -> dict[str, str]:
    """Drop empty values and fields the launch environment has locked."""
    locked = locked_fields(os.environ)
    return {
        key: value
        for key, value in payload.items()
        if key not in locked and value not in (None, "")
    }


def _key_hint(key: str | None) -> str | None:
    if not key:
        return None
    return "…" + key[-_KEY_HINT_LENGTH:]


def _effective(base: Settings, data_dir: Path) -> Settings:
    return merge_current(base, data_dir, os.environ)


def _readiness_for(backend: str, comfy_url: str, api_key: str | None) -> dict:
    if backend == "sdk":
        if not api_key:
            return {
                "ok": False,
                "code": "sdk_missing_api_key",
                "message": "The official Comfy SDK needs an API key before it can run.",
            }
        return {
            "ok": True,
            "code": "sdk_configured",
            "message": "The official Comfy SDK is configured with an API key. Reachability is verified on the first run.",
        }
    readiness = renderer_readiness(backend, comfy_url).as_dict()
    return {"ok": bool(readiness["ready"]), "code": readiness["code"], "message": readiness["message"]}


def _view(base: Settings, data_dir: Path) -> dict:
    saved = load_connection(data_dir)
    effective = _effective(base, data_dir)
    locked = locked_fields(os.environ)
    fields: dict[str, dict] = {}
    for name in ("backend", "comfy_url"):
        if name in locked:
            source = "environment"
        elif name in saved:
            source = "saved"
        else:
            source = "default"
        fields[name] = {"value": getattr(effective, name), "locked": name in locked, "source": source}
    fields["comfy_api_key"] = {
        "has_value": bool(effective.comfy_api_key),
        "hint": _key_hint(effective.comfy_api_key),
        "locked": "comfy_api_key" in locked,
        "source": (
            "environment" if "comfy_api_key" in locked
            else "saved" if "comfy_api_key" in saved
            else "default"
        ),
    }
    return {
        "comfy_url": effective.comfy_url,
        "backend": effective.backend,
        "locked": sorted(locked),
        "has_api_key": bool(effective.comfy_api_key),
        "api_key_hint": _key_hint(effective.comfy_api_key),
        "fields": fields,
        "saved": bool(saved),
        "backends": sorted(SUPPORTED_BACKENDS),
        "connection_file": CONNECTION_VIEW_NAME,
    }


def create_settings_router(
    *,
    base_settings: Callable[[], Settings],
    data_dir: Callable[[], Path],
    active_jobs: Callable[[], dict],
) -> APIRouter:
    router = APIRouter(prefix="/api/settings")

    @router.get("")
    def view_settings() -> dict:
        try:
            return _view(base_settings(), data_dir())
        except ConnectionFileError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @router.post("/test")
    def test_settings(draft: ConnectionDraft) -> dict:
        try:
            effective = _effective(base_settings(), data_dir())
            proposed = validate_connection(_editable_values(draft.model_dump()))
        except (ValueError, ConnectionFileError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return _readiness_for(
            proposed.get("backend", effective.backend),
            proposed.get("comfy_url", effective.comfy_url),
            proposed.get("comfy_api_key", effective.comfy_api_key),
        )

    @router.post("")
    def save_settings(draft: ConnectionDraft) -> dict:
        if any(entry.get("state") in ACTIVE_STATES for entry in active_jobs().values()):
            raise HTTPException(
                status_code=409,
                detail="Wait for the running generations to finish before changing the connection.",
            )
        posted = draft.model_dump()
        try:
            saved = load_connection(data_dir())
            proposed = validate_connection(_editable_values(posted))
        except (ValueError, ConnectionFileError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        # Absent fields keep their saved value; an emptied field reverts to the
        # launch default, and fields the environment has locked never persist.
        merged: dict[str, str] = {
            **saved,
            **proposed,
        }
        locked = locked_fields(os.environ)
        for field in ("backend", "comfy_url", "comfy_api_key"):
            if posted.get(field) == "" and field not in locked:
                merged.pop(field, None)
        for field in locked:
            merged.pop(field, None)
        verdict = _readiness_for(
            merged.get("backend", base_settings().backend),
            merged.get("comfy_url", base_settings().comfy_url),
            merged.get("comfy_api_key", base_settings().comfy_api_key),
        )
        if not verdict["ok"]:
            raise HTTPException(status_code=400, detail=verdict)
        try:
            save_connection(data_dir(), merged)
        except (OSError, ValueError) as error:
            raise HTTPException(status_code=503, detail=f"The connection could not be saved: {error}") from error
        try:
            payload = _view(base_settings(), data_dir())
        except ConnectionFileError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        payload["message"] = verdict["message"]
        return payload

    return router
