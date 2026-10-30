# SPDX-License-Identifier: MIT
"""Synthetic-only bridge/file and application wiring checks; no GPU imports."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from openjutsu.sdk_assets import validate_inputs

ROOT = Path(__file__).resolve().parents[1]


def bridge(monkeypatch, root):
    monkeypatch.setitem(sys.modules, "folder_paths", SimpleNamespace(
        get_input_directory=lambda: str(root),
        get_annotated_filepath=lambda name: str(root / name)))
    spec = importlib.util.spec_from_file_location("fixture_bridge", ROOT / "custom_nodes/openjutsu_assets/__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OpenJutsuAssetPlan()


def test_bridge_materializes_exact_bfs_names(monkeypatch, tmp_path):
    node = bridge(monkeypatch, tmp_path)
    for name in ("video.mp4", "ref.png", "ref2.png"):
        (tmp_path / name).write_bytes(b"synthetic")
    plan = {"video": "old", "global_ref": "old", "global_ref2": "old", "global_refs": [],
            "fps": 24, "audio_mode": "auto", "segs": [{"prompt": "unchanged"}]}
    bound = json.loads(node.bind(json.dumps(plan), "video.mp4", "ref.png", "ref2.png")[0])
    assert bound == dict(plan, video="video.mp4", global_ref="ref.png", global_ref2="ref2.png",
                         global_refs=["ref.png", "ref2.png"])
    assert json.loads(node.bind(json.dumps(plan), "video.mp4", "ref.png")[0])["global_ref2"] == ""


@pytest.mark.parametrize("bad", ["../escape.mp4", "/tmp/escape.mp4", "https://host/x", "missing.mp4",
                                {"__type": "core/ASSET"}, "asset-uuid"])
def test_bridge_rejects_unmaterialized_or_unsafe(monkeypatch, tmp_path, bad):
    node = bridge(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        node.bind("{}", bad, "ref.png")


def test_bridge_rejects_symlink_escape(monkeypatch, tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    (tmp_path / "outside").write_bytes(b"synthetic")
    (root / "escape.mp4").symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError):
        bridge(monkeypatch, root).bind("{}", "escape.mp4", "ref.png")


@pytest.mark.parametrize("plan", ["[]", "bad-json", '{}', '{"video": []}'])
def test_invalid_planner_shape(plan):
    workflow = json.loads((ROOT / "workflows/recastroom_h3_workflow.json").read_text())
    workflow["1189"]["inputs"]["plan"] = plan
    with pytest.raises(ValueError, match="Invalid SDK"):
        validate_inputs(workflow, "missing.mp4", "missing.png")


def test_app_passes_manifest_inputs_and_original_audio(monkeypatch, tmp_path):
    import app.main as main
    manifest = {"source": str(tmp_path / "original.mp4"), "reference_1": str(tmp_path / "one.png"),
                "reference_2": str(tmp_path / "two.png"), "rights_attested": True}
    (tmp_path / "job.json").write_text(json.dumps(manifest))
    (tmp_path / "workflow.json").write_text('{}')
    monkeypatch.setattr(main, "_job_dir", lambda job_id: tmp_path)
    calls = {}

    class Runner:
        def __init__(self, **kwargs):
            pass

        def run_workflow(self, workflow, output_dir, **kwargs):
            calls["inputs"] = kwargs
            return [tmp_path / "generated.mp4"]

    monkeypatch.setattr(main, "ComfySdkRunner", Runner)
    monkeypatch.setattr(main, "_set_status", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "_complete_media_job", lambda *args, **kwargs: calls.update(final=kwargs))
    main._run_sdk_job("fixture-job")
    assert calls["inputs"] == {
        "source": manifest["source"],
        "reference_1": manifest["reference_1"],
        "reference_2": manifest["reference_2"],
    }
    assert calls["final"]["source"] == Path(manifest["source"])
    assert calls["final"]["generated"] == tmp_path / "generated.mp4"


def test_app_redacts_provider_exception(monkeypatch, tmp_path):
    import app.main as main
    (tmp_path / "job.json").write_text('{}')
    (tmp_path / "workflow.json").write_text('{}')
    monkeypatch.setattr(main, "_job_dir", lambda job_id: tmp_path)
    def fail(**kwargs):
        raise RuntimeError("SECRET https://signed.example/token")
    monkeypatch.setattr(main, "ComfySdkRunner", fail)
    statuses = []
    monkeypatch.setattr(main, "_set_status", lambda *args, **kwargs: statuses.append(kwargs))
    main._run_sdk_job("redaction-fixture")
    assert statuses[-1]["state"] == "error"
    assert "SECRET" not in json.dumps(statuses)
