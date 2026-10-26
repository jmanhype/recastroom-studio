# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any
import urllib.parse

import requests


@dataclass
class ComfyLegacyResult:
    prompt_id: str
    outputs: list[dict[str, Any]]
    history: dict[str, Any]


class ComfyLegacyRunner:
    """Small, explicit client for a self-hosted ComfyUI HTTP API."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 120,
        poll_interval: float = 5.0,
        max_wait_seconds: float = 7200,
        client_name: str = "recastroom-studio",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_wait_seconds = max_wait_seconds
        self.client_name = client_name

    def system_stats(self) -> dict[str, Any]:
        response = requests.get(self.base_url + "/system_stats", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def upload(self, path: str | Path) -> str:
        upload_path = Path(path)
        with upload_path.open("rb") as handle:
            response = requests.post(
                self.base_url + "/upload/image",
                files={"image": (upload_path.name, handle)},
                data={"overwrite": "true"},
                timeout=max(self.timeout, 600),
            )
        response.raise_for_status()
        payload = response.json()
        name = payload.get("name")
        if not name:
            raise RuntimeError(f"ComfyUI upload returned no name: {payload}")
        return name

    def queue(self, workflow: dict[str, Any]) -> str:
        response = requests.post(
            self.base_url + "/prompt",
            json={"prompt": workflow, "client_id": self.client_name},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("node_errors"):
            raise RuntimeError(json.dumps(payload["node_errors"], indent=2))
        prompt_id = payload.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI returned no prompt_id: {payload}")
        return prompt_id

    def history(self, prompt_id: str) -> dict[str, Any] | None:
        response = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=self.timeout)
        response.raise_for_status()
        return response.json().get(prompt_id)

    def wait(self, prompt_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.max_wait_seconds
        while time.monotonic() < deadline:
            entry = self.history(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(json.dumps(entry, indent=2))
                if status.get("completed"):
                    return entry
            time.sleep(self.poll_interval)
        raise TimeoutError(prompt_id)

    @staticmethod
    def output_items(history: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for node in history.get("outputs", {}).values():
            for key in ("gifs", "videos", "images"):
                for item in node.get(key, []) or []:
                    if item.get("type") == "output":
                        items.append(item)
        return items

    def download(self, item: dict[str, Any], destination: str | Path) -> Path:
        query = urllib.parse.urlencode(item)
        response = requests.get(
            self.base_url + "/view",
            params=dict(urllib.parse.parse_qsl(query)),
            timeout=max(self.timeout, 600),
        )
        response.raise_for_status()
        output = Path(destination)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)
        return output

    def run(self, workflow: dict[str, Any]) -> ComfyLegacyResult:
        prompt_id = self.queue(workflow)
        history = self.wait(prompt_id)
        return ComfyLegacyResult(prompt_id=prompt_id, outputs=self.output_items(history), history=history)
