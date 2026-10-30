# SPDX-License-Identifier: MIT
"""Frozen public contracts for the managed RecastRoom milestone one flow.

These records are deliberately transport-facing: IDs are opaque safe strings,
hashes are SHA-256 text, coordinates are integers, and no record exposes a local
filesystem path or credential.  JSON arrays decode back to the immutable tuple
shape declared by each dataclass.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import json
import math
import re
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints


class ExecutionMode(str, Enum):
    DRY_RUN = "dry_run"
    RETAINED_REPLAY = "retained_replay"
    COMFY = "comfy"
    SDK = "sdk"


class AttemptState(str, Enum):
    PREPARED = "prepared"
    READY = "ready"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"
    RUNNING = "running"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    RECONCILE_NEEDED = "reconcile_needed"
    CANCEL_REQUESTED = "cancel_requested"
    PROVIDER_CONFIRMED_CANCELLED = "provider_confirmed_cancelled"


class AudioPolicy(str, Enum):
    SOURCE_EDIT_MAP = "source_edit_map"
    MUTE = "mute"
    SOURCE_STREAM_COPY = "source_stream_copy"


class ReviewVerdict(str, Enum):
    KEEPER = "keeper"
    REJECT = "reject"
    NEEDS_REVIEW = "needs_review"


class RemoteState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


_HASH = re.compile(r"[0-9a-f]{64}\Z")
_OPAQUE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_SHOT_KIND = frozenset({"render", "pass_through"})
_TAKE_ORIGIN = frozenset({"dry_run", "retained_replay", "provider"})
_EXPORT_STATE = frozenset({"completed", "failed"})


def _exact_int(value: object, label: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return value


def _text(value: object, label: str, *, maximum: int = 20_000) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{label} must be non-empty text of at most {maximum} characters")
    return value


def _id(value: object, label: str) -> str:
    result = _text(value, label, maximum=128)
    if _OPAQUE_ID.fullmatch(result) is None:
        raise ValueError(f"{label} must be an opaque safe identifier")
    return result


def _hash(value: object, label: str) -> str:
    result = _text(value, label, maximum=64)
    if _HASH.fullmatch(result) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 value")
    return result


def _enum(value: object, enum_type: type[Enum], label: str) -> Enum:
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        try:
            return enum_type(value)
        except ValueError as error:
            raise ValueError(f"{label} is unsupported") from error
    raise ValueError(f"{label} is unsupported")


def _literal(value: object, allowed: frozenset[str], label: str) -> str:
    if value not in allowed or not isinstance(value, str):
        raise ValueError(f"{label} must be one of: {', '.join(sorted(allowed))}")
    return value


def _optional_id(value: object, label: str) -> str | None:
    return None if value is None else _id(value, label)


@dataclass(frozen=True, slots=True)
class FrameRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        _exact_int(self.start, "frame start", minimum=0)
        _exact_int(self.end, "frame end", minimum=0)
        if self.start >= self.end:
            raise ValueError("frame end must be greater than frame start")

    @classmethod
    def from_json(cls, payload: object) -> "FrameRange":
        if isinstance(payload, (str, bytes, bytearray)):
            payload = json.loads(payload)
        return _record(cls, payload)  # type: ignore[arg-type,return-value]

    def to_json(self) -> str:
        return json.dumps(_public(self), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Timebase:
    num: int
    den: int

    def __post_init__(self) -> None:
        _exact_int(self.num, "timebase numerator", minimum=1)
        _exact_int(self.den, "timebase denominator", minimum=1)
        if math.gcd(self.num, self.den) != 1:
            raise ValueError("timebase must be reduced")

    @classmethod
    def from_json(cls, payload: object) -> "Timebase":
        if isinstance(payload, (str, bytes, bytearray)):
            payload = json.loads(payload)
        return _record(cls, payload)  # type: ignore[arg-type,return-value]

    def to_json(self) -> str:
        return json.dumps(_public(self), sort_keys=True, separators=(",", ":"))


def _record(cls: type[Any], values: dict[str, object] | None = None, **kwargs: object) -> Any:
    """Construct and validate a frozen DTO without depending on pydantic."""
    payload: dict[str, object] = dict(values or {})
    payload.update(kwargs)
    type_hints: dict[str, Any] = get_type_hints(cls)
    missing = [name for name in type_hints if name not in payload]
    extra = [name for name in payload if name not in type_hints]
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unexpected {', '.join(extra)}")
        raise ValueError(f"{cls.__name__} fields are invalid: {'; '.join(detail)}")
    converted: dict[str, object] = {}
    for name, declared in type_hints.items():
        label = f"{cls.__name__}.{name}"
        candidate = payload[name]
        converted[name] = _convert(_validated(candidate, name, declared, label), declared, label)
    instance = object.__new__(cls)
    for field in fields(cls):
        object.__setattr__(instance, field.name, converted[field.name])
    if hasattr(instance, "__post_init__"):
        instance.__post_init__()
    return instance


def _convert(value: object, declared: Any, label: str) -> Any:
    origin = get_origin(declared)
    if origin is Union or origin is UnionType:
        return _convert_alternatives(value, get_args(declared), label)
    if origin is Literal:
        allowed = frozenset(str(item) for item in get_args(declared))
        return _literal(value, allowed, label)
    if origin is tuple:
        if not isinstance(value, (tuple, list)):
            raise ValueError(f"{label} must be an array")
        args = getattr(declared, "__args__", ())
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_convert(item, args[0], label) for item in value)
        if len(value) != len(args):
            raise ValueError(f"{label} must contain exactly {len(args)} items")
        return tuple(_convert(item, arg, label) for item, arg in zip(value, args))
    if origin is None and isinstance(declared, type):
        if issubclass(declared, Enum):
            return _enum(value, declared, label)
        if declared is FrameRange or declared is Timebase:
            if isinstance(value, declared):
                return value
            if not isinstance(value, dict):
                raise ValueError(f"{label} must be an object")
            return declared(**value)
        if is_dataclass(declared):
            if isinstance(value, declared):
                return value
            if not isinstance(value, dict):
                raise ValueError(f"{label} must be an object")
            return _record(declared, value)
    if declared is int:
        return _exact_int(value, label)
    if declared is bool:
        if not isinstance(value, bool):
            raise ValueError(f"{label} must be a boolean")
        return value
    if declared is str:
        return _text(value, label)
    if declared is object or origin is None:
        return value
    raise ValueError(f"{label} has unsupported contract type {declared!r}")


def _convert_alternatives(value: object, alternatives: tuple[Any, ...], label: str) -> Any:
    if value is None and type(None) in alternatives:
        return None
    errors: list[str] = []
    for alternative in alternatives:
        if alternative is type(None):
            continue
        try:
            return _convert(value, alternative, label)
        except ValueError as error:
            errors.append(str(error))
    raise ValueError("; ".join(errors) or f"{label} is unsupported")


def _validated(value: object, name: str, declared: Any, label: str) -> object:
    origin = get_origin(declared)
    nullable = (origin is Union or origin is UnionType) and type(None) in get_args(declared)
    if value is None and nullable:
        return None
    if name == "sha256" or name.endswith("_sha256"):
        return _hash(value, label)
    if name == "id" or name.endswith("_id") or name == "challenger_of":
        return _id(value, label)
    if name in {"frame_count", "expected_decoder_frames", "revision", "epoch"}:
        return _exact_int(value, label, minimum=1)
    if name in {"pad_left", "pad_right", "seed"}:
        return _exact_int(value, label, minimum=0)
    return value


def frozen(cls: type[Any]) -> type[Any]:
    """Attach a sealed constructor and JSON round-trip to a typed record."""

    def constructor(self: Any, *args: object, **kwargs: object) -> None:
        if args:
            record_fields = fields(cls)
            if kwargs or len(args) != len(record_fields):
                raise TypeError(f"{cls.__name__} accepts {len(record_fields)} positional arguments")
            kwargs = {field.name: value for field, value in zip(record_fields, args)}
        for field in fields(cls):
            if field.name not in kwargs:
                raise TypeError(f"{cls.__name__} is missing {field.name}")
        extras = set(kwargs) - {field.name for field in fields(cls)}
        if extras:
            raise TypeError(f"{cls.__name__} has unexpected {', '.join(sorted(extras))}")
        for field in fields(cls):
            declared = get_type_hints(cls)[field.name]
            label = f"{cls.__name__}.{field.name}"
            candidate = _validated(kwargs[field.name], field.name, declared, label)
            object.__setattr__(self, field.name, _convert(candidate, declared, label))
        if hasattr(self, "__post_init__"):
            self.__post_init__()

    def from_json(cls_value: type[Any], payload: object) -> Any:
        if isinstance(payload, (str, bytes, bytearray)):
            try:
                payload = json.loads(payload)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError("DTO JSON is malformed") from error
        if not isinstance(payload, dict):
            raise ValueError("DTO JSON must be an object")
        return _record(cls_value, payload)

    cls.__init__ = constructor
    cls.from_json = classmethod(from_json)
    cls.to_json = lambda self: json.dumps(
        _public(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return cls


def _public(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (FrameRange, Timebase)):
        return {name: _public(getattr(value, name)) for name in value.__slots__}
    if isinstance(value, (tuple, list)):
        return [_public(item) for item in value]
    if is_dataclass(value):
        return {field.name: _public(getattr(value, field.name)) for field in fields(value)}
    return value


def public_json(value: Any) -> str:
    """Serialize a DTO deterministically without adding private aliases."""
    return json.dumps(_public(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def dto_json(value: Any) -> dict[str, Any]:
    result = _public(value)
    if not isinstance(result, dict):
        raise ValueError("DTO root must be a record")
    return result


@dataclass(frozen=True)
@frozen
class WordTimingInterval:
    start: float
    end: float
    word: str

    def __post_init__(self) -> None:
        for name in ("start", "end"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("word timing endpoints must be JSON numbers")
            try:
                value = float(value)
            except OverflowError as error:
                raise ValueError("word timing endpoints must be finite") from error
            if not math.isfinite(value):
                raise ValueError("word timing endpoints must be finite")
            object.__setattr__(self, name, 0.0 if value == 0 else value)
        if not 0 <= self.start < self.end:
            raise ValueError("word timing requires 0 <= start < end")
        if (len(self.word) > 128 or self.word != self.word.strip()
                or any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF
                       for c in self.word)):
            raise ValueError("word timing text must be stripped, bounded and control-free")


@dataclass(frozen=True)
@frozen
class WordTiming:
    source_asset_id: str
    source_sha256: str
    words: tuple[WordTimingInterval, ...]

    def __post_init__(self) -> None:
        if not 1 <= len(self.words) <= 512:
            raise ValueError("word timing requires 1–512 intervals")
        if any(right.start < left.end for left, right in zip(self.words, self.words[1:])):
            raise ValueError("word timing must be ordered and non-overlapping")


@dataclass(frozen=True)
@frozen
class SourceTiming:
    asset_id: str
    sha256: str
    frame_count: int
    timebase: Timebase
    cfr: bool
    has_audio: bool


@dataclass(frozen=True)
@frozen
class ShotSpec:
    id: str
    source_range: FrameRange
    kind: Literal["render", "pass_through"]


@dataclass(frozen=True)
@frozen
class SceneRevision:
    id: str
    project_id: str
    source: SourceTiming
    shots: tuple[ShotSpec, ...]
    revision: int


@dataclass(frozen=True)
@frozen
class WindowMap:
    source_range: FrameRange
    source_timebase: Timebase
    render_range: FrameRange
    render_timebase: Timebase
    pad_left: int
    pad_right: int
    expected_decoder_frames: int
    decoder_keep: FrameRange
    timeline_range: FrameRange
    timeline_timebase: Timebase
    qualification_id: str


@dataclass(frozen=True)
@frozen
class RecipePin:
    recipe_id: str
    version: str
    raw_graph_sha256: str
    profile_id: str
    adapter_version: str
    endpoint_fingerprint: str


@dataclass(frozen=True)
@frozen
class ResolvedOperation:
    id: str
    project_id: str
    scene_revision_id: str
    shot_id: str
    window: WindowMap
    pin: RecipePin
    character_version: tuple[str, int]
    seed: int
    canonical_json: str
    fingerprint: str
    managed_job_id: str


@dataclass(frozen=True)
@frozen
class Fence:
    attempt_id: str
    owner_id: str
    epoch: int


@dataclass(frozen=True)
@frozen
class AttemptRecord:
    id: str
    project_id: str
    operation_id: str
    client_request_id: str
    mode: ExecutionMode
    challenger_of: str | None
    state: AttemptState
    provider_id: str | None
    revision: int


@dataclass(frozen=True)
@frozen
class AttemptEvent:
    kind: str
    payload_json: str


@dataclass(frozen=True)
@frozen
class Readiness:
    ready: bool
    code: str
    detail: str


@dataclass(frozen=True)
@frozen
class BoundSubmission:
    operation_id: str
    binding_asset_id: str
    binding_sha256: str
    charge_bearing: bool


@dataclass(frozen=True)
@frozen
class Receipt:
    attempt_id: str
    provider_id: str
    request_key: str
    adapter_version: str
    endpoint_fingerprint: str
    receipt_asset_id: str
    receipt_sha256: str


@dataclass(frozen=True)
@frozen
class OutputEvidence:
    asset_id: str
    sha256: str
    frame_count: int
    timebase: Timebase
    receipt: Receipt | None


@dataclass(frozen=True)
@frozen
class CancelResult:
    supported: bool
    confirmed: bool
    detail: str


@dataclass(frozen=True)
@frozen
class TakeRecord:
    id: str
    project_id: str
    scene_revision_id: str | None
    shot_id: str
    attempt_id: str | None
    operation_id: str | None
    output: OutputEvidence
    origin: Literal["dry_run", "retained_replay", "provider"]
    qualified: bool

    def __post_init__(self) -> None:
        if self.scene_revision_id is None and (
            self.qualified or self.operation_id is not None or self.attempt_id is not None
            or self.origin != "retained_replay"
        ):
            raise ValueError("NULL scene scope requires an unattached unqualified import")


@dataclass(frozen=True)
@frozen
class ReplayReceipt:
    scene_revision_id: str
    shot_id: str
    source_sha256: str
    input_sha256: str
    recipe_id: str
    recipe_version: str
    raw_graph_sha256: str
    resolved_graph_sha256: str
    output_sha256: str
    window: WindowMap
    historical_verdict: ReviewVerdict | None


@dataclass(frozen=True)
@frozen
class ReviewRecord:
    id: str
    take_id: str
    verdict: ReviewVerdict
    note: str


@dataclass(frozen=True)
@frozen
class SelectionRecord:
    project_id: str
    scene_revision_id: str
    shot_id: str
    take_id: str | None
    revision: int


@dataclass(frozen=True)
@frozen
class EditItem:
    shot_id: str
    take_id: str | None
    source_range: FrameRange
    decoder_keep: FrameRange | None
    timeline_range: FrameRange


@dataclass(frozen=True)
@frozen
class EditRevision:
    id: str
    project_id: str
    scene_revision_id: str
    items: tuple[EditItem, ...]
    audio: AudioPolicy
    timebase: Timebase


@dataclass(frozen=True)
@frozen
class ExportRecord:
    id: str
    revision_id: str
    state: Literal["completed", "failed"]
    asset_id: str | None
    sha256: str | None
    checks_json: str
