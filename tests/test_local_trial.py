# SPDX-License-Identifier: MIT
from pathlib import Path

import pytest

from scripts.local_trial import require_loopback_host, scan_exposure


def test_local_trial_accepts_only_loopback_hosts() -> None:
    for host in ("127.0.0.1", "localhost", "::1"):
        require_loopback_host(host)

    with pytest.raises(ValueError, match="loopback"):
        require_loopback_host("0.0.0.0")


def test_exposure_scan_reports_credentials_and_local_paths(tmp_path, monkeypatch) -> None:
    from scripts.local_trial import REPO

    safe = tmp_path / "safe.md"
    unsafe = tmp_path / "unsafe.log"
    credential_value = "a" * 24
    private_path = Path("/", "Users", "reviewer", "private")
    safe.write_text("Public reviewer path with no secret or absolute path.\n", encoding="utf-8")
    unsafe.write_text(
        f'api_key = "{credential_value}"\n{private_path}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.local_trial.REPO", tmp_path)
    try:
        findings = scan_exposure([safe, unsafe])
    finally:
        monkeypatch.setattr("scripts.local_trial.REPO", REPO)

    assert {item["kind"] for item in findings} == {
        "absolute-or-private-network-path",
        "possible-credential-value",
    }
