# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import fcntl
import hashlib
import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .sdk_assets import bind_graph, validate_inputs


class ComfySdkRunError(RuntimeError):
    """Allowlisted messages only; never expose provider exception bodies."""


def _save_state(path, state):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".sdk-state-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class ComfySdkConfigurationError(RuntimeError):
    """A machine-readable, pre-network SDK configuration failure."""

    def __init__(self, code: str, message: str, environment_variable: str) -> None:
        self.code = code
        self.message = message
        self.environment_variable = environment_variable
        super().__init__(f"{code}: {message}")

    def as_dict(self) -> dict[str, dict[str, str]]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "environment_variable": self.environment_variable,
            }
        }


class ComfySdkRunner:
    """Adapter for the official Comfy Python SDK and Comfy API v2 deployments.

    The SDK intentionally does not hide errors behind a generic HTTP client. Set:

        COMFY_API_KEY=...
        COMFY_BASE_URL=https://<your-comfy-developer-platform-deployment>

    Input bytes are explicitly bound via OpenJutsuAssetPlan. See
    docs/deployment/SDK_ASSETS.md for the required deployment bridge and limits.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        client_info: str = "recastroom-studio",
    ) -> None:
        resolved_api_key = api_key or os.environ.get("COMFY_API_KEY")
        if not resolved_api_key or not resolved_api_key.strip():
            raise ComfySdkConfigurationError(
                "missing_comfy_api_key",
                "A Comfy API deployment requires an API key; no key was supplied.",
                "COMFY_API_KEY",
            )
        base_url = (base_url or os.environ.get("COMFY_BASE_URL", "")).strip()
        if not base_url:
            raise ComfySdkConfigurationError(
                "missing_comfy_base_url",
                "A Comfy API deployment URL is required to avoid silently targeting Comfy Cloud.",
                "COMFY_BASE_URL",
            )
        try:
            from comfy_sdk import Comfy
        except ImportError as error:
            raise RuntimeError("Install official Comfy support with: pip install comfy-sdk") from error
        self.client = Comfy(api_key=resolved_api_key, client_info=client_info)
        self._endpoint_fingerprint = hashlib.sha256(base_url.encode()).hexdigest()

    def run_workflow(self, workflow: dict[str, Any], output_dir: str | Path, *,
                     source: str | Path, reference_1: str | Path,
                     reference_2: str | Path | None = None) -> list[Path]:
        plan, files, fingerprint = validate_inputs(workflow, source, reference_1, reference_2)
        if os.environ.get("COMFY_SDK_ASSET_BRIDGE") != "openjutsu-v1":
            raise ComfySdkRunError("SDK asset bridge deployment has not been configured")
        output_path = Path(output_dir)
        if output_path.is_symlink():
            raise ComfySdkRunError("Unsafe SDK output directory")
        output_path.mkdir(parents=True, exist_ok=True)
        state_path = output_path / "submission.json"
        lock_path = output_path / ".submission.lock"
        if state_path.is_symlink() or lock_path.is_symlink():
            raise ComfySdkRunError("Unsafe SDK state path")
        # Local POSIX process lock, not a distributed queue/lease claim.
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                return self._run_locked(workflow, output_path, state_path, plan, files, fingerprint)
            except ComfySdkRunError:
                raise
            except Exception:
                raise ComfySdkRunError("SDK operation failed; submission state retained for recovery") from None

    def _run_locked(self, workflow, output_path, state_path, plan, files, fingerprint):
        endpoint = self._endpoint_fingerprint
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state.get("fingerprint") != fingerprint or state.get("endpoint") != endpoint:
                raise ComfySdkRunError("SDK inputs or deployment changed; existing submission preserved")
            if not state.get("key") or state.get("phase") not in {"prepared", "submitting", "submitted"}:
                raise ComfySdkRunError("SDK submission state invalid; manual reconciliation required")
        else:
            state = {"key": str(uuid.uuid4()), "fingerprint": fingerprint,
                     "endpoint": endpoint, "phase": "prepared", "job_id": None}
            _save_state(state_path, state)
        if state.get("job_id"):
            job = self.client.jobs.get(state["job_id"])
        else:
            if state["phase"] != "prepared":
                raise ComfySdkRunError("SDK submission outcome unknown; manual reconciliation required; not resubmitted")
            graph = bind_graph(self.client, workflow, plan, files)
            state["phase"] = "submitting"
            _save_state(state_path, state)
            # Any failure from this point is conservatively ambiguous, including
            # a crash after response but before the durable ID write.
            job = self.client.submit(graph, idempotency_key=state["key"])
            state.update(job_id=job.id, phase="submitted")
            _save_state(state_path, state)
        job.wait(timeout=3600)
        if job.status != "succeeded":
            raise ComfySdkRunError("SDK job did not succeed; provider job ID retained")
        outputs = [o for o in job.get_outputs("751") if o.name.lower().endswith(".mp4")]
        if len(outputs) != 1:
            raise ComfySdkRunError("SDK generation node 751 must return exactly one MP4")
        output = outputs[0]
        if (Path(output.name).name != output.name or "\\" in output.name or ":" in output.name
                or any(ord(c) < 32 for c in output.name)):
            raise ComfySdkRunError("Unsafe SDK output filename")
        destination = output_path / "generated.mp4"
        if destination.is_symlink():
            raise ComfySdkRunError("Unsafe SDK output path")
        fd, temporary = tempfile.mkstemp(dir=output_path, prefix=".sdk-output-")
        os.close(fd)
        try:
            output.to_file(temporary)
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return [destination]
