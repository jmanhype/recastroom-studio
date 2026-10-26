# SPDX-License-Identifier: MIT
"""Decomposed, fail-closed keeper manifest verification."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Callable

from openjutsu.evidence import (
    EXPECTED_CONCEPTS,
    MANIFEST_NAME,
    REQUIRED_ARTIFACT_KINDS,
    SHA256_PATTERN,
    _require,
    _safe_artifact_path,
    _verify_media_metadata,
    _verify_probe,
    _verify_rights,
    sha256_file,
)


ProbeRunner = Callable[[Path], dict[str, Any]]


def _verify_receipts(root: Path, receipts: list[Any], listed_paths: set[Path], errors: list[str]) -> int:
    artifact_count = 0
    for index, receipt in enumerate(receipts):
        label = f"provenance_receipts[{index}]"
        if not isinstance(receipt, dict):
            errors.append(f"{label}: must be an object")
            continue
        path = _safe_artifact_path(root, receipt.get("path"), label, errors)
        if path is None:
            continue
        relative = Path(receipt["path"])
        _require(relative not in listed_paths, f"{label}: duplicate path {relative}", errors)
        listed_paths.add(relative)
        _verify_size_and_hash(receipt, path, label, errors)
        source_hash = receipt.get("source_sha256")
        if isinstance(source_hash, str) and source_hash != receipt.get("sha256"):
            errors.append(f"{label}.source_sha256 does not match the imported receipt")
        _verify_rights(receipt.get("rights"), label, errors)
        artifact_count += 1
    return artifact_count


def _verify_size_and_hash(entry: dict[str, Any], path: Path, label: str, errors: list[str]) -> None:
    expected_bytes = entry.get("bytes")
    expected_hash = entry.get("sha256")
    _require(isinstance(expected_bytes, int) and expected_bytes == path.stat().st_size, f"{label}.bytes does not match", errors)
    valid_hash = isinstance(expected_hash, str) and SHA256_PATTERN.fullmatch(expected_hash) is not None
    _require(valid_hash, f"{label}.sha256 is invalid", errors)
    if valid_hash:
        _require(sha256_file(path) == expected_hash, f"{label}.sha256 changed", errors)


def _verify_keepers(
    root: Path,
    keepers: list[Any],
    listed_paths: set[Path],
    probe_runner: ProbeRunner,
    errors: list[str],
) -> int:
    artifact_count = 0
    for index, keeper in enumerate(keepers):
        if not isinstance(keeper, dict):
            errors.append(f"keepers[{index}]: must be an object")
            continue
        artifact_count += _verify_keeper(root, keeper, listed_paths, probe_runner, errors)
    return artifact_count


def _verify_keeper(
    root: Path,
    keeper: dict[str, Any],
    listed_paths: set[Path],
    probe_runner: ProbeRunner,
    errors: list[str],
) -> int:
    label = f"keeper[{keeper.get('slug', '<missing>')}]"
    _verify_keeper_identity(keeper, label, errors)
    workflow = _verify_keeper_workflow(keeper, label, errors)
    qc = _verify_keeper_qc(keeper, label, errors)
    artifacts = keeper.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append(f"{label}.artifacts: must be an array")
        return 0
    return _verify_keeper_artifacts(root, keeper, workflow, qc, artifacts, listed_paths, probe_runner, errors)


def _verify_keeper_identity(keeper: dict[str, Any], label: str, errors: list[str]) -> None:
    concept = keeper.get("format_concept")
    if not isinstance(concept, dict):
        errors.append(f"{label}.format_concept: must be an object")
    else:
        _require(concept.get("name") in EXPECTED_CONCEPTS, f"{label}.format_concept.name is not an approved concept", errors)
        _require(isinstance(concept.get("description"), str) and concept.get("description"), f"{label}.format_concept.description is missing", errors)
    _require(isinstance(keeper.get("title"), str) and bool(keeper.get("title")), f"{label}.title is missing", errors)


def _verify_keeper_workflow(keeper: dict[str, Any], label: str, errors: list[str]) -> Any:
    workflow = keeper.get("workflow")
    if not isinstance(workflow, dict):
        errors.append(f"{label}.workflow: must be an object")
        return workflow
    _require(workflow.get("seed") in {50, 51}, f"{label}.workflow.seed must be 50 or 51", errors)
    _require(workflow.get("steps") == 8, f"{label}.workflow.steps must be 8", errors)
    _require(workflow.get("character_lora_strength") == 1.0, f"{label}.workflow.character_lora_strength must be 1.0", errors)
    _require(workflow.get("head_lora_strength") in {0.0, 0.35, 0.5}, f"{label}.workflow.head_lora_strength is not allowed", errors)
    _require(workflow.get("with_audio") is True, f"{label}.workflow.with_audio must be true", errors)
    _require(workflow.get("source_blur") == "off", f"{label}.workflow.source_blur must be off", errors)
    _require(workflow.get("fps") == 24, f"{label}.workflow.fps must be 24", errors)
    return workflow


def _verify_keeper_qc(keeper: dict[str, Any], label: str, errors: list[str]) -> Any:
    qc = keeper.get("qc")
    if not isinstance(qc, dict):
        errors.append(f"{label}.qc: must be an object")
        return qc
    machine = qc.get("machine")
    if not isinstance(machine, dict):
        errors.append(f"{label}.qc.machine: must be an object")
    else:
        score = machine.get("score")
        _require(isinstance(score, (int, float)) and not isinstance(score, bool) and 8 <= score <= 10, f"{label}.qc.machine.score must be 8-10", errors)
        _require(machine.get("verdict") == "keeper_candidate", f"{label}.qc.machine.verdict must be keeper_candidate", errors)
        _require(isinstance(machine.get("report"), str) and bool(machine.get("report")), f"{label}.qc.machine.report is missing", errors)
    human = qc.get("human")
    if not isinstance(human, dict):
        errors.append(f"{label}.qc.human: must be an object")
    else:
        _require(human.get("verdict") == "Done and perfect", f"{label}.qc.human.verdict is unapproved", errors)
        _require(human.get("status") == "approved_for_demo_assembly", f"{label}.qc.human.status is invalid", errors)
    return qc


def _verify_keeper_artifacts(
    root: Path,
    keeper: dict[str, Any],
    workflow: Any,
    qc: Any,
    artifacts: list[Any],
    listed_paths: set[Path],
    probe_runner: ProbeRunner,
    errors: list[str],
) -> int:
    label = f"keeper[{keeper.get('slug', '<missing>')}]"
    kinds = [artifact.get("kind") for artifact in artifacts if isinstance(artifact, dict)]
    if Counter(kinds) != Counter(REQUIRED_ARTIFACT_KINDS):
        errors.append(f"{label}.artifacts must contain exactly one final, compare, contact, and qwen_report")
    final_paths: list[str] = []
    report_paths: list[str] = []
    artifact_count = 0
    for index, artifact in enumerate(artifacts):
        artifact_label = f"{label}.artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{artifact_label}: must be an object")
            continue
        path = _safe_artifact_path(root, artifact.get("path"), artifact_label, errors)
        if path is None:
            continue
        relative = Path(artifact["path"])
        _require(relative not in listed_paths, f"{artifact_label}: duplicate path {relative}", errors)
        listed_paths.add(relative)
        artifact_count += 1
        _verify_size_and_hash(artifact, path, artifact_label, errors)
        if path.suffix.lower() == ".mp4":
            _verify_media_metadata(path, artifact_label, probe_runner, errors)
        _verify_rights(artifact.get("rights"), artifact_label, errors)
        if artifact.get("kind") in {"final", "compare", "contact"}:
            _verify_probe(artifact.get("probe"), path, artifact_label, probe_runner, errors)
        if artifact.get("kind") == "final":
            final_paths.append(str(relative))
        if artifact.get("kind") == "qwen_report":
            report_paths.append(str(relative))
    if isinstance(qc, dict) and isinstance(qc.get("machine"), dict):
        _require(qc["machine"].get("report") in report_paths, f"{label}.qc.machine.report must point to the included qwen_report", errors)
    if len(final_paths) == 1 and isinstance(workflow, dict):
        _require(workflow.get("final_asset") == final_paths[0], f"{label}.workflow.final_asset must identify the final artifact", errors)
    return artifact_count


def _verify_complete_file_set(root: Path, listed_paths: set[Path], errors: list[str]) -> None:
    actual_files: set[Path] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            errors.append(f"evidence root contains symlink: {path.relative_to(root)}")
            continue
        if path.is_file() and path.name != MANIFEST_NAME:
            actual_files.add(path.relative_to(root))
    for path in sorted(actual_files - listed_paths):
        errors.append(f"evidence root contains unmanifested file: {path}")
    for path in sorted(listed_paths - actual_files):
        errors.append(f"manifest lists missing file: {path}")
