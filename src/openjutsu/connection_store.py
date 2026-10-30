# SPDX-License-Identifier: MIT
"""Saved renderer connection for the settings screen, stored beside workspace data.

The launch environment always wins: a field set through RECASTROOM_*/OPENJUTSU_*
(or COMFY_API_KEY) is locked and never overridden by the saved file, mirroring
the Henge bridge's connection.json semantics. The file holds only the
runtime-editable fields (backend, comfy_url, comfy_api_key); data locations,
workflow selection, and tool paths stay launch-time settings.
"""
from __future__ import annotations

from dataclasses import replace
import json
import os
import re
from pathlib import Path
from typing import Mapping

from .config import SUPPORTED_BACKENDS, Settings, setting

CONNECTION_FILENAME = "connection.json"
EDITABLE_FIELDS = ("backend", "comfy_url", "comfy_api_key")
_URL_PATTERN = re.compile(r"^https?://[^\s?#]+$")
_FILE_MODE = 0o600


class ConnectionFileError(RuntimeError):
    """The saved connection file exists but cannot be used as saved."""


def _is_locked(env: Mapping[str, str], field: str) -> bool:
    if field == "comfy_api_key":
        return bool(env.get("COMFY_API_KEY") or setting(env, "COMFY_API_KEY"))
    return setting(env, field.upper()) is not None


def locked_fields(env: Mapping[str, str] | None = None) -> set[str]:
    """Fields fixed by the launch environment; the browser cannot change them."""
    source = os.environ if env is None else env
    return {field for field in EDITABLE_FIELDS if _is_locked(source, field)}


def connection_path(data_dir: Path) -> Path:
    return Path(data_dir) / CONNECTION_FILENAME


def load_connection(data_dir: Path) -> dict:
    """Return the saved connection overrides; {} when none are saved."""
    path = connection_path(data_dir)
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConnectionFileError(f"The saved connection file is unreadable: {error}") from error
    if not isinstance(payload, dict):
        raise ConnectionFileError("The saved connection file is not a settings object.")
    unknown = sorted(set(payload) - set(EDITABLE_FIELDS))
    if unknown:
        raise ConnectionFileError(f"The saved connection file has unknown fields: {', '.join(unknown)}.")
    return dict(payload)


def validate_connection(payload: Mapping[str, object]) -> dict[str, str]:
    """Validate non-empty connection values; unknown keys and bad values raise ValueError."""
    unknown = sorted(set(payload) - set(EDITABLE_FIELDS))
    if unknown:
        raise ValueError(f"Unknown connection field: {', '.join(unknown)}.")
    normalized: dict[str, str] = {}
    for field in EDITABLE_FIELDS:
        if field not in payload or payload[field] in (None, ""):
            continue
        value = payload[field]
        if not isinstance(value, str):
            raise ValueError(f"Connection field {field} must be text.")
        if field == "backend" and value not in SUPPORTED_BACKENDS:
            supported = ", ".join(sorted(SUPPORTED_BACKENDS))
            raise ValueError(f"The backend must be one of: {supported}.")
        if field == "comfy_url":
            if not _URL_PATTERN.match(value):
                raise ValueError("The renderer address must be an http(s) URL, for example http://127.0.0.1:8188.")
            value = value.rstrip("/")
        normalized[field] = value
    return normalized


def save_connection(data_dir: Path, overrides: Mapping[str, str]) -> None:
    """Atomically replace the saved connection file with validated overrides."""
    normalized = validate_connection(overrides)
    destination = connection_path(data_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{CONNECTION_FILENAME}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.chmod(temporary, _FILE_MODE)
    os.replace(temporary, destination)


def merge_current(base: Settings, data_dir: Path, env: Mapping[str, str] | None = None) -> Settings:
    """Overlay the saved connection onto launch settings; locked fields never change."""
    saved = load_connection(data_dir)
    if not saved:
        return base
    locked = locked_fields(env)
    updates = {
        field: value.rstrip("/") if field == "comfy_url" else value
        for field, value in saved.items()
        if field not in locked
    }
    return replace(base, **updates) if updates else base
