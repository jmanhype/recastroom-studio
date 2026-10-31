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
    environment_variable: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = {
            "backend": self.backend,
            "ready": self.ready,
            "checked": self.checked,
            "code": self.code,
            "message": self.message,
        }
        if self.environment_variable is not None:
            result["environment_variable"] = self.environment_variable
        return result


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


def check_sdk_configuration(
    api_key: str | None,
    base_url: str | None,
    asset_bridge: str | None,
) -> RendererReadiness:
    """Validate local hosted configuration without contacting the provider."""
    resolved_key = (api_key or "").strip()
    if not resolved_key:
        return RendererReadiness(
            backend="sdk",
            ready=False,
            checked=True,
            code="missing_comfy_api_key",
            message="A Comfy API deployment requires an API key; no key was supplied.",
            environment_variable="COMFY_API_KEY",
        )
    resolved_base_url = (base_url or "").strip()
    if not resolved_base_url:
        return RendererReadiness(
            backend="sdk",
            ready=False,
            checked=True,
            code="missing_comfy_base_url",
            message="A Comfy API deployment URL is required to avoid silently targeting Comfy Cloud.",
            environment_variable="COMFY_BASE_URL",
        )
    if asset_bridge != "openjutsu-v1":
        return RendererReadiness(
            backend="sdk",
            ready=False,
            checked=True,
            code="sdk_bridge_not_configured",
            message="Set COMFY_SDK_ASSET_BRIDGE=openjutsu-v1 for a deployment containing the RecastRoom asset bridge.",
            environment_variable="COMFY_SDK_ASSET_BRIDGE",
        )
    return RendererReadiness(
        backend="sdk",
        ready=True,
        checked=False,
        code="sdk_configuration_ready",
        message="Hosted configuration is present. Provider reachability and model availability are not checked.",
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
        raise ValueError("call check_sdk_configuration for backend=sdk")
    return RendererReadiness(
        backend=backend,
        ready=False,
        checked=False,
        code="unsupported_backend",
        message="The configured backend is not supported.",
    )
