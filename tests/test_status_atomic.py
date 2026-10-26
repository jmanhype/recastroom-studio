# SPDX-License-Identifier: MIT
"""Local-only status publication regressions, including the old writer control."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
import threading

from fastapi.testclient import TestClient
import pytest

import app.main as main


JOB_ID = "a123456789ab"
STATUS_URL = f"/api/jobs/{JOB_ID}/status"


@pytest.fixture
def status_path(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "SETTINGS", replace(main.SETTINGS, data_dir=tmp_path))
    monkeypatch.setattr(main, "JOB_STATUS", {})
    path = tmp_path / "jobs" / JOB_ID / "status.json"
    path.parent.mkdir(parents=True)
    main._set_status(JOB_ID, state="queued", message="before")
    return path


def legacy_set_status(job_id, **values):
    """Negative control: the truncating implementation at base 2b22504."""
    status = main.JOB_STATUS.setdefault(
        job_id, {"job_id": job_id, "state": "queued", "message": "", "artifacts": {}},
    )
    status.update(values)
    (main.SETTINGS.data_dir / "jobs" / job_id / "status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8",
    )


@pytest.mark.parametrize("legacy", [True, False], ids=["old-writer-500", "atomic-writer-200"])
def test_publication_boundary(status_path, monkeypatch, legacy):
    """Hold the writer at publication: old exposes empty JSON, fixed exposes old JSON."""
    entered, release = threading.Event(), threading.Event()
    original_write = Path.write_text
    original_replace = main.os.replace

    def pause():
        entered.set()
        assert release.wait(10), "publication barrier timed out"

    def truncating_write(path, data, *args, **kwargs):
        if path != status_path:
            return original_write(path, data, *args, **kwargs)
        # Same open/truncate/write sequence as Path.write_text, with a barrier.
        with path.open(mode="w", encoding=kwargs.get("encoding")) as handle:
            pause()
            return handle.write(data)

    def paused_replace(source, destination):
        assert Path(source).parent == status_path.parent
        assert json.loads(Path(source).read_text())["message"] == "after"
        pause()
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "write_text", truncating_write)
    monkeypatch.setattr(main.os, "replace", paused_replace)
    writer = legacy_set_status if legacy else main._set_status
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(writer, JOB_ID, state="complete", message="after")
        try:
            assert entered.wait(10), "writer never reached publication"
            with TestClient(main.app, raise_server_exceptions=False) as client:
                response = client.get(STATUS_URL)
            assert response.status_code == (500 if legacy else 200)
            if not legacy:
                assert response.json()["message"] == "before"
                assert main.JOB_STATUS[JOB_ID]["message"] == "before"
        finally:
            release.set()
        future.result(timeout=10)
    with TestClient(main.app) as client:
        assert client.get(STATUS_URL).json()["message"] == "after"
    assert not list(status_path.parent.glob(".status-*.tmp"))


@pytest.mark.parametrize("failure", ["serialize", "write", "replace"])
def test_failed_publication_preserves_snapshot(status_path, monkeypatch, failure):
    before = status_path.read_bytes()
    memory = main.JOB_STATUS[JOB_ID].copy()
    real_temporary = main.tempfile.NamedTemporaryFile

    def fail(*args, **kwargs):
        raise OSError("injected publication failure")

    class BrokenWriter:
        def __init__(self, *args, **kwargs):
            self.handle = real_temporary(*args, **kwargs)

        def __enter__(self):
            self.handle.__enter__()
            return self

        @property
        def name(self):
            return self.handle.name

        def write(self, payload):
            self.handle.write(payload[:7])
            fail()

        def __exit__(self, *args):
            return self.handle.__exit__(*args)

    if failure == "write":
        monkeypatch.setattr(main.tempfile, "NamedTemporaryFile", BrokenWriter)
    elif failure == "replace":
        monkeypatch.setattr(main.os, "replace", fail)
    values = {"message": object() if failure == "serialize" else "after"}
    with pytest.raises((TypeError, OSError)):
        main._set_status(JOB_ID, **values)
    assert status_path.read_bytes() == before
    assert main.JOB_STATUS[JOB_ID] == memory
    assert not list(status_path.parent.glob(".status-*.tmp"))


def test_concurrent_status_api_snapshots(status_path, monkeypatch):
    workers, iterations = 3, 60
    barrier = threading.Barrier(workers * 2, timeout=15)
    names = []
    real_replace = main.os.replace

    def record_replace(source, destination):
        names.append(Path(source))
        return real_replace(source, destination)

    monkeypatch.setattr(main.os, "replace", record_replace)
    main._set_status(JOB_ID, sequence="initial", message="initial")

    def writer(index):
        for sequence in range(iterations):
            barrier.wait()
            token = f"{index}:{sequence}"
            main._set_status(
                JOB_ID, state="generating", sequence=token, message=token,
                **{f"writer_{index}": sequence},
            )

    def reader():
        with TestClient(main.app, raise_server_exceptions=False) as client:
            for _ in range(iterations):
                barrier.wait()
                response = client.get(STATUS_URL)
                assert response.status_code == 200
                payload = response.json()
                assert payload["job_id"] == JOB_ID
                assert payload["message"] == payload["sequence"]
                assert payload["state"] in {"queued", "generating"}
                assert payload["artifacts"] == {}

    with ThreadPoolExecutor(max_workers=workers * 2) as pool:
        futures = [pool.submit(writer, index) for index in range(workers)]
        futures += [pool.submit(reader) for _ in range(workers)]
        for future in futures:
            future.result(timeout=30)
    payload = json.loads(status_path.read_text())
    assert payload == main.JOB_STATUS[JOB_ID]
    assert all(payload[f"writer_{index}"] == iterations - 1 for index in range(workers))
    assert len(names) == len(set(names)) == workers * iterations + 1
    assert all(path.parent == status_path.parent for path in names)
    assert not list(status_path.parent.glob(".status-*.tmp"))


def test_status_schema_and_missing_jobs(status_path):
    with TestClient(main.app) as client:
        assert client.get(STATUS_URL).json() == {
            "job_id": JOB_ID, "state": "queued", "message": "before", "artifacts": {},
        }
        for job_id in ("bad-id", "short", "b123456789ab"):
            assert client.get(f"/api/jobs/{job_id}/status").status_code == 404
        status_path.unlink()
        assert client.get(STATUS_URL).status_code == 404
