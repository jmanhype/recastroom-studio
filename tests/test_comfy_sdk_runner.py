import json
import sys
from types import SimpleNamespace
import hashlib

import pytest

# SPDX-License-Identifier: MIT
from openjutsu.comfy_sdk_runner import ComfySdkConfigurationError, ComfySdkRunner


def deny_client_construction(monkeypatch) -> None:
    class ClientShouldNotBeConstructed:
        def __init__(self, **kwargs):
            raise AssertionError("configuration validation must fail first")

    monkeypatch.setitem(sys.modules, "comfy_sdk", SimpleNamespace(Comfy=ClientShouldNotBeConstructed))


def install_fake_comfy(monkeypatch) -> list[object]:
    constructed: list[object] = []

    class FakeComfy:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            constructed.append(self)

    monkeypatch.setitem(sys.modules, "comfy_sdk", SimpleNamespace(Comfy=FakeComfy))
    return constructed


@pytest.mark.parametrize(
    ("explicit_key", "expected_key"),
    [
        ("explicit-key-for-test", "explicit-key-for-test"),
        (None, "environment-key-for-test"),
    ],
)
def test_resolved_api_key_is_forwarded_to_comfy(
    monkeypatch, explicit_key, expected_key
):
    constructed = install_fake_comfy(monkeypatch)
    monkeypatch.setenv("COMFY_BASE_URL", "https://deployment.example")
    monkeypatch.setenv("COMFY_API_KEY", "environment-key-for-test")

    runner = ComfySdkRunner(api_key=explicit_key)

    assert len(constructed) == 1
    assert runner.client.kwargs == {
        "api_key": expected_key,
        "client_info": "recastroom-studio",
    }


def test_explicit_deployment_url_is_used_without_environment_fallback(monkeypatch):
    constructed = install_fake_comfy(monkeypatch)
    monkeypatch.delenv("COMFY_BASE_URL", raising=False)

    runner = ComfySdkRunner(
        api_key="configuration-present-for-test",
        base_url="https://resolved-deployment.example",
    )

    assert len(constructed) == 1
    assert runner._endpoint_fingerprint == hashlib.sha256(
        b"https://resolved-deployment.example"
    ).hexdigest()


def test_missing_api_key_fails_closed_before_client_construction(monkeypatch):
    deny_client_construction(monkeypatch)
    monkeypatch.setenv("COMFY_BASE_URL", "https://deployment.example")
    monkeypatch.delenv("COMFY_API_KEY", raising=False)

    with pytest.raises(ComfySdkConfigurationError) as excinfo:
        ComfySdkRunner(api_key=None)

    error = excinfo.value
    assert error.code == "missing_comfy_api_key"
    assert error.environment_variable == "COMFY_API_KEY"
    assert json.dumps(error.as_dict(), sort_keys=True) == json.dumps(
        {
            "error": {
                "code": "missing_comfy_api_key",
                "message": "A Comfy API deployment requires an API key; no key was supplied.",
                "environment_variable": "COMFY_API_KEY",
            }
        },
        sort_keys=True,
    )


def test_missing_deployment_fails_closed_before_client_construction(monkeypatch):
    deny_client_construction(monkeypatch)
    monkeypatch.delenv("COMFY_BASE_URL", raising=False)

    with pytest.raises(ComfySdkConfigurationError) as excinfo:
        ComfySdkRunner(api_key="configuration-present-for-test")

    error = excinfo.value
    assert error.code == "missing_comfy_base_url"
    assert error.environment_variable == "COMFY_BASE_URL"
    payload = error.as_dict()
    assert payload["error"]["code"] == "missing_comfy_base_url"
    assert json.dumps(payload, sort_keys=True)
