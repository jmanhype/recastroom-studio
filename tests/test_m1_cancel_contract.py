# SPDX-License-Identifier: MIT
"""Contract proof for the native M1 cancellation result DTO."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from enum import Enum
import json
from typing import get_type_hints

import pytest

import openjutsu.m1_types as m1_types
from openjutsu.m1_types import CancelResult


EXPECTED_RECORDS = frozenset({
    "FrameRange", "Timebase", "SourceTiming", "ShotSpec", "SceneRevision", "WindowMap",
    "RecipePin", "ResolvedOperation", "Fence", "AttemptRecord", "AttemptEvent", "Readiness",
    "BoundSubmission", "Receipt", "OutputEvidence", "CancelResult", "TakeRecord", "ReplayReceipt",
    "ReviewRecord", "SelectionRecord", "EditItem", "EditRevision", "ExportRecord",
    "WordTiming", "WordTimingInterval",
})
EXPECTED_ENUMS = frozenset({
    "ExecutionMode", "AttemptState", "AudioPolicy", "ReviewVerdict", "RemoteState",
})
VALID = {"supported": True, "confirmed": False, "detail": "provider has not confirmed yet"}


def test_complete_native_record_and_enum_surface() -> None:
    exported = vars(m1_types).items()
    records = {name for name, value in exported if not name.startswith("_") and isinstance(value, type) and is_dataclass(value)}
    enums = {
        name for name, value in exported
        if not name.startswith("_") and isinstance(value, type) and value is not Enum and issubclass(value, Enum)
    }
    assert records == EXPECTED_RECORDS
    assert len(EXPECTED_RECORDS) == 25
    assert enums == EXPECTED_ENUMS
    assert len(EXPECTED_ENUMS) == 5


def test_cancel_result_has_exact_frozen_contract_surface() -> None:
    hints = get_type_hints(CancelResult)
    assert list(hints) == ["supported", "confirmed", "detail"]
    assert hints == {"supported": bool, "confirmed": bool, "detail": str}
    assert CancelResult.__dataclass_params__.frozen is True
    public_own_members = {name for name in CancelResult.__dict__ if not name.startswith("__")}
    assert public_own_members == {"from_json", "to_json"}


@pytest.mark.parametrize(
    ("supported", "confirmed", "detail"),
    [(True, True, "provider confirmed cancellation"), (False, False, "adapter cannot cancel")],
)
def test_direct_construction_accepts_independent_valid_values(
    supported: bool, confirmed: bool, detail: str
) -> None:
    result = CancelResult(supported, confirmed, detail)
    assert result == CancelResult(supported=supported, confirmed=confirmed, detail=detail)
    assert (result.supported, result.confirmed, result.detail) == (supported, confirmed, detail)


def test_direct_construction_rejects_missing_and_extra_fields() -> None:
    for missing in VALID:
        values = dict(VALID)
        del values[missing]
        with pytest.raises(TypeError, match=missing):
            CancelResult(**values)
    with pytest.raises(TypeError, match="unexpected request_id"):
        CancelResult(**VALID, request_id="extra")


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("supported", 1), ("supported", "true"), ("supported", None),
        ("confirmed", 0), ("confirmed", "false"), ("confirmed", None),
        ("detail", 3), ("detail", None), ("detail", ""), ("detail", "x" * 20_001),
    ],
)
def test_direct_construction_rejects_every_invalid_field(field_name: str, value: object) -> None:
    with pytest.raises(ValueError, match=field_name):
        CancelResult(**(VALID | {field_name: value}))


@pytest.mark.parametrize(
    ("supported", "confirmed", "detail"),
    [(True, False, "provider has not confirmed yet"), (False, False, "adapter cannot cancel")],
)
def test_json_round_trip_is_exact_and_deterministic(
    supported: bool, confirmed: bool, detail: str
) -> None:
    result = CancelResult(supported, confirmed, detail)
    payload = json.dumps(
        {"supported": supported, "confirmed": confirmed, "detail": detail},
        sort_keys=True, separators=(",", ":"),
    )
    assert result.to_json() == payload
    assert CancelResult.from_json(payload) == result
    assert json.loads(payload) == {"supported": supported, "confirmed": confirmed, "detail": detail}


def test_json_parsing_rejects_malformed_incomplete_extra_and_mistyped_payloads() -> None:
    cases: list[tuple[str, object]] = [
        ("malformed", "{"), ("array", [VALID]), ("scalar", 7), ("extra", VALID | {"request_id": "extra"}),
        ("bad supported", VALID | {"supported": 1}), ("bad confirmed", VALID | {"confirmed": "false"}),
        ("bad detail type", VALID | {"detail": 3}), ("empty detail", VALID | {"detail": ""}),
    ]
    for missing in VALID:
        values = dict(VALID)
        del values[missing]
        cases.append((f"missing {missing}", values))
    for label, payload in cases:
        with pytest.raises(ValueError, match="DTO|CancelResult"):
            CancelResult.from_json(payload)


def test_each_cancel_result_field_is_independently_frozen() -> None:
    result = CancelResult(False, False, "adapter cannot cancel")
    for field in fields(result):
        with pytest.raises(FrozenInstanceError):
            setattr(result, field.name, not getattr(result, field.name))
