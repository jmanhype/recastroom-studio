# SPDX-License-Identifier: MIT
import re

from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_bundled_workflow_without_local_paths() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["workflow"] == "recastroom_h3_workflow.json"
    assert payload["workflow_exists"] is True
    assert "/Users/" not in response.text


def test_home_page_serves_public_ui() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "RecastRoom Studio" in response.text
    assert "Openjutsu Studio" not in response.text
    assert "OPENJUTSU" not in response.text


def test_workflow_catalog_prioritizes_recast_room_without_fake_readiness() -> None:
    client = TestClient(app)

    response = client.get("/api/workflows")

    assert response.status_code == 200
    payload = response.json()
    assert payload["studio"]["name"] == "RecastRoom Studio"
    workflows = {item["id"]: item for item in payload["workflows"]}
    assert workflows["recast-room"]["status"] == "Production"
    assert workflows["recast-room"]["available"] is True
    assert workflows["recast-room"]["model"] == "MiniMax H3 Ref2VA"
    assert workflows["custom-recast"]["available"] is True
    assert workflows["multi-person-recast"]["available"] is False
    assert workflows["multi-person-recast"]["badges"] == [
        "Per-person consent", "Per-person QC", "Not in this release"
    ]
    assert workflows["studio-queue"]["available"] is False
    assert workflows["cinematic-camera"]["available"] is False
    assert workflows["re-shoot"]["available"] is False
    assert workflows["vfx-presets"]["available"] is False
    assert "/Users/" not in response.text


def test_recorded_official_sdk_proof_is_exposed_through_bounded_routes() -> None:
    client = TestClient(app)

    summary = client.get("/api/proof/comfy-api-sdk-c1")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["kind"] == "recorded_hosted_h3_proof"
    assert payload["job_id"] == "233a17e4-253f-4797-baa6-f82a2b3bbbc8"
    assert payload["status"] == "succeeded"
    assert payload["adapter"] == "openjutsu.comfy_sdk_runner.ComfySdkRunner"
    assert payload["output_sha256"] == "f8ed7bcee8f9c2eb83f26d83c763d563e75a3625a1a08829ba32541399dabab8"
    assert payload["audio_verification"] == "decoded source and final PCM SHA-256 identical"
    assert payload["deployment_teardown"] == "deleted"
    assert "credential" not in response_text_lower(payload)
    assert "27.02" not in summary.text

    final = client.get("/api/proof/comfy-api-sdk-c1/media/final.mp4")
    assert final.status_code == 200
    assert final.headers["content-type"].startswith("video/mp4")
    assert len(final.content) == 2478102

    for path in (
        "/api/proof/comfy-api-sdk-c1/media/../receipt.json",
        "/api/proof/comfy-api-sdk-c1/media/unknown.mp4",
        "/api/proof/comfy-api-sdk-c1/media/submission.json",
    ):
        assert client.get(path).status_code == 404


def response_text_lower(payload: dict) -> str:
    return str(payload).lower()


def test_archive_source_discovery_is_key_free_and_rights_explicit(monkeypatch) -> None:
    client = TestClient(app)
    calls = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "response": {
                    "docs": [
                        {
                            "identifier": "GoingSte1951",
                            "title": "Going Steady?",
                            "year": 1951,
                            "downloads": 57577,
                            "licenseurl": "http://creativecommons.org/licenses/publicdomain/",
                        },
                        {"identifier": "unknown-rights", "title": "Unknown Rights"},
                    ]
                }
            }

    def fake_get(url, params=None, timeout=None):
        calls.update({"url": url, "params": params, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr("openjutsu.archive.requests.get", fake_get)

    response = client.get("/api/archive/sources", params={"query": "going steady", "limit": 2})

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "archive.org"
    assert payload["key_required"] is False
    assert calls["url"] == "https://archive.org/advancedsearch.php"
    assert calls["timeout"] == 12
    assert calls["params"]["fl[]"] == (
        "identifier", "title", "year", "downloads", "licenseurl"
    )
    assert calls["params"]["q"] == (
        "collection:prelinger AND mediatype:movies AND (going steady)"
    )
    assert payload["sources"][0]["rights"] == {
        "evidence": "explicit-archive-license",
        "public_domain": True,
        "review_required": False,
    }
    assert payload["sources"][1]["rights"]["review_required"] is True
    assert payload["sources"][1]["rights"]["evidence"] == "archive-license-url-missing"


def test_archive_source_discovery_rejects_unsupported_collections() -> None:
    client = TestClient(app)

    response = client.get("/api/archive/sources", params={"query": "film", "collection": "any-url"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Unsupported Archive.org collection"


def test_reference_preview_images_can_shrink_inside_fixed_grid_boxes() -> None:
    client = TestClient(app)

    home = client.get("/")
    stylesheet = client.get("/styles.css")

    assert home.status_code == 200
    assert home.text.count('class="reference-screen"') == 2
    assert stylesheet.status_code == 200
    container_rule = re.search(r"\.reference-screen\{([^}]*)\}", stylesheet.text)
    image_rules = re.findall(r"\.reference-screen img\{([^}]*)\}", stylesheet.text)
    assert container_rule is not None
    assert len(image_rules) == 2

    declarations = dict(
        declaration.split(":", 1)
        for rule in image_rules
        for declaration in rule.split(";")
    )
    container_declarations = dict(
        declaration.split(":", 1) for declaration in container_rule.group(1).split(";")
    )
    assert container_declarations["display"] == "grid"
    assert container_declarations["overflow"] == "hidden"
    assert declarations["min-width"] == "0"
    assert declarations["min-height"] == "0"
    assert declarations["width"] == "100%"
    assert declarations["height"] == "100%"
    assert declarations["object-fit"] == "contain"


def test_archive_discovery_is_visible_but_never_bypasses_permission_gate() -> None:
    client = TestClient(app)

    home = client.get("/")
    script = client.get("/studio.js")

    assert home.status_code == 200
    assert script.status_code == 200
    assert "Find Archive.org footage" in home.text
    assert 'name="rights_attested"' in home.text
    assert "/api/archive/sources" in script.text
    assert "Discovery metadata does not bypass the permission checkpoint" in home.text


def test_readiness_strip_discloses_dependencies_without_claiming_provider_quality() -> None:
    client = TestClient(app)

    home = client.get("/")
    script = client.get("/studio.js")
    stylesheet = client.get("/styles.css")

    assert home.status_code == 200
    assert script.status_code == 200
    assert stylesheet.status_code == 200
    assert 'id="readiness"' in home.text
    for label in ("Source", "Primary reference", "Permission", "Workflow", "ComfyUI", "Execution"):
        assert f">{label}<" in home.text
    assert "function readinessStates()" in script.text
    assert "function updateReadiness()" in script.text
    assert "updateReadiness();" in script.text
    assert "getReadiness: readinessStates" in script.text
    assert "Preview · no AI inference" in script.text
    assert "Hosted Comfy configured · reachability unchecked" in script.text
    assert "ComfyUI disconnected" in script.text
    assert "Custom workflow pending validation" in script.text
    assert ".readiness-strip" in stylesheet.text
    assert '.readiness-strip>div[data-state="ok"]' in stylesheet.text
    assert '.readiness-strip>div[data-state="blocked"]' in stylesheet.text
    assert not re.search(r"(?i)quality score|percent complete", script.text)
