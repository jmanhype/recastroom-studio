# SPDX-License-Identifier: MIT
"""Fail-closed verification for the Openjutsu keeper evidence pack.

The verifier intentionally returns no partial-success state. Every required
file, rights field, human receipt, workflow field, QC receipt, and media probe
must be present and match before a pack can pass.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = "openjutsu.keeper-evidence.v1"
MANIFEST_NAME = "manifest.json"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_MEDIA_TAGS = {
    "compatible_brands",
    "encoder",
    "handler_name",
    "hyperframes_renderer",
    "hyperframes_version",
    "language",
    "major_brand",
    "minor_version",
    "vendor_id",
}
PRIVATE_METADATA_PATTERN = re.compile(
    r"(?i)(/users/|c:\\users\\|api[_-]?key|password|pexels|mr[._ ]?bean|the[._ ]?mask)"
)
EXPECTED_KEEPERS = {
    "seed50_jay_plate_a",
    "era_1985_plate_a",
    "era_noir_plate_a_fullbw",
    "fanwipe_man_plate_a",
    "fanwipe_young_plate_a",
    "impossible_robot_mechanical_mouth",
    "hotel_jay_repair_seed51",
    "object_jay",
    "twoperson_jay_trimmed_hostrestored",
    "lenspush_jay_repair_seed51",
    "cameramove_jay_stretch",
}
EXPECTED_CONCEPTS = {
    "Core identity swap",
    "Era restyle",
    "Fan wipe",
    "Impossible casting",
    "Singing performance swap",
    "Object preservation",
    "Selective person swap",
    "Lens interaction",
    "Camera-move preservation",
}
REQUIRED_ARTIFACT_KINDS = {"final", "compare", "contact", "qwen_report"}
RIGHTS_CLEAN = "rights_clean_generated"


class EvidenceVerificationError(ValueError):
    """Raised when an evidence pack fails one or more closed checks."""


@dataclass(frozen=True)
class VerificationResult:
    keeper_count: int
    artifact_count: int
    manifest_sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_ffprobe(path: Path) -> dict[str, Any]:
    executable = Path("/opt/homebrew/bin/ffprobe")
    if not executable.exists():
        import shutil

        found = shutil.which("ffprobe")
        if found is None:
            raise EvidenceVerificationError("ffprobe is required but was not found")
        executable = Path(found)
    completed = subprocess.run(
        [
            str(executable),
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:format_tags",
            "-show_entries",
            "stream=index,codec_type,codec_name,width,height,avg_frame_rate,nb_frames,channels,sample_rate:stream_tags",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise EvidenceVerificationError(f"ffprobe failed for {path}: {completed.stderr.strip()}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise EvidenceVerificationError(f"ffprobe returned invalid JSON for {path}") from error


def _safe_artifact_path(root: Path, relative: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        errors.append(f"{label}: path must be a non-empty relative string")
        return None
    relative_path = Path(relative)
    if any(part in {"", ".", ".."} for part in relative_path.parts):
        errors.append(f"{label}: path must not contain '.', '..', or empty components")
        return None
    unresolved = root / relative_path
    try:
        if unresolved.is_symlink():
            errors.append(f"{label}: symlinks are not permitted")
            return None
        resolved = unresolved.resolve(strict=True)
        root_resolved = root.resolve(strict=True)
        resolved.relative_to(root_resolved)
    except FileNotFoundError:
        errors.append(f"{label}: missing file")
        return None
    except (OSError, ValueError) as error:
        errors.append(f"{label}: unsafe path ({error})")
        return None
    if not resolved.is_file():
        errors.append(f"{label}: not a regular file")
        return None
    return resolved


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _verify_rights(rights: Any, label: str, errors: list[str]) -> None:
    if not isinstance(rights, dict):
        errors.append(f"{label}.rights: must be an object")
        return
    _require(rights.get("classification") == RIGHTS_CLEAN, f"{label}.rights.classification must be {RIGHTS_CLEAN}", errors)
    _require(rights.get("private_ip") is False, f"{label}.rights.private_ip must be false", errors)
    _require(rights.get("third_party_film_tv") is False, f"{label}.rights.third_party_film_tv must be false", errors)
    provenance = rights.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{label}.rights.provenance: must be an object")
    else:
        _require(
            provenance.get("source_type") == "project_generated_synthetic_or_operator_authorized",
            f"{label}.rights.provenance.source_type is not allowed",
            errors,
        )
        receipt = provenance.get("source_receipt")
        _require(isinstance(receipt, str) and bool(receipt), f"{label}.rights.provenance.source_receipt is missing", errors)
    consent = rights.get("consent")
    if not isinstance(consent, dict):
        errors.append(f"{label}.rights.consent: must be an object")
    else:
        _require(consent.get("status") == "recorded", f"{label}.rights.consent.status must be recorded", errors)
        _require(consent.get("actor") == "operator/Jay", f"{label}.rights.consent.actor must be operator/Jay", errors)
        _require(consent.get("verdict") == "Done and perfect", f"{label}.rights.consent.verdict is unapproved", errors)
        approved_at = consent.get("approved_at_utc")
        try:
            datetime.fromisoformat(str(approved_at))
        except (TypeError, ValueError):
            errors.append(f"{label}.rights.consent.approved_at_utc is invalid")


def _verify_probe(
    expected: Any,
    path: Path,
    label: str,
    probe_runner: Callable[[Path], dict[str, Any]],
    errors: list[str],
) -> None:
    if not isinstance(expected, dict):
        errors.append(f"{label}.probe: must be an object")
        return
    try:
        actual_raw = probe_runner(path)
    except EvidenceVerificationError:
        raise
    except Exception as error:  # Third-party probe failures must fail closed.
        errors.append(f"{label}.probe: ffprobe execution failed ({error})")
        return

    actual_streams = actual_raw.get("streams", [])
    actual_format = actual_raw.get("format", {})
    if expected.get("media_type") == "video":
        videos = [stream for stream in actual_streams if stream.get("codec_type") == "video"]
        audios = [stream for stream in actual_streams if stream.get("codec_type") == "audio"]
        _require(len(videos) == 1, f"{label}.probe: exactly one video stream required", errors)
        _require(len(audios) == 1, f"{label}.probe: exactly one audio stream required", errors)
        if videos and audios:
            actual = {
                "codec_name": videos[0].get("codec_name"),
                "width": videos[0].get("width"),
                "height": videos[0].get("height"),
                "avg_frame_rate": videos[0].get("avg_frame_rate"),
                "nb_frames": videos[0].get("nb_frames"),
                "audio_codec_name": audios[0].get("codec_name"),
                "audio_sample_rate": audios[0].get("sample_rate"),
                "audio_channels": audios[0].get("channels"),
                "duration": actual_format.get("duration"),
                "size": actual_format.get("size"),
            }
            for field, expected_value in expected.items():
                if field != "media_type":
                    _require(actual.get(field) == expected_value, f"{label}.probe.{field}: expected {expected_value!r}, got {actual.get(field)!r}", errors)
    elif expected.get("media_type") == "image":
        images = [stream for stream in actual_streams if stream.get("codec_type") == "video"]
        _require(len(images) == 1, f"{label}.probe: exactly one image stream required", errors)
        if images:
            actual = {
                "codec_name": images[0].get("codec_name"),
                "width": images[0].get("width"),
                "height": images[0].get("height"),
            }
            for field, expected_value in expected.items():
                if field != "media_type":
                    _require(actual.get(field) == expected_value, f"{label}.probe.{field}: expected {expected_value!r}, got {actual.get(field)!r}", errors)
    else:
        errors.append(f"{label}.probe.media_type must be video or image")


def verify_manifest(
    manifest_path: Path,
    *,
    probe_runner: Callable[[Path], dict[str, Any]] = default_ffprobe,
) -> VerificationResult:
    """Verify a keeper evidence pack or raise ``EvidenceVerificationError``."""
    from openjutsu.manifest_verifier import (
        _verify_complete_file_set,
        _verify_keepers,
        _verify_receipts,
    )

    manifest_path = Path(manifest_path)
    errors: list[str] = []
    root = manifest_path.parent
    try:
        root_resolved = root.resolve(strict=True)
    except FileNotFoundError as error:
        raise EvidenceVerificationError(f"evidence root is missing: {root}") from error
    _safe = _safe_artifact_path(root_resolved, manifest_path.name, "manifest", errors)
    if _safe is None or not manifest_path.name == MANIFEST_NAME:
        if not manifest_path.name == MANIFEST_NAME:
            errors.append(f"manifest: filename must be {MANIFEST_NAME}")
        raise EvidenceVerificationError("\n".join(errors))
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceVerificationError(f"manifest could not be read as JSON: {error}") from error
    if not isinstance(manifest, dict):
        raise EvidenceVerificationError("manifest: top-level value must be an object")

    _require(manifest.get("schema_version") == SCHEMA_VERSION, f"manifest.schema_version must be {SCHEMA_VERSION}", errors)
    _require(manifest.get("status") == "human_approved", "manifest.status must be human_approved", errors)
    _require(manifest.get("keeper_count") == 11, "manifest.keeper_count must be 11", errors)
    intended_ids = manifest.get("intended_keeper_ids")
    if not isinstance(intended_ids, list) or len(intended_ids) != 11 or set(intended_ids) != EXPECTED_KEEPERS or len(set(intended_ids)) != 11:
        errors.append("manifest.intended_keeper_ids must exactly match the eleven approved keepers")
    rejected = manifest.get("rejected_optional_variant")
    if not isinstance(rejected, dict) or rejected.get("slug") != "era_anime_plate_a" or rejected.get("included") is not False:
        errors.append("manifest.rejected_optional_variant must exclude era_anime_plate_a")

    approval = manifest.get("human_approval")
    if not isinstance(approval, dict):
        errors.append("manifest.human_approval: must be an object")
    else:
        _require(approval.get("approved_by") == "operator/Jay", "human_approval.approved_by must be operator/Jay", errors)
        _require(approval.get("operator_verdict") == "Done and perfect", "human_approval.operator_verdict is unapproved", errors)
        try:
            datetime.fromisoformat(str(approval.get("approved_at_utc")))
        except (TypeError, ValueError):
            errors.append("human_approval.approved_at_utc is invalid")

    keepers = manifest.get("keepers")
    if not isinstance(keepers, list):
        errors.append("manifest.keepers: must be an array")
        raise EvidenceVerificationError("\n".join(errors))
    ids = [keeper.get("slug") for keeper in keepers if isinstance(keeper, dict)]
    if len(keepers) != 11 or len(ids) != 11 or len(set(ids)) != 11 or set(ids) != EXPECTED_KEEPERS:
        errors.append("manifest.keepers must contain exactly the eleven intended slugs")

    listed_paths: set[Path] = set()
    receipts = manifest.get("provenance_receipts")
    if not isinstance(receipts, list) or not receipts:
        errors.append("manifest.provenance_receipts: must be a non-empty array")
        receipts = []
    artifact_count = _verify_receipts(root_resolved, receipts, listed_paths, errors)
    artifact_count += _verify_keepers(root_resolved, keepers, listed_paths, probe_runner, errors)
    _verify_complete_file_set(root_resolved, listed_paths, errors)

    if errors:
        raise EvidenceVerificationError("\n".join(errors))
    return VerificationResult(
        keeper_count=len(keepers),
        artifact_count=artifact_count,
        manifest_sha256=sha256_file(manifest_path),
    )


def _verify_media_metadata(
    path: Path,
    label: str,
    probe_runner: Callable[[Path], dict[str, Any]],
    errors: list[str],
) -> None:
    try:
        raw = probe_runner(path)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        errors.append(f"{label}.media metadata probe failed: {error}")
        return
    tags: dict[str, str] = dict(raw.get("format", {}).get("tags", {}))
    for stream in raw.get("streams", []):
        tags.update(stream.get("tags", {}))
    for key, value in tags.items():
        if str(key).lower() not in ALLOWED_MEDIA_TAGS:
            errors.append(f"{label}.media tag {key} is not allowed")
        if PRIVATE_METADATA_PATTERN.search(f"{key}={value}"):
            errors.append(f"{label}.media tag {key} contains private metadata")
