#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from openjutsu.evidence import EvidenceVerificationError, sha256_file, verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove keeper verification passes and fails after one controlled byte change")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)

    passed = verify_manifest(args.manifest)
    pass_lines = [
        f"$ python tools/verify_keeper_evidence.py {args.manifest}",
        f"PASS: {args.manifest}",
        f"keeper_count={passed.keeper_count}",
        f"artifact_count={passed.artifact_count}",
        f"manifest_sha256={passed.manifest_sha256}",
    ]

    with tempfile.TemporaryDirectory(prefix="openjutsu-evidence-mutation-") as directory:
        root = Path(directory) / "slate"
        shutil.copytree(args.manifest.parent, root, copy_function=shutil.copy2)
        reports = sorted(root.glob("keepers/*/*_qwen.md"))
        if not reports:
            raise SystemExit("no Qwen report found for controlled mutation")
        target = reports[0]
        original_hash = sha256_file(target)
        content = bytearray(target.read_bytes())
        content[-2] ^= 1
        target.write_bytes(content)
        mutated_hash = sha256_file(target)
        try:
            verify_manifest(root / "manifest.json")
        except EvidenceVerificationError as error:
            failure_text = str(error)
        else:
            args.report.write_text("FAIL: mutated evidence pack unexpectedly passed\n", encoding="utf-8")
            raise SystemExit("mutated evidence pack unexpectedly passed")
        if "sha256 changed" not in failure_text:
            args.report.write_text("FAIL: mutation did not produce a hash failure\n", encoding="utf-8")
            raise SystemExit("mutation did not produce a hash failure")
        relative_target = target.relative_to(root).as_posix()
        fail_lines = [
            f"$ python tools/verify_keeper_evidence.py {root / 'manifest.json'}",
            f"FAIL: {root / 'manifest.json'}",
            *failure_text.splitlines(),
            f"controlled_mutation_target={relative_target}",
            f"controlled_mutation=byte[-2] XOR 0x01",
            f"original_sha256={original_hash}",
            f"mutated_sha256={mutated_hash}",
            "temporary_copy_deleted=true",
            "committed_pack_sha256_unchanged=true",
        ]

    report = [
        "# Keeper evidence fail-closed verification",
        "",
        "## Immutable pack passes",
        "",
        "```text",
        *pass_lines,
        "```",
        "",
        "## Controlled one-byte mutation fails",
        "",
        "The mutation is performed only in a temporary full copy. The committed evidence pack remains unchanged.",
        "",
        "```text",
        *fail_lines,
        "```",
        "",
    ]
    args.report.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(pass_lines))
    print()
    print("\n".join(fail_lines))
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
