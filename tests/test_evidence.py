# SPDX-License-Identifier: MIT
import json
import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from openjutsu.evidence import EvidenceVerificationError, verify_manifest


REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "docs/evidence/slate/manifest.json"


def test_committed_eleven_keeper_pack_passes() -> None:
    if shutil.which("ffprobe") is None and not Path("/opt/homebrew/bin/ffprobe").exists():
        pytest.skip("ffprobe is unavailable")

    result = verify_manifest(MANIFEST)

    assert result.keeper_count == 11
    assert result.artifact_count == 48


def test_verifier_fails_closed_on_changed_and_missing_asset_bytes(tmp_path: Path) -> None:
    if shutil.which("ffprobe") is None and not Path("/opt/homebrew/bin/ffprobe").exists():
        pytest.skip("ffprobe is unavailable")
    copied_root = tmp_path / "slate"
    shutil.copytree(MANIFEST.parent, copied_root, copy_function=shutil.copy2)
    report = next(copied_root.glob("keepers/*/*_qwen.md"))
    original = report.read_bytes()
    mutated = bytearray(original)
    mutated[-2] ^= 1
    report.write_bytes(mutated)

    with pytest.raises(EvidenceVerificationError, match=r"sha256 changed"):
        verify_manifest(copied_root / "manifest.json")

    missing = next(copied_root.glob("keepers/*/*_contact.jpg"))
    missing.unlink()
    with pytest.raises(EvidenceVerificationError, match=r"missing file"):
        verify_manifest(copied_root / "manifest.json")


def test_verifier_fails_closed_on_cached_media_metadata(tmp_path: Path) -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("ffmpeg tools are unavailable")
    copied_root = tmp_path / "slate"
    shutil.copytree(MANIFEST.parent, copied_root, copy_function=shutil.copy2)
    media = next(copied_root.glob("keepers/*/*_compare_480p.mp4"))
    temporary = media.with_suffix(".tagged.mp4")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(media),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-c",
            "copy",
            "-movflags",
            "+use_metadata_tags",
            "-metadata",
            "prompt=cached",
            str(temporary),
        ],
        check=True,
    )
    temporary.replace(media)
    manifest_path = copied_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relative = media.relative_to(copied_root).as_posix()
    for keeper in manifest["keepers"]:
        for artifact in keeper["artifacts"]:
            if artifact["path"] == relative:
                artifact["bytes"] = media.stat().st_size
                artifact["sha256"] = hashlib.sha256(media.read_bytes()).hexdigest()
                if isinstance(artifact.get("probe"), dict):
                    artifact["probe"]["size"] = str(media.stat().st_size)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(EvidenceVerificationError, match=r"media tag prompt is not allowed"):
        verify_manifest(manifest_path)


def test_verifier_fails_closed_on_unconsented_private_entry(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.md"
    receipt.write_text("receipt\n", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "schema_version": "openjutsu.keeper-evidence.v1",
        "status": "human_approved",
        "keeper_count": 11,
        "intended_keeper_ids": [],
        "human_approval": {},
        "rejected_optional_variant": {},
        "provenance_receipts": [
            {
                "path": "receipt.md",
                "bytes": receipt.stat().st_size,
                "sha256": "0" * 64,
                "rights": {
                    "classification": "private_ip",
                    "private_ip": True,
                    "third_party_film_tv": True,
                    "provenance": {"source_type": "private_film_tv", "source_receipt": "receipt.md"},
                    "consent": {"status": "missing", "actor": "unknown"},
                },
            }
        ],
        "keepers": [],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(EvidenceVerificationError, match=r"(?s)private_ip must be false.*consent.status must be recorded"):
        verify_manifest(manifest_path)
