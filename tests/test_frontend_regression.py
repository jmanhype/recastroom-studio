# SPDX-License-Identifier: MIT
from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from openjutsu.config import load_settings


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "tests/fixtures/synthetic_source.mp4"
REFERENCE = REPO / "tests/fixtures/synthetic_reference.png"
WORDS = REPO / "tests/fixtures/word_timings.json"
ARTIFACTS = ("generated", "final", "side_by_side")
SCENE_UI_INVENTORY = (
    "A rights-aware workspace for MiniMax H3.",
    "PERMISSION BEFORE PRODUCTION",
    "Consent is part of the craft.",
    "RecastRoom Studio is a rights aware Comfy workspace for MiniMax H3 performance recasting. Keep the take, camera, timing, and exact source audio while an authorized reference becomes the new lead.",
    "A rights aware MiniMax H3 recasting workspace with exact source audio restoration, frame by frame review, and an open Comfy workflow.",
    "RecastRoom is a rights aware Comfy workspace. The source take stays intact while an authorized reference becomes the new lead.",
    "Rights are a production state",
    "Attestation gate",
    "These are rights-clean keeper comparisons from the evidence corpus.",
    "No attestation, no render",
    "Run one rights aware proof",
    "Start a rights aware dry run",
)
LEGACY_AUDIO_CLAIMS = (
    "23.8 second proof · exact source audio restored · local deterministic review",
    "Exact audio lock",
    "The final render restores the original decoded audio",
    "Exact audio restoration",
    "The accepted proof restores the source dialogue",
    "The accepted proof path restores the original decoded audio",
)


class ControlsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: dict[str, dict[str, str | None]] = {}
        self.labels: dict[str, str] = {}
        self._label_for: str | None = None
        self._label_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if tag in {"a", "button", "input", "summary", "textarea", "video"} and element_id:
            self.elements[element_id] = {
                "tag": tag,
                "type": values.get("type"),
                "required": "required" if "required" in values else None,
                "controls": "controls" if "controls" in values else None,
                "hidden": values.get("hidden"),
            }
        if tag == "label":
            self._label_for = values.get("for")
            self._label_text = []

    def handle_data(self, data: str) -> None:
        if self._label_for is not None:
            self._label_text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "label" and self._label_for is not None:
            self.labels[self._label_for] = " ".join(
                fragment for fragment in self._label_text if fragment
            )
            self._label_for = None


def uploads() -> dict[str, tuple[str, bytes, str]]:
    return {
        "source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4"),
        "reference_1": (REFERENCE.name, REFERENCE.read_bytes(), "image/png"),
        "words": (WORDS.name, WORDS.read_bytes(), "application/json"),
    }


def prepare_request(client: TestClient, rights_attested: str = "true"):
    return client.post(
        "/api/prepare",
        files=uploads(),
        data={
            "identity": "Synthetic fixture performer",
            "seed": "50",
            "rights_attested": rights_attested,
        },
    )


@pytest.fixture
def studio(tmp_path: Path):
    import app.main as main

    original_settings = main.SETTINGS
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = load_settings(
        {"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path)}
    )
    main.JOB_STATUS.clear()
    main.JOB_LOCKS.clear()
    try:
        with TestClient(main.app) as client:
            yield main, client
    finally:
        main.SETTINGS = original_settings
        main.JOB_STATUS.clear()
        main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear()
        main.JOB_LOCKS.update(original_locks)


def test_served_ui_discloses_consent_no_ai_and_truthful_controls(studio):
    _, client = studio

    home = client.get("/")
    script = client.get("/studio.js")
    m1_script = client.get("/m1.js")
    stylesheet = client.get("/styles.css")
    assert home.status_code == 200
    assert script.status_code == 200
    assert m1_script.status_code == 200
    assert stylesheet.status_code == 200
    assert home.headers["content-type"].startswith("text/html")
    assert script.headers["content-type"].startswith(("application/javascript", "text/javascript"))
    assert stylesheet.headers["content-type"].startswith("text/css")

    parser = ControlsParser()
    parser.feed(home.text)
    for control in ("source", "reference_1", "rights", "submit", "reset", "run", "retry-status"):
        assert control in parser.elements
    assert parser.elements["source"]["required"] is not None
    assert parser.elements["reference_1"]["required"] is not None
    assert parser.elements["rights"] == {
        "tag": "input",
        "type": "checkbox",
        "required": "required",
        "controls": None,
        "hidden": None,
    }
    assert "explicit permission" in parser.labels["rights"]
    assert 'id="workflow-catalog"' in home.text
    assert 'id="workflow-note"' in home.text
    assert 'id="readiness"' in home.text
    assert 'id="recorded-proof"' in home.text
    assert "Recorded hosted H3 proof" in home.text
    assert "This result was recorded on October 30" in home.text
    assert 'id="quickstart"' in home.text
    assert 'id="walkthrough"' in home.text
    assert 'id="advanced-studio"' in home.text
    assert "Set up studio" in home.text
    assert "Choose the performance" in home.text
    assert "Add the new lead" in home.text
    assert "Confirm and prepare" in home.text
    assert 'id="walkthrough" class="walkthrough" hidden role="dialog"' in home.text
    assert 'data-required="true"' in home.text
    assert "REQUIRED · 4 STEPS" in home.text
    assert "Where should recasts run?" in home.text
    assert ">ComfyUI</strong>" in home.text
    assert "Comfy API SDK" in home.text
    assert "Local preview" in home.text
    assert "RunPod" not in home.text
    assert "Restart with the matching mode" in home.text
    assert "This saves a preference" in home.text
    assert "Solo or review handoff?" in home.text
    assert "Reviewer name" in home.text
    assert 'id="walkthrough-skip"' in home.text
    assert ">Skip setup</button>" in home.text
    assert "Open the studio" in home.text
    assert parser.elements["show-walkthrough"]["tag"] == "button"
    assert "Primary reference" in home.text
    assert "ComfyUI" in home.text
    assert "Custom RecastRoom-compatible workflow JSON" in home.text
    assert "Future concepts stay on the roadmap" in home.text
    assert parser.elements["source-preview"]["controls"] is not None
    assert parser.elements["final-preview"]["controls"] is not None
    assert "no automated score is provided" in home.text

    js = script.text
    assert "$('rights').checked" in js
    assert "['source', 'reference_1', 'reference_2'].includes(event.target.id)" in js
    assert "$('rights').checked = false" in js
    assert "!ready || busy || !health?.ok || !health?.workflow_exists" in js
    assert "!job || !recommended || busy || running || !runConnectionReady()" in js
    assert "Preview only: copies source media. No AI inference or recasting." in js
    assert "Preview complete · no AI inference or recasting · output copies the source." in js
    assert "status.state === 'complete' && status.backend === 'dry_run'" in js
    assert "Preview copy · no AI inference" in js
    assert "Final · original audio restored" in js
    assert "request('/api/proof/comfy-api-sdk-c1')" in js
    assert "function renderPreparedContract(contract)" in js
    assert "contract.timing?.status" in js
    assert "contract.timing?.schedule" in js
    assert "configuration_ready === true" in js
    assert "Hosted Comfy configuration incomplete" in js
    assert "SDK submission recovery" in client.get("/").text
    assert "SDK outcome is unknown" in js
    assert "guardedSdkStateRefusal" in js
    assert "status.state === 'complete'" in js
    assert "if (!status.artifacts?.[key]) continue" in js
    assert "status.state === 'error'" in js
    assert "Status unavailable:" in js
    assert "do not submit a duplicate run" in js
    assert "$('retry-status').hidden = false" in js
    assert "Prepare a new job" in js
    assert "const isCurrent = (version, id = job)" in js
    assert "epoch += 1" in js
    assert "window.StudioUI = Object.freeze({" in js
    assert "getReadiness: readinessStates" in js
    assert "updateReadiness();" in js
    assert "request('/api/workflows')" in js
    assert "filter((item) => item.available === true)" in js
    assert "moveAdvancedPanels" in js
    assert "closeWalkthrough" in js
    assert "finishWalkthrough" in js
    assert "skipWalkthrough" in js
    assert "skipped: true" in js
    assert "SETUP_KEY = 'recastroom-setup-v1'" in js
    assert "COLLAB_KEY = 'recastroom-collab-v1'" in js
    assert "function updateConnectionGuidance()" in js
    assert "RECASTROOM_BACKEND=sdk COMFY_API_KEY=<your-key>" in js
    assert "COMFY_BASE_URL=https://<deployment>.run.comfy.app" in js
    assert "COMFY_SDK_ASSET_BRIDGE=openjutsu-v1" in js
    assert "copy-runtime-command" in js
    assert "Required first-run setup cannot be dismissed by clicking the backdrop." in js
    assert "if (!$('walkthrough').hidden) return;" in js
    assert "collab?.mode === 'handoff'" in m1_script.text
    assert "attributedNote" in m1_script.text
    assert "guideTo(button.dataset.guideTarget)" in js
    assert "selectedWorkflow = 'recast-room'" in js
    assert "$('advanced').open = true" in js
    for historical_mutation in (
        "setStage",
        "renderStatus",
        "renderPrepareResult",
        "resetStaleJob",
    ):
        assert historical_mutation not in js
    assert not re.search(r"(?i)\b(percent|eta|qc|quality score)\b", js)

    css = stylesheet.text
    assert ":focus-visible" in css
    assert "outline:2px solid var(--accent)" in css
    assert "@media(prefers-reduced-motion:reduce)" in css
    assert "animation:none!important" in css
    assert "transition:none!important" in css


def test_landing_leads_with_workflow_and_scopes_audio_proof(studio):
    _, client = studio

    landing = client.get("/landing.html")
    assert landing.status_code == 200
    assert landing.headers["content-type"].startswith("text/html")

    home = client.get("/")
    assert home.status_code == 200
    served_ui = home.text + landing.text
    for promotional_copy in SCENE_UI_INVENTORY:
        assert promotional_copy not in served_ui
    for legacy_audio_claim in LEGACY_AUDIO_CLAIMS:
        assert legacy_audio_claim not in landing.text

    assert "Keep the performance, camera, timing, and original dialogue" in home.text
    assert "Discovery metadata does not bypass the permission checkpoint." in home.text
    assert "From original shot to final export" in landing.text
    assert "Advanced project tools record source cuts, take selections, and export checks" in landing.text
    assert "23.8-second public example" in landing.text
    assert "Shot / take / export" in landing.text
    assert "review output restores the original source audio" in landing.text
    assert "advanced exports follow the selected audio policy" in landing.text
    assert "Source and likeness permissions" in landing.text
    assert "cannot prove legal clearance" in landing.text


def test_real_dry_run_flow_requires_consent_and_serves_only_completed_artifacts(studio, tmp_path):
    _, client = studio

    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.json()
    assert {key: health_payload[key] for key in ("ok", "workflow", "workflow_exists", "backend")} == {
        "ok": True,
        "workflow": "recastroom_h3_workflow.json",
        "workflow_exists": True,
        "backend": "dry_run",
    }
    assert health_payload["renderer_ready"] is True
    assert health_payload["renderer"]["code"] == "local_dry_run"

    missing_consent = prepare_request(client, rights_attested="false")
    invalid_consent = prepare_request(client, rights_attested="not-a-boolean")
    assert missing_consent.status_code == 422
    assert missing_consent.json()["detail"] == "Permission declaration is required."
    assert invalid_consent.status_code == 422
    assert not (tmp_path / "uploads").exists()
    assert not (tmp_path / "jobs").exists()

    prepared = prepare_request(client)
    assert prepared.status_code == 200
    payload = prepared.json()
    assert re.fullmatch(r"[a-z0-9]{12}", payload["job_id"])
    assert payload["scene"]["recommended"] is True
    manifest = payload["manifest"]
    assert manifest["rights_attested"] is True
    assert manifest["reference_2"] is None
    assert manifest["word_schedule_path"] == WORDS.name
    assert "/Users/" not in prepared.text

    job_id = payload["job_id"]
    upload_dir = tmp_path / "uploads" / job_id
    assert (upload_dir / SOURCE.name).read_bytes() == SOURCE.read_bytes()
    assert (upload_dir / REFERENCE.name).read_bytes() == REFERENCE.read_bytes()
    assert (upload_dir / WORDS.name).read_bytes() == WORDS.read_bytes()
    workflow = client.get(payload["workflow_url"])
    prompt = client.get(payload["prompt_url"])
    assert workflow.status_code == 200
    assert prompt.status_code == 200
    assert "Synthetic fixture performer" in prompt.text
    assert "rights" in prompt.text and "clean" in prompt.text
    for artifact in ARTIFACTS:
        assert client.get(f"/api/jobs/{job_id}/artifacts/{artifact}").status_code == 404

    run = client.post(f"/api/jobs/{job_id}/run")
    status_response = client.get(f"/api/jobs/{job_id}/status")
    assert run.status_code == 200
    assert run.json() == {"job_id": job_id, "state": "queued"}
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["state"] == "complete"
    assert status["backend"] == "dry_run"
    assert status["prompt_id"].startswith("dry-run-")
    assert set(status["artifacts"]) == set(ARTIFACTS)
    assert not re.search(r"(?i)\b(percent|eta|qc|quality score)\b", status_response.text)

    job_dir = tmp_path / "jobs" / job_id
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert hashlib.sha256((job_dir / "generated.mp4").read_bytes()).hexdigest() == source_hash
    for artifact in ARTIFACTS:
        downloaded = client.get(f"/api/jobs/{job_id}/artifacts/{artifact}")
        assert downloaded.status_code == 200, artifact
        assert downloaded.headers["content-type"].startswith("video/mp4")
        assert downloaded.content


def test_labeled_fault_injection_fails_retry_then_new_job_recovers(studio, tmp_path):
    _, client = studio

    first = prepare_request(client)
    assert first.status_code == 200
    first_job = first.json()["job_id"]
    first_dir = tmp_path / "jobs" / first_job
    first_source = Path(json.loads((first_dir / "job.json").read_text())["source"])
    injection = first_dir / "FAULT-INJECTION-missing-source.txt"
    injection.write_text(
        "Isolated persisted fault injection: this test removes the uploaded source "
        "after prepare. It does not represent real dry-run provider behavior.\n",
        encoding="utf-8",
    )
    first_source.unlink()

    first_run = client.post(f"/api/jobs/{first_job}/run")
    first_status = client.get(f"/api/jobs/{first_job}/status")
    assert first_run.status_code == 200
    assert first_status.json()["state"] == "error"
    assert first_status.json()["backend"] == "dry_run"
    assert first_status.json()["message"]
    assert first_status.json()["artifacts"] == {}
    assert injection.is_file()
    for artifact in ARTIFACTS:
        assert client.get(f"/api/jobs/{first_job}/artifacts/{artifact}").status_code == 404

    retried = client.post(f"/api/jobs/{first_job}/run")
    retry_status = client.get(f"/api/jobs/{first_job}/status")
    assert retried.status_code == 200
    assert retried.json()["state"] == "queued"
    assert retry_status.json()["state"] == "error"
    assert retry_status.json()["job_id"] == first_job

    second = prepare_request(client)
    second_job = second.json()["job_id"]
    assert second_job != first_job
    second_dir = tmp_path / "jobs" / second_job
    assert not (second_dir / injection.name).exists()
    assert client.post(f"/api/jobs/{second_job}/run").status_code == 200
    recovered = client.get(f"/api/jobs/{second_job}/status").json()
    assert recovered["state"] == "complete"
    assert set(recovered["artifacts"]) == set(ARTIFACTS)
    assert client.get(f"/api/jobs/{first_job}/status").json()["state"] == "error"


def test_active_unknown_and_stale_job_guards(studio, tmp_path):
    main, client = studio

    prepared = prepare_request(client)
    job_id = prepared.json()["job_id"]
    active_status = {
        "job_id": job_id,
        "state": "generating",
        "message": "Injected active status for guard testing",
        "artifacts": {},
        "backend": "dry_run",
    }
    marker = tmp_path / "jobs" / job_id / "FAULT-INJECTION-active-status.txt"
    marker.write_text(
        "Isolated persisted state injection: represents an active job only for the "
        "duplicate-run guard. It is not real provider output.\n",
        encoding="utf-8",
    )
    main.JOB_STATUS[job_id] = active_status.copy()
    (tmp_path / "jobs" / job_id / "status.json").write_text(
        json.dumps(active_status) + "\n", encoding="utf-8"
    )

    duplicate = client.post(f"/api/jobs/{job_id}/run")
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Job is already generating"
    assert client.get(f"/api/jobs/{job_id}/status").json()["state"] == "generating"

    unknown = "0123456789ab"
    assert not (tmp_path / "jobs" / unknown).exists()
    assert client.post(f"/api/jobs/{unknown}/run").status_code == 404
    assert client.get(f"/api/jobs/{unknown}/status").status_code == 404
    assert client.get(f"/api/jobs/{unknown}/artifacts/final").status_code == 404
    malformed = "bad%2Aid"
    assert client.post(f"/api/jobs/{malformed}/run").status_code == 404
    assert client.get(f"/api/jobs/{malformed}/status").status_code == 404
    assert client.get(f"/api/jobs/{malformed}/artifacts/generated").status_code == 404
    assert marker.is_file()
