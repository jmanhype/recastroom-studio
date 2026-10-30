#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fail closed on private paths, credentials, or cached media metadata."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN_PREFIXES = (".paivot/", ".vault/", ".claude/", "work/")
LOCAL_ONLY_FILES = {
    "tools/build_keeper_evidence.py",
    "tools/initialize_contest_backlog.py",
}
FORBIDDEN_BASENAMES = {"secrets.yaml", "secrets.local.yaml"}
FORBIDDEN_SUFFIXES = {".env", ".pem", ".key", ".secrets"}
PRIVATE_PREFIXES = ("pexels", "mr_bean", "mrbean", "the_mask")
PRIVATE_PHRASES = ("mr bean", "the mask")
ABSOLUTE_PATH = re.compile(r"(?i)(/users/[a-z0-9_.-]+/|c:\\users\\[a-z0-9_.-]+\\)")
PRIVATE_NETWORK = re.compile(r"(?i)\b(192\.168|10)\.\d{1,3}\.\d{1,3}\b")
CREDENTIAL = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\b\s*[:=]\s*"
    r"[\"']([a-z0-9_./+=:-]{12,})[\"']"
)
PLACEHOLDERS = ("...", "<", "example", "your-", "changeme")
TEST_VALUE_MARKERS = ("for-test", "test-value")
ALLOWED_MEDIA_TAGS = {
    "compatible_brands",
    "encoder",
    "handler_name",
    "language",
    "major_brand",
    "minor_version",
    "vendor_id",
}
AUDIT_DEFINITIONS = {
    Path("tools/audit_release.py").as_posix(),
    Path("src/openjutsu/evidence.py").as_posix(),
}


def has_private_marker(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in (*PRIVATE_PREFIXES, *PRIVATE_PHRASES))


def release_files(root: Path) -> list[Path]:
    generated = {".git", "__pycache__", ".pytest_cache", ".venv"}
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not (set(path.relative_to(root).parts) & generated)
    )


def check_paths(files: list[Path], root: Path, errors: list[str]) -> None:
    for path in files:
        relative = path.relative_to(root).as_posix()
        if relative.startswith(FORBIDDEN_PREFIXES) or relative in LOCAL_ONLY_FILES:
            errors.append(f"private/local-only path is present: {relative}")
        if Path(relative).name.lower() in FORBIDDEN_BASENAMES:
            errors.append(f"credential-like path is present: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"credential-like suffix is present: {relative}")
        if path.is_symlink():
            errors.append(f"symlink is present: {relative}")


def check_text_and_binaries(files: list[Path], root: Path, errors: list[str]) -> tuple[int, int]:
    text_count = 0
    binary_count = 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            binary_count += 1
            lowered = raw.lower()
            if any(marker.encode() in lowered for marker in (*PRIVATE_PREFIXES, *PRIVATE_PHRASES)):
                errors.append(f"cached private-reference marker: {relative}")
            if b"/users/" in lowered or b"c:\\users\\" in lowered:
                errors.append(f"absolute user path: {relative}")
            continue

        text_count += 1
        if relative not in AUDIT_DEFINITIONS:
            if ABSOLUTE_PATH.search(text):
                errors.append(f"absolute user path: {relative}")
            if PRIVATE_NETWORK.search(text):
                errors.append(f"private network address: {relative}")
            if has_private_marker(text):
                errors.append(f"cached private-reference marker: {relative}")
        for match in CREDENTIAL.finditer(text):
            value = match.group(1).lower()
            if any(marker in value for marker in TEST_VALUE_MARKERS):
                continue
            if not any(placeholder in value for placeholder in PLACEHOLDERS):
                errors.append(f"possible credential value: {relative}")
                break
    return text_count, binary_count


def check_media_metadata(files: list[Path], root: Path, errors: list[str]) -> int:
    count = 0
    for path in files:
        if path.suffix.lower() not in {".mp4", ".jpg", ".jpeg", ".png"}:
            continue
        count += 1
        relative = path.relative_to(root).as_posix()
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            errors.append(f"media probe failed: {relative}")
            continue
        probe = json.loads(result.stdout)
        tags = dict(probe.get("format", {}).get("tags", {}))
        for stream in probe.get("streams", []):
            tags.update(stream.get("tags", {}))
        for key, value in tags.items():
            if str(key).lower() not in ALLOWED_MEDIA_TAGS:
                errors.append(f"unallowed media tag {key}: {relative}")
            if has_private_marker(f"{key}={value}") or ABSOLUTE_PATH.search(f"{key}={value}"):
                errors.append(f"private media tag {key}: {relative}")
    return count


def check_workflow(root: Path, errors: list[str]) -> None:
    workflow_path = root / "workflows/recastroom_h3_workflow.json"
    if not workflow_path.is_file():
        errors.append("bundled workflow is missing")
        return
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    try:
        plan = json.loads(workflow["1189"]["inputs"]["plan"])
    except (KeyError, TypeError, json.JSONDecodeError):
        errors.append("bundled workflow has no valid BFSShotPlanner plan")
        return
    if "ref_details" in plan:
        errors.append("bundled workflow retains cached reference details")
    serialized = json.dumps(plan)
    if has_private_marker(serialized) or ABSOLUTE_PATH.search(serialized):
        errors.append("bundled workflow plan contains private data")


def check_license(files: list[Path], root: Path, errors: list[str]) -> None:
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    if "MIT License" not in license_text or "Permission is hereby granted" not in license_text:
        errors.append("MIT LICENSE is missing or changed")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    if 'license = { text = "MIT" }' not in pyproject:
        errors.append("package metadata does not declare MIT")
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.suffix == ".py" and "SPDX-License-Identifier: MIT" not in path.read_text(encoding="utf-8")[:180]:
            errors.append(f"Python file lacks an MIT SPDX header: {relative}")
        elif path.suffix == ".html" and "SPDX-License-Identifier: MIT" not in path.read_text(encoding="utf-8")[:180]:
            errors.append(f"HTML file lacks an MIT SPDX header: {relative}")


def audit(root: Path) -> tuple[list[str], dict[str, int | str]]:
    root = root.resolve()
    files = release_files(root)
    errors: list[str] = []
    check_paths(files, root, errors)
    text_count, binary_count = check_text_and_binaries(files, root, errors)
    media_count = check_media_metadata(files, root, errors)
    check_workflow(root, errors)
    check_license(files, root, errors)
    return errors, {
        "root": str(root),
        "tracked_files": len(files),
        "text_files": text_count,
        "binary_files": binary_count,
        "probed_media_files": media_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path, help="write the complete audit output to this local file")
    args = parser.parse_args()
    errors, summary = audit(args.root)
    lines = [f"{key}={value}" for key, value in summary.items()]
    lines.append("PASS: release audit" if not errors else "FAIL: release audit")
    lines.extend(f"FAIL: {error}" for error in errors)
    output = "\n".join(lines) + "\n"
    sys.stdout.write(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
