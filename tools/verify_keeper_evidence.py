#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
from pathlib import Path

from openjutsu.evidence import EvidenceVerificationError, verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail closed on an incomplete or changed Openjutsu keeper evidence pack")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = verify_manifest(args.manifest)
    except EvidenceVerificationError as error:
        print(f"FAIL: {args.manifest}")
        print(error)
        return 1
    print(f"PASS: {args.manifest}")
    print(f"keeper_count={result.keeper_count}")
    print(f"artifact_count={result.artifact_count}")
    print(f"manifest_sha256={result.manifest_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
