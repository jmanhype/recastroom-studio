# SPDX-License-Identifier: MIT
"""Real-process utilities shared by the Studio foundation trial."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from typing import Any, Literal

import requests


REPO = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)
HOST = "127.0.0.1"
LOOPBACK_ONLY = True
TRUSTED_TOOL_DIRECTORIES = (
    Path("/opt/homebrew/bin"),
    Path("/usr/local/bin"),
    Path("/usr/bin"),
    Path("/bin"),
)
TRUSTED_TOOL_PATH = ":".join(str(directory) for directory in TRUSTED_TOOL_DIRECTORIES)
TOOL_ENVIRONMENT = {"PATH": TRUSTED_TOOL_PATH}
FIXED_TOOL_NAMES = frozenset(("ffmpeg", "ffprobe"))


def resolve_tool(tool_name: str) -> Path:
    """Resolve one fixed media tool from the explicit trusted search path."""
    if tool_name not in FIXED_TOOL_NAMES:
        raise ValueError(f"Unsupported media tool {tool_name!r}; expected ffmpeg or ffprobe")
    for directory in TRUSTED_TOOL_DIRECTORIES:
        executable = directory / tool_name
        if executable.is_file() and os.access(executable, os.X_OK):
            return executable
    raise RuntimeError(
        f"Required media tool {tool_name!r} was not found in trusted PATH "
        f"{TRUSTED_TOOL_PATH}; install FFmpeg with Homebrew or apt before running tests"
    )


FFMPEG = resolve_tool("ffmpeg")
FFPROBE = resolve_tool("ffprobe")


def sha256_bytes(content: bytes) -> str:
    """Return the public SHA-256 used by project evidence receipts."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash a generated or downloaded media artifact without exposing its path."""
    digest = hashlib.sha256()
    with path.open(mode="rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def child_environment(data_dir: Path) -> dict[str, str]:
    """Build an explicit dry-run environment without inheriting host secrets."""
    return {
        "PATH": TOOL_ENVIRONMENT["PATH"],
        "RECASTROOM_BACKEND": "dry_run",
        "RECASTROOM_DATA_DIR": str(data_dir.resolve()),
        "PYTHONPATH": f"{REPO / 'src'}:{REPO}",
    }


def free_loopback_port() -> int:
    """Reserve a transient port on the loopback interface only."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def sanitize_log(path: Path, roots: tuple[Path, ...]) -> None:
    """Redact local roots before a server log becomes public evidence."""
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    for root in sorted(roots, key=lambda item: len(str(item)), reverse=True):
        text = text.replace(str(root.resolve()), "<local-root>")
    path.write_text(text.replace("/Users/", "<user-root>/"), encoding="utf-8")


def run_tool(arguments: list[str]) -> None:
    """Run only a fixed FFmpeg/ffprobe binary from the trusted search path."""
    if not arguments:
        raise ValueError("No media tool specified; expected ffmpeg or ffprobe")
    executable = resolve_tool(arguments[0])
    subprocess.run(
        [str(executable), *arguments[1:]],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO,
        env=TOOL_ENVIRONMENT,
    )


def generate_media(temp_root: Path) -> dict[str, Path]:
    """Materialize the pinned synthetic media set for portable offline proofs."""
    media_root = temp_root / "input"
    media_root.mkdir(parents=True)
    pinned_root = REPO / "tests" / "fixtures" / "m1"
    source = pinned_root / "foundation-source.mp4"
    primary = pinned_root / "foundation-primary.png"
    secondary = pinned_root / "foundation-secondary.png"
    for original in (source, primary, secondary):
        if not original.is_file():
            raise RuntimeError(f"pinned synthetic media fixture is missing: {original.name}")
        shutil.copyfile(original, media_root / original.name)
    source = media_root / source.name
    primary = media_root / primary.name
    secondary = media_root / secondary.name
    return {"source": source, "primary": primary, "secondary": secondary}


def media_probe(path: Path) -> dict[str, Any]:
    """Return only public ffprobe facts for a real generated/downloaded file."""
    ffprobe = resolve_tool("ffprobe")
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO,
        env=TOOL_ENVIRONMENT,
    )
    payload: dict[str, Any] = json.loads(result.stdout)
    return {
        "format": payload.get("format", {}).get("format_name"),
        "duration_seconds": float(payload.get("format", {}).get("duration", 0)),
        "streams": [
            {
                "codec_type": stream.get("codec_type"),
                "codec_name": stream.get("codec_name"),
                "width": stream.get("width"),
                "height": stream.get("height"),
            }
            for stream in payload.get("streams", [])
        ],
    }


def record(response: requests.Response, body: object) -> dict[str, Any]:
    """Record the request path and response without an absolute local origin."""
    url = response.request.url or ""
    path = "/" + url.split("/", 3)[-1] if "://" in url else url
    return {
        "method": response.request.method,
        "path": path,
        "status_code": response.status_code,
        "body": body,
    }


def call(
    client: requests.Session,
    base_url: str,
    method: str,
    path: str,
    records: list[dict[str, Any]],
    **kwargs: Any,
) -> tuple[requests.Response, object]:
    """Make one real HTTP request and append public-safe evidence."""
    response = client.request(method, base_url + path, timeout=10, **kwargs)
    try:
        body: object = response.json()
    except ValueError:
        body = {"text_sha256": sha256_bytes(response.content), "bytes": len(response.content)}
    records.append(record(response, body))
    return response, body


def require_status(response: requests.Response, expected: int, label: str) -> None:
    """Fail closed unless an HTTP step returns the required status."""
    if response.status_code != expected:
        raise RuntimeError(f"{label} returned HTTP {response.status_code}: {response.text}")


class FoundationServer:
    """One owned actual uvicorn process with strict child environment cleanup."""

    def __init__(self, port: int, data_dir: Path, log_path: Path, *,
                 test_lifespan: Literal["auto", "off"] = "auto") -> None:
        if test_lifespan not in ("auto", "off"):
            raise ValueError("test_lifespan must be auto or off")
        self._test_lifespan = test_lifespan
        self.base_url = f"http://{HOST}:{port}"
        self.data_dir = data_dir
        self.log_path = log_path
        self.process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen(
            [
                str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", HOST,
                "--port", str(self.base_url.rsplit(":", 1)[-1]),
            ] + (["--lifespan", "off"] if self._test_lifespan == "off" else []),
            cwd=REPO,
            env=child_environment(self.data_dir),
            stdout=self.log_path.open(mode="w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )
        self.wait()

    def wait(self) -> dict[str, Any]:
        last_error: Exception | None = None
        for _ in range(120):
            if self.process is not None and self.process.poll() is not None:
                raise RuntimeError(
                    f"uvicorn exited before readiness with code {self.process.returncode}"
                )
            try:
                with requests.Session() as client:
                    response = client.get(f"{self.base_url}/api/health", timeout=0.5)
                if response.status_code == 200:
                    payload = response.json()
                    if payload.get("backend") == "dry_run":
                        return payload
                last_error = RuntimeError(
                    f"health returned {response.status_code}: {response.text}"
                )
            except requests.RequestException as error:
                last_error = error
            time.sleep(0.1)
        self.stop()
        raise RuntimeError(f"actual uvicorn did not become ready: {last_error}")

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process = None
        sanitize_log(self.log_path, (REPO, self.data_dir))


def workspace_counts(data_dir: Path) -> dict[str, int]:
    """Read real persisted SQLite counts after the owned server process stops."""
    database = data_dir.resolve() / "workspace.sqlite3"
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        projects = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        characters = connection.execute("SELECT COUNT(*) FROM character_versions").fetchone()[0]
        prepared = connection.execute("SELECT COUNT(*) FROM prepared_configs").fetchone()[0]
    return {
        "projects": int(projects),
        "character_versions": int(characters),
        "prepared_jobs": int(prepared),
    }


def hash_tree(root: Path) -> dict[str, str]:
    """Hash every persisted workspace file by safe relative name."""
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def wait_complete(
    client: requests.Session, base_url: str, job_id: str, records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Poll the real status endpoint until a terminal state is reached."""
    for _ in range(150):
        response, body = call(client, base_url, "GET", f"/api/jobs/{job_id}/status", records)
        require_status(response, 200, "job status")
        assert isinstance(body, dict)
        if body.get("state") == "complete":
            return body
        if body.get("state") == "error":
            raise RuntimeError(f"dry-run job failed: {body}")
        time.sleep(0.1)
    raise RuntimeError(f"dry-run job {job_id} did not complete")


def assert_public(value: object, roots: tuple[Path, ...]) -> None:
    """Reject local roots and credential names in public evidence."""
    text = json.dumps(value, sort_keys=True)
    forbidden = [str(root.resolve()) for root in roots]
    forbidden += ["/Users/", "COMFY_API_KEY", "OPENJUTSU_COMFY_API_KEY"]
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"public receipt leaked forbidden token {token!r}")
