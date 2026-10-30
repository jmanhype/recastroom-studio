#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a deterministic filtered source archive without tagging or publishing."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_release import audit


EXCLUDED_PREFIXES = (".paivot", ".vault", ".claude", "work")
EXCLUDED_FILES = {
    "tools/build_keeper_evidence.py",
    "tools/initialize_contest_backlog.py",
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout.strip()


def require_clean_worktree() -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if status.returncode != 0:
        raise SystemExit(status.stderr)
    if status.stdout:
        raise SystemExit("refusing to archive a dirty worktree; commit or stash first")


def resolve_commit(commit: str) -> tuple[str, str]:
    git("cat-file", "-e", f"{commit}^{{commit}}")
    commit_hash = git("rev-parse", f"{commit}^{{commit}}")
    tree_hash = git("rev-parse", f"{commit_hash}^{{tree}}")
    return commit_hash, tree_hash


def extract_commit(commit: str, destination: Path) -> None:
    with tempfile.NamedTemporaryFile(prefix=".openjutsu-archive-", suffix=".tar", dir=ROOT / "work") as temporary:
        archive_path = Path(temporary.name)
    try:
        subprocess.run(
            [
                "git",
                "archive",
                "--format=tar",
                f"--output={archive_path}",
                commit,
            ],
            cwd=ROOT,
            check=True,
        )
        with tarfile.open(archive_path, "r:") as archive:
            try:
                archive.extractall(destination, filter="data")
            except TypeError:  # Python 3.10 compatibility.
                archive.extractall(destination)
    finally:
        archive_path.unlink(missing_ok=True)


def filter_local_files(root: Path) -> list[str]:
    excluded: list[str] = []
    for prefix in EXCLUDED_PREFIXES:
        path = root / prefix
        if path.exists():
            shutil.rmtree(path)
            excluded.append(prefix)
    for relative in sorted(EXCLUDED_FILES):
        path = root / relative
        if path.exists():
            path.unlink()
            excluded.append(relative)
    return sorted(excluded)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def content_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_deterministic_zip(root: Path, destination: Path, prefix: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".openjutsu-zip-", suffix=".zip", dir=destination.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(item for item in root.rglob("*") if item.is_file()):
                relative = path.relative_to(root).as_posix()
                info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                executable = path.stat().st_mode & 0o111
                info.external_attr = (0o755 if executable else 0o644) << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    require_clean_worktree()
    commit, source_tree = resolve_commit(args.commit)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    release = f"v{version}-rc.1"
    output = args.output or ROOT / "work" / "release" / f"recastroom-studio-{release}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".openjutsu-release-", dir=ROOT / "work") as directory:
        staging = Path(directory) / "release"
        staging.mkdir()
        extract_commit(commit, staging)
        excluded = filter_local_files(staging)
        errors, _ = audit(staging)
        if errors:
            raise SystemExit("filtered release tree failed audit:\n" + "\n".join(errors))
        content_tree = content_tree_digest(staging)
        write_deterministic_zip(staging, output, f"recastroom-studio-{release}")

    receipt = {
        "schema_version": "openjutsu.release-archive.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "product": "recastroom-studio",
        "version": version,
        "release_candidate": release,
        "commit": commit,
        "source_tree": source_tree,
        "filtered_content_tree_sha256": content_tree,
        "excluded_from_public_archive": excluded,
        "archive": {
            "path": output.resolve().as_posix(),
            "bytes": output.stat().st_size,
            "sha256": sha256(output),
        },
        "published": False,
        "tag_created": False,
    }
    receipt_path = args.receipt or output.with_suffix(".receipt.json")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
