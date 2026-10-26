#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build SHA-256 and ffprobe receipts for an E2E evidence directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


MEDIA_SUFFIXES = {".mp4", ".png", ".jpg", ".jpeg"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def redact_path(value: object, path: Path, display_path: str) -> object:
    if isinstance(value, dict):
        return {key: redact_path(item, path, display_path) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_path(item, path, display_path) for item in value]
    if isinstance(value, str):
        return value.replace(str(path.resolve()), display_path)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    evidence_dir = args.evidence_dir.resolve()
    artifacts: dict[str, dict] = {}
    for path in sorted(candidate for candidate in evidence_dir.rglob("*") if candidate.is_file()):
        relative = path.relative_to(evidence_dir).as_posix()
        if relative == "RECEIPTS.json":
            continue
        media_probe = ffprobe(path) if path.suffix.lower() in MEDIA_SUFFIXES else None
        if media_probe is not None:
            media_probe = redact_path(media_probe, path, relative)
        artifacts[relative] = {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "ffprobe": media_probe,
        }

    receipt = {
        "schema_version": "openjutsu.e2e-artifact-receipts.v1",
        "source_commit": args.source_commit,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    output = evidence_dir / "RECEIPTS.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
