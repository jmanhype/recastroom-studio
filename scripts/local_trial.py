#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Start a loopback-only dry-run trial and record reviewer-safe evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Iterable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import requests  # noqa: E402

from tools.audit_release import (  # noqa: E402
    ABSOLUTE_PATH,
    CREDENTIAL,
    PLACEHOLDERS,
    PRIVATE_NETWORK,
)
from tools.e2e_smoke import Server, sha256, upload_files  # noqa: E402


DEFAULT_OUTPUT = REPO / "docs/evidence/OJ-2t3g-local-trial"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
TEXT_SUFFIXES = {
    ".html", ".json", ".log", ".md", ".py", ".sh", ".txt", ".toml", ".yaml", ".yml"
}
SECRET_SUFFIXES = {".env", ".key", ".pem", ".secrets"}
SECRET_BASENAMES = {"secrets.yaml", "secrets.local.yaml"}


def require_loopback_host(host: str) -> None:
    """Reject bind addresses that could expose the unauthenticated trial app."""
    if host not in LOOPBACK_HOSTS:
        supported = ", ".join(sorted(LOOPBACK_HOSTS))
        raise ValueError(f"local trial host must be loopback ({supported}); got {host}")


def body_record(response: requests.Response) -> dict[str, object]:
    try:
        body: object = response.json()
    except ValueError:
        body = response.text
    if isinstance(body, str):
        body = {
            "text_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "text_bytes": len(body.encode("utf-8")),
        }
    return {"body": body}


def record(
    method: str, path: str, response: requests.Response, checks: list[str]
) -> dict[str, object]:
    return {
        "method": method,
        "path": path,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        **body_record(response),
        "checks": checks,
    }


def upload_probe(
    client: requests.Session,
    base_url: str,
    *,
    rights: str | None,
    fixtures: dict[str, Path],
) -> tuple[requests.Response, object, dict[str, object]]:
    data = {"identity": "Synthetic fixture performer", "seed": "50"}
    if rights is not None:
        data["rights_attested"] = rights
    response = client.post(
        f"{base_url}/api/prepare",
        files=upload_files(**fixtures),
        data=data,
        timeout=5,
    )
    try:
        body: object = response.json()
    except ValueError:
        body = response.text
    path = "/api/prepare"
    return response, body, record("POST", path, response, [])


def wait_for_complete(
    client: requests.Session, base_url: str, job_id: str
) -> tuple[dict[str, object], list[dict[str, object]]]:
    observations: list[dict[str, object]] = []
    for _ in range(150):
        response = client.get(f"{base_url}/api/jobs/{job_id}/status", timeout=2)
        response.raise_for_status()
        status = response.json()
        observations.append(
            {
                "method": "GET",
                "path": f"/api/jobs/{job_id}/status",
                "status_code": response.status_code,
                "body": status,
            }
        )
        if status["state"] == "complete":
            return status, observations
        if status["state"] == "error":
            raise RuntimeError(f"dry-run generation failed: {status}")
        time.sleep(0.1)
    raise RuntimeError("dry-run generation did not reach a terminal state")


def sanitize_text(text: str, roots: Iterable[Path]) -> str:
    replacements = sorted(
        ((str(root.resolve()), f"<{label}>") for root, label in roots),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for original, placeholder in replacements:
        text = text.replace(original, placeholder)
    return text


def finding(path: Path, kind: str, line: int | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "path": path.relative_to(REPO).as_posix(),
        "kind": kind,
    }
    if line is not None:
        result["line"] = line
    return result


def scan_exposure(paths: Iterable[Path]) -> list[dict[str, object]]:
    """Scan text, binary, artifact, and log bytes for credential/path leakage."""
    findings: list[dict[str, object]] = []
    for path in sorted(set(paths)):
        if not path.is_file() or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.suffix.lower() in SECRET_SUFFIXES or path.name.lower() in SECRET_BASENAMES:
            findings.append(finding(path, "credential-like-filename"))
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            lowered = raw.lower()
            if b"/users/" in lowered or b"c:\\users\\" in lowered:
                findings.append(finding(path, "absolute-user-path"))
            if (
                b"comfy_api_key=" in lowered
                or b"openjutsu_comfy_api_key=" in lowered
                or b"recastroom_comfy_api_key=" in lowered
            ):
                findings.append(finding(path, "credential-assignment-bytes"))
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            for line_number, line in enumerate(text.splitlines(), start=1):
                if ABSOLUTE_PATH.search(line) or PRIVATE_NETWORK.search(line):
                    findings.append(finding(path, "absolute-or-private-network-path", line_number))
                for match in CREDENTIAL.finditer(line):
                    value = match.group(1).lower()
                    if not any(placeholder in value for placeholder in PLACEHOLDERS):
                        findings.append(finding(path, "possible-credential-value", line_number))
                        break
    return findings


def scan_targets(output_dir: Path) -> list[Path]:
    roots = [
        REPO / "app",
        REPO / "docs",
        REPO / "scripts",
        REPO / "src",
        REPO / "tests/fixtures",
        REPO / "tools",
        REPO / "workflows",
        output_dir,
    ]
    return [path for root in roots if root.exists() for path in root.rglob("*")]


def write_exposure_report(path: Path, scanned_files: int, findings: list[dict[str, object]]) -> None:
    payload = {
        "schema_version": "openjutsu.local-trial-secret-scan.v1",
        "scope": [
            "app",
            "docs",
            "scripts",
            "src",
            "tests/fixtures",
            "tools",
            "workflows",
            "generated-local-trial-artifacts-and-logs",
        ],
        "scanned_files": scanned_files,
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_trial(host: str, port: int, output_dir: Path) -> dict[str, object]:
    require_loopback_host(host)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty evidence directory: {output_dir}")
    output_dir.mkdir(parents=True)
    data_dir = output_dir / ".server-data"
    log_path = output_dir / "server.log"
    fixtures = {
        "source": REPO / "tests/fixtures/synthetic_source.mp4",
        "reference": REPO / "tests/fixtures/synthetic_reference.png",
        "words": REPO / "tests/fixtures/word_timings.json",
    }
    server = Server("dry_run", host, port, data_dir, log_path)
    probes: list[dict[str, object]] = []
    try:
        server.wait()
        base_url = server.base_url
        with requests.Session() as client:
            health = client.get(f"{base_url}/api/health", timeout=2)
            probes.append(record("GET", "/api/health", health, ["status_code == 200", "backend == dry_run", "workflow_exists == true"]))
            if health.status_code != 200 or health.json() != {
                "ok": True,
                "workflow": "openjutsu_h3_lipsync_local.json",
                "workflow_exists": True,
                "backend": "dry_run",
            }:
                raise RuntimeError(f"health probe failed: {health.text}")

            home = client.get(base_url + "/", timeout=2)
            home_text = home.text
            probes.append(
                {
                    "method": "GET",
                    "path": "/",
                    "status_code": home.status_code,
                    "content_type": home.headers.get("content-type", ""),
                    "body": {
                        "text_sha256": hashlib.sha256(home_text.encode("utf-8")).hexdigest(),
                        "contains_rights_gate": 'name="rights_attested"' in home_text,
                    },
                    "checks": ["status_code == 200", "html content type", "rights_attested control present"],
                }
            )
            if home.status_code != 200 or "text/html" not in home.headers.get("content-type", ""):
                raise RuntimeError(f"home probe failed: {home.status_code}")
            if 'name="rights_attested"' not in home_text:
                raise RuntimeError("home page does not expose the operator attestation control")

            rejected, rejected_body, rejected_record = upload_probe(
                client, base_url, rights=None, fixtures=fixtures
            )
            probes.append(rejected_record)
            if rejected.status_code != 422 or rejected_body != {"detail": "Operator attestation is required."}:
                raise RuntimeError(f"rights rejection probe failed: {rejected.text}")

            prepared, prepared_body, prepared_record = upload_probe(
                client, base_url, rights="true", fixtures=fixtures
            )
            probes.append(prepared_record)
            if prepared.status_code != 200:
                raise RuntimeError(f"prepare probe failed: {prepared.text}")
            job_id = prepared_body["job_id"]  # type: ignore[index]
            queued = client.post(f"{base_url}/api/jobs/{job_id}/run", timeout=2)
            probes.append(record("POST", f"/api/jobs/{job_id}/run", queued, ["status_code == 200", "state == queued"]))
            if queued.status_code != 200 or queued.json()["state"] != "queued":
                raise RuntimeError(f"generation queue probe failed: {queued.text}")
            status, observations = wait_for_complete(client, base_url, job_id)
            probes.extend(observations)
    finally:
        server.stop()
        shutil.rmtree(data_dir, ignore_errors=True)
        log_path.write_text(
            sanitize_text(
                log_path.read_text(encoding="utf-8", errors="replace"),
                [(REPO, "workspace"), (output_dir, "evidence")],
            ),
            encoding="utf-8",
        )

    receipt = {
        "schema_version": "openjutsu.local-trial.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": f"http://{host}:{port}",
        "binding": {"host": host, "scope": "loopback-only"},
        "backend": "dry_run",
        "public_url": None,
        "credential_environment_forwarded": False,
        "gpu_or_cloud_backend_selected": False,
        "fixture_hashes": {name: sha256(path) for name, path in fixtures.items()},
        "job_id": job_id,
        "terminal_status": status,
        "probes": probes,
        "exposure_report": "secret-scan.json",
    }
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    targets = scan_targets(output_dir)
    findings = scan_exposure(targets)
    write_exposure_report(output_dir / "secret-scan.json", len(targets), findings)
    if findings:
        raise RuntimeError(f"exposure scan found {len(findings)} issue(s); see secret-scan.json")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8890)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    receipt = run_trial(args.host, args.port, args.output_dir.resolve())
    print(
        json.dumps(
            {
                "ok": True,
                "base_url": receipt["base_url"],
                "job_id": receipt["job_id"],
                "terminal_state": receipt["terminal_status"]["state"],  # type: ignore[index]
                "receipt": (args.output_dir.resolve() / "receipt.json").as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(f"local trial failed: {error}", file=sys.stderr)
        raise SystemExit(1)
