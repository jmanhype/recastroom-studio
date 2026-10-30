# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import requests


LEGACY_READINESS_TIMEOUT: tuple[float, float] = (0.5, 1.25)


@dataclass(frozen=True)
class RendererReadiness:
    backend: str
    ready: bool
    checked: bool
    code: str
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "ready": self.ready,
            "checked": self.checked,
            "code": self.code,
            "message": self.message,
        }


def _legacy_not_ready(code: str, message: str) -> RendererReadiness:
    return RendererReadiness(
        backend="legacy",
        ready=False,
        checked=True,
        code=code,
        message=message,
    )


def check_legacy_renderer(
    base_url: str,
    *,
    timeout: tuple[float, float] | None = None,
    transport: Callable[..., requests.Response] | None = None,
) -> RendererReadiness:
    """Check only whether the configured legacy ComfyUI HTTP API is reachable."""

    request = transport or _loopback_safe_get
    try:
        response = request(
            base_url.rstrip("/") + "/system_stats",
            timeout=timeout or LEGACY_READINESS_TIMEOUT,
            allow_redirects=False,
        )
    except requests.Timeout:
        return _legacy_not_ready(
            "renderer_timeout",
            "ComfyUI did not respond in time. Restore the connection, then check it again.",
        )
    except requests.RequestException:
        return _legacy_not_ready(
            "renderer_unreachable",
            "ComfyUI is unreachable. Start or reconnect it, then check the connection again.",
        )

    status = response.status_code
    if 300 <= status < 400:
        return _legacy_not_ready(
            "renderer_redirect",
            "ComfyUI returned a redirect instead of system information. Correct its configured address, then check it again.",
        )
    if not 200 <= status < 300:
        return _legacy_not_ready(
            "renderer_http_error",
            f"ComfyUI returned HTTP {status}. Restore it, then check the connection again.",
        )

    try:
        payload = response.json()
    except ValueError:
        return _legacy_not_ready(
            "renderer_malformed_response",
            "ComfyUI returned unreadable system information. Restore or update it, then check it again.",
        )

    if not isinstance(payload, dict):
        return _legacy_not_ready(
            "renderer_schema_mismatch",
            "The endpoint did not return ComfyUI system information. Verify the configured connection, then check it again.",
        )
    system = payload.get("system")
    devices = payload.get("devices")
    if not isinstance(system, dict) or not isinstance(devices, list):
        return _legacy_not_ready(
            "renderer_schema_mismatch",
            "The endpoint did not return the expected ComfyUI system and device fields. Verify the configured connection, then check it again.",
        )

    return RendererReadiness(
        backend="legacy",
        ready=True,
        checked=True,
        code="renderer_reachable",
        message="ComfyUI is reachable. This does not verify models, GPU availability, cost, or generation success.",
    )


def _loopback_safe_get(*args: Any, **kwargs: Any) -> requests.Response:
    # The configured URL is the only intended target; ignore proxy environment
    # settings so a local readiness probe cannot be diverted.
    with requests.Session() as session:
        session.trust_env = False
        return session.get(*args, **kwargs)


def renderer_readiness(
    backend: str,
    comfy_url: str,
    *,
    timeout: tuple[float, float] | None = None,
    transport: Callable[..., requests.Response] | None = None,
) -> RendererReadiness:
    if backend == "legacy":
        return check_legacy_renderer(comfy_url, timeout=timeout, transport=transport)
    if backend == "dry_run":
        return RendererReadiness(
            backend=backend,
            ready=True,
            checked=True,
            code="local_dry_run",
            message="Preview mode is local only and performs no AI inference or renderer connection.",
        )
    if backend == "sdk":
        return RendererReadiness(
            backend=backend,
            ready=False,
            checked=False,
            code="sdk_unchecked",
        message="Hosted Comfy reachability is not checked by this local health endpoint.",
        )
    return RendererReadiness(
        backend=backend,
        ready=False,
        checked=False,
        code="unsupported_backend",
        message="The configured backend is not supported.",
    )
