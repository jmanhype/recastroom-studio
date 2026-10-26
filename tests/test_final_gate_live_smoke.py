# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.final_submission_gate import verify_live_sdk_smoke


def write_smoke(root: Path, *, output_bytes: bytes = b"png", job_id: str = "job-1") -> None:
    directory = root / "docs/evidence/comfy-sdk-smoke-20261025"
    directory.mkdir(parents=True)
    output = directory / "output.png"
    output.write_bytes(output_bytes)
    receipt = {
        "schema_version": "recastroom.live-sdk-smoke.v1",
        "job_id": job_id,
        "initial_status": "queued",
        "final_status": "succeeded",
        "output_count": 1,
        "elapsed_seconds": 5,
        "bound": {
            "submissions": 1,
            "model_inference": False,
            "uploaded_assets": 0,
            "workflow_sha256": "a" * 64,
        },
        "outputs": [
            {
                "sha256": hashlib.sha256(output_bytes).hexdigest(),
                "downloaded_bytes": len(output_bytes),
            }
        ],
    }
    readonly = {
        "job_id": job_id,
        "status": "succeeded",
        "workflow_sha256": "a" * 64,
    }
    (directory / "receipt.json").write_text(json.dumps(receipt))
    (directory / "readonly-job-verification.json").write_text(json.dumps(readonly))


def test_valid_smoke_evidence_passes(tmp_path: Path) -> None:
    write_smoke(tmp_path)

    result = verify_live_sdk_smoke(tmp_path)

    assert result["job_id"] == "job-1"
    assert result["status"] == "succeeded"


def test_changed_output_fails_closed(tmp_path: Path) -> None:
    write_smoke(tmp_path, output_bytes=b"original")
    (tmp_path / "docs/evidence/comfy-sdk-smoke-20261025/output.png").write_bytes(b"changed")

    with pytest.raises(ValueError, match="output_hash_matches"):
        verify_live_sdk_smoke(tmp_path)
