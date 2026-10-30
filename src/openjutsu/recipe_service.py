# SPDX-License-Identifier: MIT
"""Fail-closed resolution of pinned recipes into effective operation inputs."""
from __future__ import annotations

import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path
import subprocess
import tempfile
import uuid
from typing import Any

from .config import load_settings
from .m1_types import (
    AudioPolicy,
    BoundSubmission,
    FrameRange,
    RecipePin,
    ResolvedOperation,
    SceneRevision,
    ShotSpec,
    WordTiming,
    public_json,
)
from .pipeline import ManagedWorkflowPreparation, prepare_managed_workflow
from .scene_service import SceneService, SceneServiceError
from .workspace_store import AssetIntegrityError, AssetRecord, WorkspaceStore, WorkspaceStoreError


class RecipeResolutionError(Exception):
    """Managed recipe resolution refused an unsupported input."""


class UnsupportedRecipeError(RecipeResolutionError):
    """No pinned allowlist entry matches this recipe/profile."""


class OwnerBlockedRecipeError(UnsupportedRecipeError):
    """A renderer profile requires separate owner qualification."""


class RecipeIntegrityError(RecipeResolutionError):
    """A frozen graph or immutable reference changed."""


ALLOWLIST_VERSION = "openjutsu-offline-routing-v1"
WORKFLOW_PATH = Path(__file__).resolve().parents[2] / "workflows/openjutsu_h3_lipsync_local.json"
OFFLINE_SOURCE_SHA256 = "2208c20f765c67042f6969f4564a2f2603fe66bbb9548282a6dfae19d77c2f64"
OFFLINE_REFERENCE_SHA256 = (
    "4d3b4ed2652ce453e10fb8dc6f44b317f76aae37659c7021ef44b87422a86343",
    "0cd734b612f4b224e015ce135237a013f1d186c574c60bc78da12d144705d072",
)
CPU_CLIP_SHA256 = {
    (0, 8): "86bd10e1717fcf37239df05ce42c1bd7bf68c00ecc9fb1e024dc345d4932d154",
    (8, 16): "ce1dc17d855b5d04aad9ac729d535fdc8b6e5f16a4d375e99d274d7216b2715c",
    (16, 24): "9bda6b65022314b4ba4bb6a3a041d57d5e87df45025b9928731a347f926bd528",
}
OFFLINE_PIN = RecipePin(
    "offline-source-routing",
    "cpu-dryrun-v1",
    "07e9f399d2168c7142bdf79a15cd3ab4fa536b734f7c74f795ca26853e10c244",
    "cpu_non_inference_routing_v1",
    "local_cpu_router-1",
    "c3f575f84b5c61336316eaca48172c7338476480f255322a84668c90cb5c7d7e",
)
_RENDERER_MARKERS = ("h3", "comfy", "sdk")


def recipe_catalog() -> dict[str, Any]:
    """Expose the read-only pinned profile without exposing paths or secrets."""
    return {
        "allowlist_version": ALLOWLIST_VERSION,
        "profiles": [{
            "pin": json.loads(OFFLINE_PIN.to_json()),
            "execution_mode": "dry_run",
            "non_inference": True,
            "qualification_scope": "offline_cpu_routing_only",
            "h3_qualified": False,
        }],
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_digest(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _run_tool(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            arguments, check=True, capture_output=True, text=True, timeout=30
        )
    except subprocess.SubprocessError as error:
        raise RecipeIntegrityError("CPU fixture extraction or measurement failed") from error


def _raw_frames(path: Path, start: int, end: int) -> bytes:
    expression = f"select='between(n\\,{start}\\,{end - 1})'"
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path),
                "-vf", expression, "-fps_mode", "passthrough", "-map", "0:v:0",
                "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1",
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.SubprocessError as error:
        raise RecipeIntegrityError("CPU pixel correspondence could not be measured") from error
    return result.stdout


class RecipeService:
    """Resolve one project-owned original shot using one active store."""

    def __init__(self, store: WorkspaceStore) -> None:
        if not isinstance(store, WorkspaceStore):
            raise WorkspaceStoreError("recipe service requires the active WorkspaceStore")
        self._store = store

    def _pin(self, pin: RecipePin) -> RecipePin:
        if not isinstance(pin, RecipePin):
            raise UnsupportedRecipeError("recipe pin must be a typed RecipePin")
        if pin == OFFLINE_PIN:
            return pin
        identity = " ".join((pin.recipe_id, pin.version, pin.profile_id)).lower()
        if any(marker in identity for marker in _RENDERER_MARKERS):
            raise OwnerBlockedRecipeError(
                "OWNER_BLOCKED: renderer/H3 qualification is not approved; refusing before queue or cost"
            )
        raise UnsupportedRecipeError(
            "recipe/profile is outside the versioned pinned allowlist; no caller graph or endpoint is accepted"
        )

    def _scene(self, project_id: str, scene_revision_id: str, shot_id: str) -> tuple[SceneRevision, ShotSpec]:
        scene = self._store.get_scene_revision(project_id, scene_revision_id)
        shot = next((item for item in scene.shots if item.id == shot_id), None)
        if shot is None:
            raise UnsupportedRecipeError(f"shot {shot_id} is not in scene revision {scene_revision_id}")
        return scene, shot

    def _reference_hashes(self, project_id: str, character_version: tuple[str, int]) -> list[str]:
        if not isinstance(character_version, tuple) or len(character_version) != 2:
            raise UnsupportedRecipeError("character_version must be an ordered character/version pair")
        try:
            character = self._store.get_character_version(*character_version)
        except WorkspaceStoreError as error:
            raise UnsupportedRecipeError("character version is unavailable or malformed") from error
        if len(character.reference_asset_ids) != 2:
            raise UnsupportedRecipeError(
                "offline CPU routing is qualified for exactly two ordered references"
            )
        hashes: list[str] = []
        for asset_id in character.reference_asset_ids:
            try:
                resolved = self._store.resolve_asset(asset_id)
            except AssetIntegrityError as error:
                raise RecipeIntegrityError("character reference bytes changed") from error
            record = resolved.record
            if (
                record.project_id != project_id
                or not record.protected
                or record.role not in {"reference_1", "reference_2"}
            ):
                raise RecipeIntegrityError("character reference is not protected and project-owned")
            hashes.append(record.sha256)
        return hashes

    def _pinned_graph(self, pin: RecipePin) -> tuple[dict[str, Any], str]:
        raw_sha256 = _sha256(WORKFLOW_PATH)
        if raw_sha256 != pin.raw_graph_sha256:
            raise RecipeIntegrityError(
                "pinned raw graph bytes changed; refusing resolution before execution"
            )
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        if not isinstance(workflow, dict):
            raise RecipeIntegrityError("pinned raw graph root is malformed")
        return workflow, raw_sha256

    def _extract_cpu_input(
        self, project_id: str, source: Path, window_json: dict[str, Any]
    ) -> AssetRecord:
        start = int(window_json["source_range"]["start"])
        end = int(window_json["source_range"]["end"])
        expected = CPU_CLIP_SHA256.get((start, end))
        if expected is None:
            raise UnsupportedRecipeError("CPU input window is outside the finite table")
        managed = self._store.root / "managed"
        managed.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cpu-input-", dir=managed) as temporary:
            clip = Path(temporary) / f"cpu-{start}-{end}.nut"
            expression = f"select='between(n\\,{start}\\,{end - 1})',setpts=PTS-STARTPTS"
            _run_tool([
                "ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(source),
                "-vf", expression, "-fps_mode", "passthrough", "-map", "0:v:0",
                "-c:v", "ffv1", "-level", "3", "-g", "1", "-pix_fmt", "yuv420p",
                "-f", "nut", str(clip),
            ])
            content = clip.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if digest != expected:
                raise RecipeIntegrityError("extracted CPU input does not match its frozen hash")
            if _raw_frames(source, start, end) != _raw_frames(clip, 0, end - start):
                raise RecipeIntegrityError("extracted CPU pixels do not match original frames")
            probe = json.loads(_run_tool([
                "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                "-show_entries", "stream=nb_read_frames,time_base:frame=pts,duration",
                "-of", "json", str(clip),
            ]).stdout)
            frames = probe.get("frames", [])
            stream = probe["streams"][0]
            if len(frames) != end - start or int(stream["nb_read_frames"]) != end - start:
                raise RecipeIntegrityError("extracted CPU frame count is not exact")
            duration = int(frames[0]["duration"])
            stream_timebase = Fraction(str(stream["time_base"]))
            for index, frame in enumerate(frames):
                if int(frame.get("pts", -1)) != index * duration or int(frame.get("duration", 0)) != duration:
                    raise RecipeIntegrityError("extracted CPU frame PTS sequence is invalid")
            if duration * stream_timebase != Fraction(1, 24):
                raise RecipeIntegrityError("extracted CPU frame period is not exactly 1/24")
            return self._store.stage_asset(
                project_id, clip.name, io.BytesIO(content), role="cpu_input", protected=True
            )

    @staticmethod
    def _model_requirements(raw_graph: dict[str, Any]) -> list[dict[str, str]]:
        requirements: list[dict[str, str]] = []
        for node_id, field in (("1", "clip_name"), ("586", "lora_name")):
            node = raw_graph.get(node_id, {})
            value = node.get("inputs", {}).get(field)
            if isinstance(value, str):
                requirements.append({
                    "node": node_id,
                    "requirement": value,
                    "support": "not_evaluated_non_inference",
                })
        return requirements

    @staticmethod
    def _manifest(
        *,
        scene: SceneRevision,
        shot: ShotSpec,
        character_version: tuple[str, int],
        references: list[str],
        seed: int,
        raw_graph_sha256: str,
        raw_graph: dict[str, Any],
        resolved_graph_sha256: str,
        prepared_workflow_sha256: str,
        prompt_sha256: str,
        word_schedule_sha256: str,
        window_json: dict[str, Any],
        input_sha256: str,
        input_policy: str,
    ) -> dict[str, Any]:
        period = {"num": scene.source.timebase.num, "den": scene.source.timebase.den}
        return {
            "manifest_version": 1,
            "recipe": {"recipe_id": OFFLINE_PIN.recipe_id, "version": OFFLINE_PIN.version,
                "allowlist_version": ALLOWLIST_VERSION, "profile_id": OFFLINE_PIN.profile_id,
                "execution_mode": "dry_run", "qualification_scope": "offline_cpu_routing_only",
                "cpu_window_table_version": "openjutsu-cpu-routing-windows-v1-20261027",
                "non_inference": True, "h3_qualified": False},
            "source": {
                "sha256": scene.source.sha256,
                "proxy_sha256": input_sha256,
                "proxy_policy": input_policy,
                "frame_count": scene.source.frame_count,
                "timebase": period,
                "cfr": scene.source.cfr,
                "has_audio": scene.source.has_audio,
                "original_pts": {"coordinate": "zero_based_half_open_source_frames",
                    "first_frame": shot.source_range.start, "frame_period_seconds": period,
                    "source_to_render_frame_offset": -shot.source_range.start,
                    "formula": "frame_index * frame_period_seconds"},
            },
            "scene": {
                "scene_revision_id": scene.id,
                "shot_id": shot.id,
                "source_range": {"start": shot.source_range.start, "end": shot.source_range.end},
            },
            "window": window_json,
            "graph": {"raw_sha256": raw_graph_sha256,
                "resolved_semantic_sha256": resolved_graph_sha256,
                "prepared_workflow_sha256": prepared_workflow_sha256,
                "node_model_requirements": RecipeService._model_requirements(raw_graph)},
            "prompt": {"sha256": prompt_sha256, "word_schedule_sha256": word_schedule_sha256},
            "character": {"version": list(character_version), "reference_hashes": references},
            "seed": seed,
            "effective_overrides": {
                "fps_timebase": {"num": window_json["source_timebase"]["num"],
                                  "den": window_json["source_timebase"]["den"]},
                "start_f": window_json["render_range"]["start"],
                "end_f": window_json["render_range"]["end"],
                "word_offset_frames": window_json["source_range"]["start"],
                "pad_left": window_json["pad_left"],
                "pad_right": window_json["pad_right"],
                "with_audio": window_json["source_range"] == {"start": 0, "end": 24}
                    and scene.source.has_audio,
                "scheduler_steps": 8,
                "lora_model_strength": 1.0,
                "source_blur": {"mode": "head + hands (keep mouth)", "strength": 1.0,
                    "segmenter": "SAM 3.1", "effect": "blur"},
                "audio": {"source_start_frame": window_json["pad_left"], "gain_db": 0.0,
                    "mix_policy": "sum", "overflow_policy": "crop"},
            },
            "adapter": {"version": OFFLINE_PIN.adapter_version,
                "endpoint_fingerprint": OFFLINE_PIN.endpoint_fingerprint},
            "audio_policy": AudioPolicy.SOURCE_EDIT_MAP.value,
        }

    def resolve(
        self,
        project_id: str,
        scene_revision_id: str,
        shot_id: str,
        pin: RecipePin,
        character_version: tuple[str, int],
        seed: int,
        *,
        rights_attested: bool = False,
        word_timing: WordTiming | None = None,
    ) -> ResolvedOperation:
        if rights_attested is not True:
            raise UnsupportedRecipeError(
                "rights_attested must be explicitly true before managed resolution"
            )
        pinned = self._pin(pin)
        scene, shot = self._scene(project_id, scene_revision_id, shot_id)
        try:
            window = SceneService(self._store).validate_window(shot, pinned)
        except SceneServiceError as error:
            raise UnsupportedRecipeError(str(error)) from error
        source = self._store.resolve_asset(scene.source.asset_id).record
        if (
            source.project_id != project_id
            or not source.protected
            or source.role != "source"
            or scene.source.sha256 != OFFLINE_SOURCE_SHA256
            or scene.source.frame_count != 24
            or scene.source.timebase.num != 1
            or scene.source.timebase.den != 24
        ):
            raise UnsupportedRecipeError(
                "source is not the exact pinned offline CPU routing fixture"
            )
        references = self._reference_hashes(project_id, character_version)
        timing_content = None
        if word_timing is not None:
            if not isinstance(word_timing, WordTiming):
                raise UnsupportedRecipeError("word_timing must be a validated WordTiming")
            timing_source = self._store.resolve_asset(word_timing.source_asset_id).record
            if (timing_source.asset_id != scene.source.asset_id
                    or timing_source.project_id != project_id or not timing_source.protected
                    or timing_source.role != "source"
                    or timing_source.sha256 != scene.source.sha256
                    or timing_source.sha256 != word_timing.source_sha256):
                raise UnsupportedRecipeError("word timing source ownership or digest mismatch")
            duration = Fraction(scene.source.frame_count * scene.source.timebase.num,
                                scene.source.timebase.den)
            if any(word.end > duration for word in word_timing.words):
                raise UnsupportedRecipeError("word timing exceeds original source duration")
            timing_content = public_json({"schema_version": 1,
                "coordinate": "original_source_seconds", "source_sha256": timing_source.sha256,
                "segments": [{"words": [json.loads(word.to_json()) for word in word_timing.words]}]})
        if list(OFFLINE_REFERENCE_SHA256) != references:
            raise UnsupportedRecipeError(
                "ordered character reference hashes do not match the pinned offline fixture"
            )
        raw_graph, raw_graph_sha256 = self._pinned_graph(pinned)
        window_json = json.loads(window.to_json())
        character = self._store.get_character_version(*character_version)
        source_path = self._store.resolve_asset(scene.source.asset_id).path
        if shot.source_range == FrameRange(0, 24):
            input_record, input_path = source, source_path
            input_policy, input_has_audio = "original_protected_bytes", scene.source.has_audio
        else:
            input_record = self._extract_cpu_input(project_id, source_path, window_json)
            input_path = self._store.resolve_asset(input_record.asset_id).path
            input_policy, input_has_audio = "lossless_ffv1_extract", False
        job_id = "managed-" + uuid.uuid4().hex
        settings = load_settings({
            "RECASTROOM_BACKEND": "dry_run",
            "RECASTROOM_DATA_DIR": str(self._store.root / "managed"),
            "RECASTROOM_FFMPEG": "ffmpeg",
            "RECASTROOM_FFPROBE": "ffprobe",
            "RECASTROOM_WHISPER": "whisper",
        })
        words_path = None
        if timing_content is not None:
            words_path = settings.data_dir / "jobs" / job_id / "word-timing.json"
            words_path.parent.mkdir(parents=True, exist_ok=True)
            words_path.write_bytes(timing_content.encode("utf-8"))
        prepared = prepare_managed_workflow(
            settings,
            job_id=job_id,
            source=input_path,
            reference_1=self._store.resolve_asset(character.reference_asset_ids[0]).path,
            reference_2=self._store.resolve_asset(character.reference_asset_ids[1]).path,
            words_path=words_path,
            rights_attested=rights_attested,
            window=window,
            source_has_audio=input_has_audio,
            with_audio=input_has_audio,
            seed=seed,
            workflow_template=raw_graph,
        )
        resolved_graph_sha256 = _json_digest(prepared.effective_workflow)
        prompt_digest = hashlib.sha256(prepared.prompt.encode("utf-8")).hexdigest()
        word_digest = hashlib.sha256(prepared.word_schedule.encode("utf-8")).hexdigest()
        manifest = self._manifest(
            scene=scene,
            shot=shot,
            character_version=character_version,
            references=references,
            seed=seed,
            raw_graph_sha256=raw_graph_sha256,
            raw_graph=raw_graph,
            resolved_graph_sha256=resolved_graph_sha256,
            prepared_workflow_sha256=prepared.effective_workflow_sha256,
            prompt_sha256=prompt_digest,
            word_schedule_sha256=word_digest,
            window_json=window_json,
            input_sha256=input_record.sha256,
            input_policy=input_policy,
        )
        timing_binding = None
        if timing_content is not None:
            manifest["word_timing"] = {"coordinate": "original_source_seconds",
                "source_sha256": word_timing.source_sha256,
                "word_timing_sha256": hashlib.sha256(timing_content.encode("utf-8")).hexdigest(),
                "original_word_count": len(word_timing.words),
                "clipped_word_count": len(prepared.effective_words)}
            timing_binding = {**manifest["word_timing"], "canonical_content": timing_content}
        canonical_json = public_json(manifest)
        operation = ResolvedOperation(
            id="operation-" + uuid.uuid4().hex,
            project_id=project_id,
            scene_revision_id=scene.id,
            shot_id=shot.id,
            window=window,
            pin=pinned,
            character_version=character_version,
            seed=seed,
            canonical_json=canonical_json,
            fingerprint=hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
            managed_job_id=job_id,
        )
        return self._bind_operation(
            operation, prepared, source, input_record, character, prompt_digest, word_digest,
            timing_binding,
        )

    def _bind_operation(
        self,
        operation: ResolvedOperation,
        prepared: ManagedWorkflowPreparation,
        source: AssetRecord,
        input_record: AssetRecord,
        character: Any,
        prompt_digest: str,
        word_digest: str,
        timing_binding: dict[str, Any] | None = None,
    ) -> ResolvedOperation:
        graph_bytes = Path(prepared.job.workflow_path).read_bytes()
        graph_asset = self._store.stage_asset(
            operation.project_id, "managed-workflow.json", io.BytesIO(graph_bytes),
            role="managed_graph", protected=True,
        )
        references = [
            self._store.resolve_asset(asset_id).record
            for asset_id in character.reference_asset_ids
        ]
        plan = json.loads(prepared.workflow["1189"]["inputs"]["plan"])
        envelope = {
            "schema_version": 1,
            "operation_id": operation.id,
            "operation_fingerprint": operation.fingerprint,
            "graph": {"asset_id": graph_asset.asset_id, "sha256": graph_asset.sha256,
                "semantic_sha256": _json_digest(prepared.effective_workflow)},
            "source": {"asset_id": source.asset_id, "sha256": source.sha256},
            "references": [{"asset_id": item.asset_id, "sha256": item.sha256} for item in references],
            "cpu_input": {"asset_id": input_record.asset_id, "sha256": input_record.sha256,
                "original_range": [operation.window.source_range.start, operation.window.source_range.end],
                "render_range": [operation.window.render_range.start, operation.window.render_range.end]},
            "substitutions": {
                "planner": {"video": plan["video"], "global_ref": plan["global_ref"],
                    "global_ref2": plan["global_ref2"], "source_asset_id": input_record.asset_id,
                    "reference_asset_ids": character.reference_asset_ids},
                "outputs": {"primary": prepared.workflow["751"]["inputs"]["filename_prefix"],
                    "comparison": prepared.workflow["1110"]["inputs"]["filename_prefix"]},
            },
            "prompt_content": prepared.prompt,
            "word_schedule_content": prepared.word_schedule,
            "prompt_sha256": prompt_digest,
            "word_schedule_sha256": word_digest,
            "adapter_version": OFFLINE_PIN.adapter_version,
            "endpoint_fingerprint": OFFLINE_PIN.endpoint_fingerprint,
        }
        if timing_binding is not None:
            envelope["word_timing"] = timing_binding
        content = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
        binding_asset = self._store.stage_asset(
            operation.project_id, "preparation-binding.json", io.BytesIO(content),
            role="preparation_binding", protected=True,
        )
        binding = BoundSubmission(
            operation.id, binding_asset.asset_id, binding_asset.sha256, False
        )
        return self._store._save_operation_and_preparation(
            operation, binding, source_asset_id=source.asset_id,
            reference_asset_ids=tuple(item.asset_id for item in references),
        )
