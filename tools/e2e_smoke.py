#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the credential-free hosted upload-to-output smoke path."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time

import requests


REPO = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(path: Path, ffprobe: str = "ffprobe") -> dict:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def redact_local_paths(value: object, roots: list[tuple[Path, str]]) -> object:
    """Replace machine-specific roots in JSON evidence with stable placeholders."""
    replacements = sorted(
        ((str(root.resolve()), label) for root, label in roots),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    if isinstance(value, dict):
        return {key: redact_local_paths(item, roots) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_local_paths(item, roots) for item in value]
    if isinstance(value, str):
        for original, label in replacements:
            value = value.replace(original, label)
        return value
    return value


def child_environment(backend: str, data_dir: Path) -> dict[str, str]:
    """Build a minimal inherited environment without exposing secret values."""
    environment = os.environ.copy()
    environment.update(
        {
            "RECASTROOM_BACKEND": backend,
            "RECASTROOM_DATA_DIR": str(data_dir),
            "PYTHONPATH": f"{REPO / 'src'}{os.pathsep}{REPO}",
        }
    )
    for name in (
        "COMFY_API_KEY",
        "OPENJUTSU_COMFY_API_KEY",
        "RECASTROOM_COMFY_API_KEY",
        "COMFY_BASE_URL",
    ):
        environment.pop(name, None)
    return environment


class Server:
    def __init__(self, backend: str, host: str, port: int, data_dir: Path, log_path: Path) -> None:
        self.backend = backend
        self.base_url = f"http://{host}:{port}"
        self.data_dir = data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=REPO,
            env=child_environment(backend, data_dir),
            stdout=log_path.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )

    def wait(self) -> None:
        last_error: Exception | None = None
        for _ in range(100):
            if self.process.poll() is not None:
                raise RuntimeError(f"{self.backend} server exited before becoming ready")
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=0.2)
                if response.status_code == 200:
                    return
            except requests.RequestException as error:
                last_error = error
            time.sleep(0.05)
        raise RuntimeError(f"{self.backend} server did not become ready: {last_error}")

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


def upload_files(source: Path, reference: Path, words: Path) -> dict[str, tuple]:
    return {
        "source": (source.name, source.read_bytes(), "video/mp4"),
        "reference_1": (reference.name, reference.read_bytes(), "image/png"),
        "words": (words.name, words.read_bytes(), "application/json"),
    }


def request_record(method: str, path: str, response: requests.Response, body: object) -> dict:
    return {
        "method": method,
        "path": path,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "body": body,
    }


def json_call(
    client: requests.Session, base_url: str, method: str, path: str, **kwargs
) -> tuple[requests.Response, object, dict]:
    response = client.request(method, base_url + path, **kwargs)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response, body, request_record(method, path, response, body)


def wait_for_terminal_status(
    client: requests.Session, base_url: str, job_id: str
) -> tuple[dict, list[dict]]:
    observations: list[dict] = []
    for _ in range(150):
        response = client.get(f"{base_url}/api/jobs/{job_id}/status", timeout=2)
        response.raise_for_status()
        status = response.json()
        observations.append({"elapsed_poll": len(observations), "status": status})
        if status["state"] in {"complete", "error"}:
            return status, observations
        time.sleep(0.1)
    raise RuntimeError(f"Job {job_id} did not reach a terminal state")


def prepare_valid_job(
    client: requests.Session, base_url: str, fixtures: dict[str, Path], records: list[dict]
) -> str:
    response, body, record = json_call(
        client,
        base_url,
        "POST",
        "/api/prepare",
        files=upload_files(**fixtures),
        data={
            "identity": "Synthetic fixture performer",
            "seed": "50",
            "rights_attested": "true",
        },
    )
    records.append(record)
    if response.status_code != 200:
        raise RuntimeError(f"Prepare failed: {body}")
    return body["job_id"]  # type: ignore[index]


def artifact_record(path: Path, response: requests.Response) -> dict:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "http_status": response.status_code,
        "http_content_type": response.headers.get("content-type", ""),
        "ffprobe": probe(path),
    }


def run_dry_run_evidence(
    server: Server, output_dir: Path, fixtures: dict[str, Path], records: list[dict]
) -> dict:
    with requests.Session() as client:
        response, body, record = json_call(client, server.base_url, "GET", "/api/health")
        records.append(record)
        assert response.status_code == 200 and body["backend"] == "dry_run"

        _, missing_body, missing_record = json_call(
            client,
            server.base_url,
            "POST",
            "/api/prepare",
            files=upload_files(**fixtures),
            data={"identity": "Synthetic fixture performer", "seed": "50"},
        )
        records.append(missing_record)
        _, invalid_body, invalid_record = json_call(
            client,
            server.base_url,
            "POST",
            "/api/prepare",
            files=upload_files(**fixtures),
            data={
                "identity": "Synthetic fixture performer",
                "seed": "50",
                "rights_attested": "invalid",
            },
        )
        records.append(invalid_record)
        if missing_record["status_code"] != 422 or invalid_record["status_code"] != 422:
            raise RuntimeError("Rights gate did not reject missing or invalid attestation")

        job_id = prepare_valid_job(client, server.base_url, fixtures, records)
        workflow_response = client.get(f"{server.base_url}/api/jobs/{job_id}/workflow", timeout=2)
        prompt_response = client.get(f"{server.base_url}/api/jobs/{job_id}/prompt", timeout=2)
        workflow_path = output_dir / "workflow.json"
        prompt_path = output_dir / "prompt.txt"
        if workflow_response.status_code != 200 or prompt_response.status_code != 200:
            raise RuntimeError("Prepared workflow or prompt download failed")
        workflow_path.write_bytes(workflow_response.content)
        prompt_path.write_bytes(prompt_response.content)

        queued_response, queued_body, queued_record = json_call(
            client, server.base_url, "POST", f"/api/jobs/{job_id}/run"
        )
        records.append(queued_record)
        status, observations = wait_for_terminal_status(client, server.base_url, job_id)
        records.extend(observations)
        if queued_response.status_code != 200 or status["state"] != "complete":
            raise RuntimeError(f"Dry-run path failed: {status}")

        artifacts: dict[str, dict] = {}
        for artifact, filename in {
            "generated": "generated.mp4",
            "final": "final.mp4",
            "side_by_side": "source_vs_final.mp4",
        }.items():
            response = client.get(
                f"{server.base_url}/api/jobs/{job_id}/artifacts/{artifact}", timeout=5
            )
            if response.status_code != 200:
                raise RuntimeError(f"Artifact download failed for {artifact}: {response.status_code}")
            path = output_dir / filename
            path.write_bytes(response.content)
            artifacts[artifact] = artifact_record(path, response)

        return {
            "base_url": server.base_url,
            "job_id": job_id,
            "rights_gate": {
                "missing_status": missing_record["status_code"],
                "missing_body": missing_body,
                "invalid_status": invalid_record["status_code"],
                "invalid_body": invalid_body,
            },
            "workflow": {
                "path": str(workflow_path),
                "bytes": workflow_path.stat().st_size,
                "sha256": sha256(workflow_path),
            },
            "prompt": {
                "path": str(prompt_path),
                "bytes": prompt_path.stat().st_size,
                "sha256": sha256(prompt_path),
            },
            "queued": queued_body,
            "status": status,
            "artifacts": artifacts,
        }


def run_sdk_fail_closed_evidence(
    server: Server, fixtures: dict[str, Path], records: list[dict]
) -> dict:
    with requests.Session() as client:
        response, body, record = json_call(client, server.base_url, "GET", "/api/health")
        records.append(record)
        assert response.status_code == 200 and body["backend"] == "sdk"
        job_id = prepare_valid_job(client, server.base_url, fixtures, records)
        queued_response, queued_body, queued_record = json_call(
            client, server.base_url, "POST", f"/api/jobs/{job_id}/run"
        )
        records.append(queued_record)
        status, observations = wait_for_terminal_status(client, server.base_url, job_id)
        records.extend(observations)
        if queued_response.status_code != 200 or status["state"] != "error":
            raise RuntimeError(f"SDK fail-closed path did not fail: {status}")
        return {
            "base_url": server.base_url,
            "job_id": job_id,
            "queued": queued_body,
            "status": status,
        }


def write_transcript(path: Path, receipt: dict) -> None:
    dry = receipt["dry_run"]
    sdk = receipt["sdk_fail_closed"]
    lines = [
        "# OJ-vwzl API E2E transcript",
        "",
        "## Commands",
        "",
        "```sh",
        "cd <workspace>",
        "python tools/e2e_smoke.py --output-dir <output-dir> "
        f"--dry-port {dry['base_url'].rsplit(':', 1)[-1]} "
        f"--sdk-port {sdk['base_url'].rsplit(':', 1)[-1]}",
        "```",
        "",
        "The driver starts isolated Uvicorn processes with `RECASTROOM_BACKEND=dry_run` and "
        "`RECASTROOM_BACKEND=sdk`, and removes `COMFY_API_KEY`, `OPENJUTSU_COMFY_API_KEY`, "
        "`RECASTROOM_COMFY_API_KEY`, and `COMFY_BASE_URL` from each child process environment "
        "without printing values.",
        "",
        "## Dry-run job",
        "",
        f"- health backend: `dry_run`",
        f"- missing-rights response: `{dry['rights_gate']['missing_status']}`",
        f"- invalid-rights response: `{dry['rights_gate']['invalid_status']}`",
        f"- prepared job: `{dry['job_id']}`",
        f"- terminal state: `{dry['status']['state']}`",
        f"- prompt ID: `{dry['status']['prompt_id']}`",
        "",
        "| artifact | bytes | SHA-256 | HTTP |",
        "|---|---:|---|---:|",
    ]
    for name, artifact in dry["artifacts"].items():
        lines.append(
            f"| `{name}` | {artifact['bytes']} | `{artifact['sha256']}` | "
            f"{artifact['http_status']} |"
        )
    lines.extend(
        [
            "",
            "## SDK fail-closed job",
            "",
            f"- health backend: `sdk`",
            f"- prepared job: `{sdk['job_id']}`",
            f"- terminal state: `{sdk['status']['state']}`",
            f"- error code: `{sdk['status']['error']['error']['code']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dry-port", type=int, default=8871)
    parser.add_argument("--sdk-port", type=int, default=8872)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    api_dir = output_dir / "api"
    if api_dir.exists() and any(api_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty evidence directory: {api_dir}")
    api_dir.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "source": REPO / "tests/fixtures/synthetic_source.mp4",
        "reference": REPO / "tests/fixtures/synthetic_reference.png",
        "words": REPO / "tests/fixtures/word_timings.json",
    }

    records: list[dict] = []
    dry_server = Server(
        "dry_run", args.host, args.dry_port, output_dir / "server-data-dry-run", api_dir / "dry-run-server.log"
    )
    sdk_server: Server | None = None
    try:
        dry_server.wait()
        dry = run_dry_run_evidence(dry_server, api_dir, fixtures, records)
        sdk_server = Server(
            "sdk", args.host, args.sdk_port, output_dir / "server-data-sdk", api_dir / "sdk-server.log"
        )
        sdk_server.wait()
        sdk = run_sdk_fail_closed_evidence(sdk_server, fixtures, records)
    finally:
        dry_server.stop()
        if sdk_server is not None:
            sdk_server.stop()
    shutil.rmtree(output_dir / "server-data-dry-run", ignore_errors=True)
    shutil.rmtree(output_dir / "server-data-sdk", ignore_errors=True)

    fixture_receipts = {
        name: {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "ffprobe": probe(path) if path.suffix.lower() in {".mp4", ".png", ".jpg"} else None,
        }
        for name, path in fixtures.items()
    }
    receipt = {
        "schema_version": "openjutsu.e2e-smoke.v1",
        "backend": {"dry_run": "complete", "sdk": "fail_closed_before_network"},
        "fixtures": fixture_receipts,
        "dry_run": dry,
        "sdk_fail_closed": sdk,
        "requests_and_status_observations": records,
    }
    receipt = redact_local_paths(
        receipt,
        [
            (REPO, "<workspace>"),
            (output_dir, "<output-dir>"),
        ],
    )
    (api_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_transcript(api_dir / "TRANSCRIPT.md", receipt)
    print(json.dumps({"ok": True, "receipt": str(api_dir / "receipt.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
