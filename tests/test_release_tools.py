# SPDX-License-Identifier: MIT
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from openjutsu.evidence import ALLOWED_MEDIA_TAGS as KEEPER_ALLOWED_MEDIA_TAGS
import tools.audit_release as audit_release
from tools.audit_release import audit
from tools.audit_release import ALLOWED_MEDIA_TAGS as RELEASE_ALLOWED_MEDIA_TAGS
from tools.build_release_archive import write_deterministic_zip


def make_release_tree(root: Path) -> None:
    (root / "LICENSE").write_text("MIT License\n\nPermission is hereby granted\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('license = { text = "MIT" }\n', encoding="utf-8")
    (root / "app.py").write_text("# SPDX-License-Identifier: MIT\n", encoding="utf-8")
    (root / "index.html").write_text("<!-- SPDX-License-Identifier: MIT -->\n", encoding="utf-8")
    workflow_dir = root / "workflows"
    workflow_dir.mkdir()
    plan = {"video": "source.mp4", "global_ref": "reference_1.png"}
    workflow = {"1189": {"inputs": {"plan": json.dumps(plan)}}}
    (workflow_dir / "recastroom_h3_workflow.json").write_text(
        json.dumps(workflow), encoding="utf-8"
    )


def test_audit_accepts_clean_release_tree_and_rejects_private_tree(tmp_path: Path) -> None:
    clean = tmp_path / "clean"
    clean.mkdir()
    make_release_tree(clean)

    errors, summary = audit(clean)

    assert errors == []
    assert summary["probed_media_files"] == 0

    private = tmp_path / "private"
    private.mkdir()
    make_release_tree(private)
    local = private / ".vault" / "runtime.json"
    local.parent.mkdir()
    local.write_text("{}\n", encoding="utf-8")

    errors, _ = audit(private)

    assert any("private/local-only path is present: .vault/runtime.json" in error for error in errors)


def test_audit_allows_bounded_hyperframes_metadata_but_rejects_unknown_tags(
    tmp_path: Path, monkeypatch
) -> None:
    assert RELEASE_ALLOWED_MEDIA_TAGS == KEEPER_ALLOWED_MEDIA_TAGS
    assert {"hyperframes_renderer", "hyperframes_version"} <= RELEASE_ALLOWED_MEDIA_TAGS

    def ffprobe(command: list[str], **_kwargs: object) -> SimpleNamespace:
        assert command[:2] == ["ffprobe", "-v"]
        tags = {
            "hyperframes_renderer": "hyperframes",
            "hyperframes_version": "0.8.200",
        }
        if "unknown.mp4" in command[-1]:
            tags["unexpected_renderer"] = "safe-value"
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"format": {"tags": tags}, "streams": []}),
            stderr="",
        )

    monkeypatch.setattr(audit_release.subprocess, "run", ffprobe)
    clean = tmp_path / "clean"
    clean.mkdir()
    make_release_tree(clean)
    (clean / "hero.mp4").write_bytes(b"fixture bytes\n")

    errors, summary = audit(clean)

    assert errors == []
    assert summary["probed_media_files"] == 1

    (clean / "hero.mp4").rename(clean / "unknown.mp4")
    errors, _ = audit(clean)
    assert errors == ["unallowed media tag unexpected_renderer: unknown.mp4"]


def test_release_zip_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    make_release_tree(source)
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    write_deterministic_zip(source, first, "openjutsu-studio-test")
    write_deterministic_zip(source, second, "openjutsu-studio-test")

    assert first.read_bytes() == second.read_bytes()
    assert hashlib.sha256(first.read_bytes()).hexdigest() == hashlib.sha256(second.read_bytes()).hexdigest()
