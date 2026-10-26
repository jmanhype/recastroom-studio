# SPDX-License-Identifier: MIT
from pathlib import Path

import pytest

from tools import final_submission_gate as gate


def test_tri_state_never_promotes_owner_blocker():
    assert gate.exit_status([]) == 1
    assert gate.exit_status([gate.row("check", "PASS", "artifact")]) == 0
    assert gate.exit_status([gate.row("check", "OWNER_BLOCKED", "artifact")]) == 2
    assert gate.exit_status([gate.row("check", "FAIL", "artifact")]) == 1
    with pytest.raises(ValueError):
        gate.row("check", "PASS", "")
    with pytest.raises(ValueError):
        gate.row("check", "unknown", "artifact")


def test_real_ffprobe_fixture_and_hash_tamper(tmp_path, monkeypatch):
    source = Path(__file__).parent / "fixtures/synthetic_source.mp4"
    monkeypatch.setattr(gate, "DEMO_HASH", gate.sha256(source))
    result = gate.probe_demo(source)
    assert 0 < result["duration_seconds"] < 120
    assert result["audio"][0]["channels"] >= 1
    assert result["video"]["width"] > 0
    assert "mp4" in result["container"]
    changed = tmp_path / "changed.mp4"
    changed.write_bytes(source.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="provenance"):
        gate.probe_demo(changed)


def test_real_probe_rejects_oversize_and_silent_media(tmp_path, monkeypatch):
    import subprocess

    for name, duration in (("silent", 1), ("long", 121)):
        media = tmp_path / (name + ".mp4")
        subprocess.run([
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=16x16:r=1",
            "-t", str(duration), "-c:v", "libx264", str(media),
        ], check=True, timeout=30)
        monkeypatch.setattr(gate, "DEMO_HASH", gate.sha256(media))
        with pytest.raises(ValueError):
            gate.probe_demo(media)


def test_evidence_cannot_be_overwritten(tmp_path):
    with pytest.raises(ValueError, match="overwrite"):
        gate.assess("HEAD", tmp_path / "absent.mp4", tmp_path)
