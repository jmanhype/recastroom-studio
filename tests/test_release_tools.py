# SPDX-License-Identifier: MIT
import hashlib
import json
from pathlib import Path

from tools.audit_release import audit
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
