# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

import pytest

from openjutsu.cli import build_parser


def test_prepare_requires_explicit_rights_attestation():
    command = [
        "prepare",
        "--source",
        "source.mp4",
        "--reference-1",
        "reference.png",
    ]
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args(command)
    assert error.value.code == 2

    args = build_parser().parse_args([*command, "--attest-rights"])
    assert args.attest_rights is True


def test_run_requires_explicit_rights_attestation():
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args(["run", str(Path("workflow.json"))])
    assert error.value.code == 2

    args = build_parser().parse_args(["run", "--attest-rights", "workflow.json"])
    assert args.attest_rights is True
