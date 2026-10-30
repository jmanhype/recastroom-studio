#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline, fail-closed submission assessment of an explicit Git commit.

Exit 0: eligible; 1: failed local check; 2: owner action still required.
This tool never publishes and never treats owner-blocked as a pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.audit_release import audit
from tools.build_release_archive import (
    content_tree_digest, extract_commit, filter_local_files, resolve_commit,
    sha256, write_deterministic_zip,
)
from openjutsu.evidence import verify_manifest

DEMO_HASH = "a14b3eb287e3daf0ed4dd27e238048c1725c087c0b48cf8ffb301758e637f13f"
LIVE_SDK_SMOKE_DIR = Path("docs/evidence/comfy-sdk-smoke-20261025")


def verify_live_sdk_smoke(root: Path) -> dict:
    """Verify the redacted one-job Comfy Cloud SDK smoke evidence."""
    directory = root / LIVE_SDK_SMOKE_DIR
    receipt_path = directory / "receipt.json"
    readonly_path = directory / "readonly-job-verification.json"
    output_path = directory / "output.png"
    for path in (receipt_path, readonly_path, output_path):
        if not path.is_file():
            raise ValueError(f"live SDK smoke evidence missing: {path.name}")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    readonly = json.loads(readonly_path.read_text(encoding="utf-8"))
    serialized = json.dumps(receipt) + json.dumps(readonly)
    if "comfyui-" in serialized or "COMFY_API_KEY=" in serialized:
        raise ValueError("live SDK smoke evidence contains a credential-shaped value")

    bound = receipt.get("bound", {})
    outputs = receipt.get("outputs", [])
    output_digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    workflow_hash = bound.get("workflow_sha256")
    expected = {
        "schema": receipt.get("schema_version") == "recastroom.live-sdk-smoke.v1",
        "one_submission": bound.get("submissions") == 1,
        "no_model_inference": bound.get("model_inference") is False,
        "no_uploaded_assets": bound.get("uploaded_assets") == 0,
        "workflow_hash": isinstance(workflow_hash, str) and len(workflow_hash) == 64,
        "queued": receipt.get("initial_status") == "queued",
        "succeeded": receipt.get("final_status") == "succeeded",
        "one_output": receipt.get("output_count") == 1 and len(outputs) == 1,
        "job_id": bool(receipt.get("job_id")),
        "elapsed_bounded": isinstance(receipt.get("elapsed_seconds"), (int, float))
            and 0 < receipt["elapsed_seconds"] <= 300,
        "output_hash_matches": bool(outputs)
            and outputs[0].get("sha256") == output_digest
            and outputs[0].get("downloaded_bytes") == output_path.stat().st_size,
        "readonly_job_matches": readonly.get("job_id") == receipt.get("job_id")
            and readonly.get("status") == "succeeded"
            and readonly.get("workflow_sha256") == workflow_hash,
    }
    if not all(expected.values()):
        failed = [name for name, passed in expected.items() if not passed]
        raise ValueError("live SDK smoke evidence failed: " + ", ".join(failed))

    return {
        "job_id": receipt["job_id"],
        "status": receipt["final_status"],
        "elapsed_seconds": receipt["elapsed_seconds"],
        "workflow_sha256": workflow_hash,
        "output_sha256": output_digest,
    }


def probe_demo(path: Path) -> dict:
    """Probe only the explicitly supplied, known public-candidate bytes."""
    digest = sha256(path)
    if digest != DEMO_HASH:
        raise ValueError("demo differs from the published-candidate provenance receipt")
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    raw = json.loads(result.stdout)
    duration = float(raw["format"]["duration"])
    videos = [s for s in raw["streams"] if s["codec_type"] == "video"]
    audio = [s for s in raw["streams"] if s["codec_type"] == "audio"]
    if not math.isfinite(duration) or not 0 < duration <= 120:
        raise ValueError("demo must be positive and no longer than 120 seconds")
    if not videos or not audio or videos[0].get("width", 0) <= 0 or videos[0].get("height", 0) <= 0:
        raise ValueError("demo requires video dimensions and an audio stream")
    return {
        "sha256": digest, "bytes": path.stat().st_size, "duration_seconds": duration,
        "container": raw["format"]["format_name"],
        "video": {k: videos[0].get(k) for k in ("codec_name", "width", "height", "r_frame_rate")},
        "audio": [{k: s.get(k) for k in ("codec_name", "channels", "sample_rate")} for s in audio],
        "provenance": "docs/evidence/OJ-mbn5-final-gate/demo-provenance.md",
    }


def row(item: str, status: str, evidence: str) -> dict:
    if status not in {"PASS", "FAIL", "OWNER_BLOCKED"} or not evidence:
        raise ValueError("every requirement needs a supported tri-state result")
    return {"requirement": item, "status": status, "evidence": evidence}


def exit_status(rows: list[dict]) -> int:
    if not rows or any(r["status"] == "FAIL" for r in rows):
        return 1
    return 2 if any(r["status"] == "OWNER_BLOCKED" for r in rows) else 0


def run_check(command: list[str], root: Path) -> dict:
    env = dict(os.environ)
    for key in list(env):
        if "COMFY" in key or key.startswith(("OPENJUTSU_", "RECASTROOM_")):
            env.pop(key)
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + str(root)
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=240)
    output = (result.stdout + result.stderr).replace(str(root), "<package>").replace(str(ROOT), "<checkout>").replace(sys.prefix, "<environment>")
    return {"command": command[1:], "exit_code": result.returncode, "output": output}


def assess(commit: str, demo: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("refusing to overwrite prior evidence")
    output.mkdir(parents=True)
    (ROOT / "work").mkdir(exist_ok=True)
    revision, tree = resolve_commit(commit)
    rows = []
    report = {"schema_version": "openjutsu.final-gate.v1", "commit": revision,
              "source_tree": tree, "published": False, "submitted": False, "matrix": rows}
    with tempfile.TemporaryDirectory(dir=ROOT / "work") as temporary:
        package = Path(temporary) / "package"
        package.mkdir()
        extract_commit(revision, package)
        report["excluded"] = filter_local_files(package)
        errors, counts = audit(package)
        counts.pop("root", None)
        report["release_audit"] = {"errors": errors, "counts": counts}
        rows.append(row("No credentials/private development artifacts; license/header audit", "FAIL" if errors else "PASS", "gate.json:release_audit"))
        report["filtered_content_sha256"] = content_tree_digest(package)
        archive = output / "public-package.zip"
        write_deterministic_zip(package, archive, "recastroom-studio")
        report["archive"] = {"file": archive.name, "sha256": sha256(archive), "bytes": archive.stat().st_size}
        second = Path(temporary) / "repeat.zip"
        write_deterministic_zip(package, second, "recastroom-studio")
        rows.append(row("Reproducible public package", "PASS" if sha256(second) == sha256(archive) else "FAIL", "gate.json:archive and filtered_content_sha256"))
        try:
            verified = verify_manifest(package / "docs/evidence/slate/manifest.json")
            report["keepers"] = {"count": verified.keeper_count, "artifacts": verified.artifact_count, "sha256": verified.manifest_sha256}
            rows.append(row("Synthetic keeper artifacts", "PASS", "gate.json:keepers; docs/evidence/slate/manifest.json"))
        except Exception as error:
            rows.append(row("Synthetic keeper artifacts", "FAIL", type(error).__name__))
        report["tests"] = run_check([sys.executable, "-m", "pytest", "-q"], package)
        report["pip_check"] = run_check([sys.executable, "-m", "pip", "check"], package)
        for item, key in (("Working UI, CLI, timing, rights, workflow mutation, local dry-run upload-to-output", "tests"), ("Installed dependency consistency", "pip_check")):
            rows.append(row(item, "PASS" if report[key]["exit_code"] == 0 else "FAIL", f"gate.json:{key}"))
        for item, path in (("OSS MIT license", "LICENSE"), ("Setup instructions", "docs/QUICKSTART.md"), ("Comfy API-format workflow", "workflows/recastroom_h3_workflow.json"), ("Screenshots", "docs/images/app-landing.png"), ("API examples", "docs/API_EXAMPLES.md")):
            exists = (package / path).is_file()
            rows.append(row(item, "PASS" if exists else "FAIL", path + (" sha256=" + sha256(package / path) if exists else " missing")))
        try:
            report["live_sdk_smoke"] = verify_live_sdk_smoke(package)
            rows.append(row("Official Comfy Developer Platform live SDK smoke", "PASS", "gate.json:live_sdk_smoke"))
        except Exception as error:
            rows.append(row("Official Comfy Developer Platform live SDK smoke", "FAIL", type(error).__name__ + ": smoke evidence rejected"))
    try:
        report["demo"] = probe_demo(demo)
        rows.append(row("Demo at most 120 seconds; resolution/container/audio", "PASS", "gate.json:demo"))
    except Exception as error:
        rows.append(row("Demo at most 120 seconds; resolution/container/audio", "FAIL", type(error).__name__ + ": demo probe rejected"))
    for item, evidence in (
        ("Public GitHub repository and release tag", "docs/CONTEST.md: unchecked public repository; docs/RELEASE.md: unpublished"),
        ("Public demo link and final repository URL card", "docs/CONTEST.md: final repo URL card pending publication"),
        ("Public social post with #OpenSourceHiggsfield", "docs/FINAL_SUBMISSION_PACKET.md: unpublished social draft"),
        ("Typeform submission before deadline", "docs/SUBMISSION_CHECKLIST.md: unchecked Typeform"),
        ("Optional deployed link", "docs/evidence/OJ-2t3g-local-trial/receipt.json: public_url=null; optional, not an eligibility requirement"),
        ("Exact demo rights/consent and third-party model licenses", "docs/evidence/OJ-mbn5-final-gate/demo-provenance.md: bounded provenance, owner clearance outstanding"),
        ("Clean environment install and fresh checkout launch", "docs/RELEASE.md: owner must rerun on final public commit; this gate reuses installed environment"),
    ):
        rows.append(row(item, "OWNER_BLOCKED", evidence))
    report["exit_code"] = exit_status(rows)
    report["eligible_to_submit"] = report["exit_code"] == 0
    (output / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--demo", type=Path, required=True, help="known synthetic demo candidate only")
    parser.add_argument("--output", type=Path, required=True, help="new local evidence directory")
    args = parser.parse_args()
    try:
        report = assess(args.commit, args.demo, args.output)
    except Exception as error:
        print("FAIL: final gate: " + type(error).__name__)
        return 1
    print(json.dumps({"exit_code": report["exit_code"], "eligible_to_submit": report["eligible_to_submit"], "matrix": report["matrix"]}, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
