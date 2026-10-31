# SPDX-License-Identifier: MIT
from __future__ import annotations

from contextlib import asynccontextmanager
import json
import hashlib
import os
from dataclasses import asdict
from pathlib import Path
import shutil
import tempfile
import threading
import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from openjutsu.comfy_legacy import ComfyLegacyRunner
from openjutsu.comfy_sdk_runner import ComfySdkConfigurationError, ComfySdkRunner
from openjutsu.archive import ArchiveSearchError, search_public_video_sources
from openjutsu.config import load_settings
from openjutsu.media import make_side_by_side, restore_source_audio
from openjutsu.pipeline import prepare_workflow
from openjutsu.readiness import check_sdk_configuration, renderer_readiness
from openjutsu.scene import analyze_scene
from openjutsu.studio_catalog import catalog
from openjutsu.workflow import WorkflowError, prepared_run_contract
from openjutsu.workspace_store import (
    AttemptConflictError,
    AssetIntegrityError,
    NotFoundError,
    UnsafePathError,
    ValidationError,
    WorkspaceStore,
    WorkspaceStoreError,
)
from openjutsu.attempt_worker import _pending, cpu_adapters, run_once

from .project_api import create_project_router
from .m1_api import create_m1_router


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = load_settings()
SETTINGS.data_dir.mkdir(parents=True, exist_ok=True)
OFFICIAL_SDK_PROOF_DIR = ROOT / "docs/evidence/comfy-api-sdk-c1-20261030"
OFFICIAL_SDK_PROOF_MEDIA = {
    "final.mp4": "video/mp4",
    "source_vs_final.mp4": "video/mp4",
    "source_final_contact.jpg": "image/jpeg",
}

JOB_STATUS: dict[str, dict] = {}
JOB_LOCKS: dict[str, threading.Lock] = {}
STATUS_LOCK = threading.Lock()
PROJECT_STORE = WorkspaceStore(SETTINGS.data_dir)
PROJECT_STORE_LOCK = threading.Lock()


@asynccontextmanager
async def _worker_lifespan(_app: FastAPI):
    stop = threading.Event()
    app.state.worker_error = None

    def activate() -> None:
        while not stop.is_set():
            if not (SETTINGS.data_dir / "workspace.sqlite3").is_file():
                stop.wait(0.20)
                continue
            try:
                store = _workspace_store()
                if not _pending(store):
                    stop.wait(0.20)
                    continue
                with store.worker_lock("app-worker"):
                    while not stop.is_set() and _workspace_store() is store:
                        processed = run_once(store, cpu_adapters(store))
                        stop.wait(0.05 if processed else 0.20)
            except AttemptConflictError as error:
                if str(error) != "WORKER_BUSY":
                    app.state.worker_error = type(error).__name__
                    break
                stop.wait(0.20)
            except Exception as error:  # Keep server data private; no traceback is exposed.
                app.state.worker_error = type(error).__name__
                break

    worker = threading.Thread(target=activate, name="openjutsu-managed-worker", daemon=True)
    app.state.worker_thread = worker
    worker.start()
    try:
        yield
    finally:
        stop.set()
        worker.join()
        app.state.worker_error = app.state.worker_error or None


app = FastAPI(title="RecastRoom Studio", version="0.3.5", lifespan=_worker_lifespan)
app.state.workspace_store = PROJECT_STORE


def _workspace_store() -> WorkspaceStore:
    """Follow SETTINGS.data_dir so isolated TestClients cannot share stale state."""
    global PROJECT_STORE
    with PROJECT_STORE_LOCK:
        requested_root = SETTINGS.data_dir.resolve(strict=True)
        if PROJECT_STORE.root != requested_root:
            PROJECT_STORE = WorkspaceStore(SETTINGS.data_dir)
            app.state.workspace_store = PROJECT_STORE
        return PROJECT_STORE


@app.middleware("http")
async def synchronize_workspace_store(request: Request, call_next) -> Response:
    if request.url.path.startswith(("/api/projects", "/api/characters", "/api/assets", "/api/jobs")):
        _workspace_store()
    return await call_next(request)


@app.get("/api/health")
def health() -> dict:
    if SETTINGS.backend == "sdk":
        renderer = check_sdk_configuration(
            SETTINGS.comfy_api_key,
            SETTINGS.comfy_base_url,
            os.environ.get("COMFY_SDK_ASSET_BRIDGE"),
        ).as_dict()
        configuration_ready = renderer["ready"]
    else:
        renderer = renderer_readiness(SETTINGS.backend, SETTINGS.comfy_url).as_dict()
        configuration_ready = renderer["ready"]
    return {
        "ok": True,
        "workflow": SETTINGS.workflow.name,
        "workflow_exists": SETTINGS.workflow.is_file(),
        "backend": SETTINGS.backend,
        "renderer_ready": False if SETTINGS.backend == "sdk" else renderer["ready"],
        "configuration_ready": configuration_ready,
        "renderer": renderer,
    }


@app.get("/api/workflows")
def workflows() -> dict:
    return catalog()


@app.get("/api/proof/comfy-api-sdk-c1")
def official_sdk_proof_summary() -> dict:
    receipt = json.loads(
        (OFFICIAL_SDK_PROOF_DIR / "receipt.json").read_text(encoding="utf-8")
    )
    output = receipt["output"]
    return {
        "kind": "recorded_hosted_h3_proof",
        "adapter": receipt["adapter"],
        "sdk_version": receipt["sdk_version"],
        "cli_version": receipt["cli_version"],
        "build_id": receipt["build_id"],
        "release_id": receipt["release_id"],
        "release_version": receipt["release_version"],
        "job_id": receipt["job_id"],
        "status": receipt["job_status"],
        "submitted_utc": receipt["submitted_utc"],
        "output_ready_utc": receipt["output_ready_utc"],
        "active_render_window_seconds": receipt["active_render_window_seconds"],
        "workflow_sha256": receipt["workflow_sha256"],
        "output_sha256": output["generated_sha256"],
        "final_sha256": output["final_exact_audio_sha256"],
        "audio_verification": output["audio_verification"],
        "format": output["format"],
        "deployment_teardown": "deleted",
        "media": {
            "final": "/api/proof/comfy-api-sdk-c1/media/final.mp4",
            "comparison": "/api/proof/comfy-api-sdk-c1/media/source_vs_final.mp4",
            "contact_sheet": "/api/proof/comfy-api-sdk-c1/media/source_final_contact.jpg",
        },
    }


@app.get("/api/proof/comfy-api-sdk-c1/media/{artifact}")
def official_sdk_proof_media(artifact: str) -> FileResponse:
    media_type = OFFICIAL_SDK_PROOF_MEDIA.get(artifact)
    if media_type is None:
        raise HTTPException(status_code=404, detail="Unknown proof artifact")
    return FileResponse(OFFICIAL_SDK_PROOF_DIR / artifact, media_type=media_type)


@app.get("/api/archive/sources")
def archive_sources(query: str, collection: str = "prelinger", limit: int = 12) -> JSONResponse:
    try:
        return JSONResponse(search_public_video_sources(query, collection=collection, limit=limit))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ArchiveSearchError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


def _public_manifest(job: object) -> dict:
    payload = json.loads(job.to_json())  # type: ignore[attr-defined]
    for key in ("source", "reference_1", "reference_2", "word_schedule_path", "workflow_path", "prompt_path"):
        if payload.get(key) is not None:
            payload[key] = Path(payload[key]).name
    return payload


def _public_scene(report: object) -> dict:
    payload = json.loads(report.to_json())  # type: ignore[attr-defined]
    if payload.get("path") is not None:
        payload["path"] = Path(payload["path"]).name
    return payload


def _store_error(error: WorkspaceStoreError) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, AssetIntegrityError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, (ValidationError, UnsafePathError)):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=503, detail="Workspace store operation failed.")


def _has_upload(upload: UploadFile | None) -> bool:
    return upload is not None and bool(upload.filename)


def _reject_upload_basename_collisions(uploads: dict[str, UploadFile | None]) -> None:
    """Reject present uploads whose flattened destinations would collide."""
    owners: dict[str, str] = {}
    for role, upload in uploads.items():
        if upload is None or not upload.filename:
            continue
        basename = Path(upload.filename or role).name
        previous_role = owners.get(basename)
        if previous_role is not None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Upload filename collision for {basename}: {previous_role} and {role}. "
                    "Rename one of the uploads before preparing again."
                ),
            )
        owners[basename] = role


def _saved_references(
    store: WorkspaceStore,
    project_id: str,
    character_id: str,
    character_version: int,
) -> list[Path]:
    project = store.get_project(project_id)
    character = store.get_character_version(character_id, character_version)
    return [store.resolve_asset(asset_id).path for asset_id in character.reference_asset_ids]


def _prepare_reference_selection(
    project_id: str,
    character_id: str,
    character_version: int,
    reference_1: UploadFile | None,
    reference_2: UploadFile | None,
) -> list[Path] | None:
    """Validate reference selection and return saved paths when used."""
    uploaded_reference_1 = _has_upload(reference_1)
    uploaded_reference_2 = _has_upload(reference_2)
    saved_reference_paths: list[Path] | None = None
    if uploaded_reference_2 and not uploaded_reference_1:
        raise HTTPException(status_code=422, detail="A primary reference is required with a secondary reference.")
    if character_id or character_version:
        if not character_id or character_version < 1:
            raise HTTPException(status_code=422, detail="A saved character requires character_id and a positive version.")
        if not project_id:
            raise HTTPException(status_code=422, detail="A project is required to use a saved character.")
        if uploaded_reference_1 or uploaded_reference_2:
            raise HTTPException(status_code=422, detail="Choose either uploaded references or one saved character version, not both.")
        try:
            saved_reference_paths = _saved_references(
                _workspace_store(), project_id, character_id, character_version
            )
        except WorkspaceStoreError as error:
            raise _store_error(error) from error
    elif not uploaded_reference_1:
        raise HTTPException(status_code=422, detail="Choose an uploaded primary reference or a saved character version.")
    if project_id and saved_reference_paths is None:
        try:
            _workspace_store().get_project(project_id)
        except WorkspaceStoreError as error:
            raise _store_error(error) from error
    return saved_reference_paths


@app.post("/api/prepare")
async def prepare(
    background_tasks: BackgroundTasks,
    source: UploadFile = File(...),
    reference_1: UploadFile | None = File(None),
    reference_2: UploadFile | None = File(None),
    words: UploadFile | None = File(None),
    workflow: UploadFile | None = File(None),
    identity: str = Form(""),
    rights_attested: bool = Form(False),
    seed: int = Form(49),
    project_id: str = Form(""),
    character_id: str = Form(""),
    character_version: int = Form(0),
) -> JSONResponse:
    if not rights_attested:
        raise HTTPException(status_code=422, detail="Permission declaration is required.")
    if not source.filename:
        raise HTTPException(status_code=422, detail="A source clip is required.")

    selected_project_id: str | None = project_id or None
    saved_reference_paths = _prepare_reference_selection(
        project_id,
        character_id,
        character_version,
        reference_1,
        reference_2,
    )

    uploads = {
        "source": source,
        "reference_1": reference_1 if _has_upload(reference_1) else None,
        "reference_2": reference_2 if _has_upload(reference_2) else None,
        "words": words if words and words.filename else None,
        "workflow": workflow if workflow and workflow.filename else None,
    }
    _reject_upload_basename_collisions(uploads)

    job_id = uuid.uuid4().hex[:12]
    upload_dir = SETTINGS.data_dir / "uploads" / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved: dict[str, Path] = {}
    for key, upload in uploads.items():
        if upload is None:
            continue
        destination = upload_dir / Path(upload.filename or key).name
        with destination.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        saved[key] = destination

    try:
        report = analyze_scene(saved["source"], SETTINGS.ffprobe)
        reference_paths = (
            saved_reference_paths
            if saved_reference_paths is not None
            else [saved["reference_1"], *([saved["reference_2"]] if "reference_2" in saved else [])]
        )
        job, workflow = prepare_workflow(
            SETTINGS,
            job_id=job_id,
            source=saved["source"],
            reference_1=reference_paths[0],
            reference_2=reference_paths[1] if len(reference_paths) > 1 else None,
            words_path=saved.get("words"),
            workflow_template=saved.get("workflow"),
            rights_attested=True,
            identity_description=identity or None,
            seed=seed,
        )
        contract = prepared_run_contract(
            workflow,
            prompt=Path(job.prompt_path).read_text(encoding="utf-8"),
            timing_input="supplied" if "words" in saved else "omitted",
            timing_basis=(
                "Whisper JSON at default 24 fps"
                if "words" in saved
                else "Default 24 fps fallback schedule"
            ),
        )
    except (ValueError, WorkflowError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    background_tasks.add_task(lambda: None)
    prepared_record = None
    if selected_project_id is not None:
        try:
            prepared_record = _workspace_store().record_prepared_job(
                selected_project_id,
                job_id,
                SETTINGS.data_dir / "jobs" / job_id,
                (character_id, character_version) if character_id else None,
            )
        except WorkspaceStoreError as error:
            raise _store_error(error) from error
    payload = {
        "job_id": job_id,
        "scene": _public_scene(report),
        "manifest": _public_manifest(job),
        "contract": contract,
        "workflow_url": f"/api/jobs/{job_id}/workflow",
        "prompt_url": f"/api/jobs/{job_id}/prompt",
    }
    if prepared_record is not None:
        payload["project_id"] = selected_project_id
        payload["prepared"] = asdict(prepared_record)
    return JSONResponse(payload)


def _job_path(job_id: str, filename: str) -> Path:
    if not job_id.isalnum() or len(job_id) not in (8, 12, 16, 32):
        raise HTTPException(status_code=404, detail="Job not found")
    path = SETTINGS.data_dir / "jobs" / job_id / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Job artifact not found")
    return path


def _job_dir(job_id: str) -> Path:
    if not job_id.isalnum() or len(job_id) not in (8, 12, 16, 32):
        raise HTTPException(status_code=404, detail="Job not found")
    path = SETTINGS.data_dir / "jobs" / job_id
    if not path.is_dir():
        raise HTTPException(status_code=404, detail="Job not found")
    return path


def _sdk_submission_projection(job_dir: Path) -> dict[str, object]:
    """Project durable SDK state without exposing keys, fingerprints, or paths."""
    state_path = job_dir / "sdk_outputs" / "submission.json"
    if not state_path.is_file():
        return {"sdk_phase": None, "provider_job_id": None, "retry": "allowed"}
    if state_path.is_symlink():
        return {
            "sdk_phase": "invalid",
            "provider_job_id": None,
            "retry": "blocked",
            "message": "SDK submission state is unreadable; manual reconciliation is required.",
        }
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        phase = state["phase"]
        provider_job_id = state.get("job_id")
        if (
            not isinstance(phase, str)
            or phase not in {"prepared", "submitting", "submitted"}
            or not state.get("key")
        ):
            raise ValueError("invalid SDK submission state")
        if phase == "prepared" and provider_job_id is not None:
            raise ValueError("invalid SDK submission state")
        if provider_job_id is not None and (
            not isinstance(provider_job_id, str)
            or not provider_job_id
            or len(provider_job_id) > 128
        ):
            raise ValueError("invalid provider job ID")
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
        return {
            "sdk_phase": "invalid",
            "provider_job_id": None,
            "retry": "blocked",
            "message": "SDK submission state is unreadable; manual reconciliation is required.",
        }

    retry = "resume" if provider_job_id else ("allowed" if phase == "prepared" else "blocked")
    return {"sdk_phase": phase, "provider_job_id": provider_job_id, "retry": retry}


def _managed_projection(job_id: str) -> dict | None:
    """Project a managed operation/attempt from SQLite, never legacy status files."""
    if not job_id.startswith(("managed-", "attempt-")):
        return None
    store = _workspace_store()
    with store._connect() as db:
        operation = db.execute(
            "SELECT operation_id,project_id,managed_job_id FROM operations WHERE managed_job_id=?",
            (job_id,),
        ).fetchone()
        if operation is not None:
            attempts = db.execute(
                "SELECT * FROM attempts WHERE operation_id=? ORDER BY created_at,attempt_id",
                (operation["operation_id"],),
            ).fetchall()
        else:
            attempts = [db.execute("SELECT * FROM attempts WHERE attempt_id=?", (job_id,)).fetchone()]
    if operation is None and (not attempts or attempts[0] is None):
        return None
    source = operation if operation is not None else attempts[0]
    attempt = attempts[-1] if attempts else None
    state = "resolved" if attempt is None else attempt["state"]
    public_state = {
        "completed": "complete", "failed": "error",
        "provider_confirmed_cancelled": "cancelled",
    }.get(state, "running" if attempt is not None else "resolved")
    return {
        "job_id": job_id,
        "managed": True,
        "backend": "managed",
        "state": public_state,
        "attempt_state": state,
        "project_id": source["project_id"],
        "operation_id": source["operation_id"],
        "attempt_id": attempt["attempt_id"] if attempt is not None else None,
        "attempts_url": f"/api/projects/{source['project_id']}/attempts",
    }


def _require_recorded_attestation(manifest: dict, backend: str) -> None:
    if not manifest.get("rights_attested"):
        raise RuntimeError(f"{backend} execution requires a recorded permission declaration")


def _set_status(job_id: str, **values: object) -> None:
    # Serialize read/merge/publish without sharing the long-running job lock.
    # Readers see either complete snapshot; failed writes leave memory unchanged.
    with STATUS_LOCK:
        status = {
            **JOB_STATUS.get(
                job_id,
                {"job_id": job_id, "state": "queued", "message": "", "artifacts": {}},
            ),
            **values,
        }
        payload = json.dumps(status, indent=2) + "\n"
        destination = SETTINGS.data_dir / "jobs" / job_id / "status.json"
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=destination.parent,
                prefix=".status-", suffix=".tmp", delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(payload)
            os.replace(temporary, destination)
            JOB_STATUS[job_id] = status
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def _complete_media_job(
    job_id: str,
    *,
    backend: str,
    generated: Path,
    source: Path,
    message: str,
    **status: object,
) -> None:
    job_dir = SETTINGS.data_dir / "jobs" / job_id
    final = job_dir / "final.mp4"
    side_by_side = job_dir / "source_vs_final.mp4"
    restore_source_audio(generated, source, final, ffmpeg=SETTINGS.ffmpeg)
    make_side_by_side(source, final, side_by_side, ffmpeg=SETTINGS.ffmpeg)
    _set_status(
        job_id,
        state="complete",
        backend=backend,
        presentation="preview" if backend == "dry_run" else "generation",
        message=message,
        artifacts={
            "generated": generated.name,
            "final": final.name,
            "side_by_side": side_by_side.name,
        },
        **status,
    )


def _run_dry_run_job(job_id: str) -> None:
    lock = JOB_LOCKS.setdefault(job_id, threading.Lock())
    with lock:
        try:
            job_dir = _job_dir(job_id)
            manifest = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
            workflow = json.loads((job_dir / "workflow.json").read_text(encoding="utf-8"))
            _require_recorded_attestation(manifest, "Preview")

            plan = json.loads(workflow["1189"]["inputs"]["plan"])
            source = Path(manifest["source"])
            uploads = {
                "source": plan.get("video"),
                "reference_1": plan.get("global_ref"),
                "reference_2": plan.get("global_ref2") or None,
            }
            if uploads["source"] != source.name:
                raise RuntimeError("Prepared workflow does not route the uploaded source")
            if uploads["reference_1"] != Path(manifest["reference_1"]).name:
                raise RuntimeError("Prepared workflow does not route the primary reference")

            _set_status(
                job_id,
                state="uploading",
                backend="dry_run",
                message="Validating deterministic upload routing",
                uploads=uploads,
            )
            workflow_digest = hashlib.sha256((job_dir / "workflow.json").read_bytes()).hexdigest()
            prompt_id = f"dry-run-{workflow_digest[:16]}"
            _set_status(
                job_id,
                state="generating",
                backend="dry_run",
                message="Validating preview copy · no AI inference",
                prompt_id=prompt_id,
            )
            _set_status(
                job_id,
                state="downloading",
                backend="dry_run",
                message="Preparing preview copy",
                prompt_id=prompt_id,
            )
            generated = job_dir / "generated.mp4"
            shutil.copyfile(source, generated)
            _complete_media_job(
                job_id,
                backend="dry_run",
                generated=generated,
                source=source,
                message="Preview complete · no AI inference or recasting · output copies the source",
                prompt_id=prompt_id,
            )
        except Exception as error:
            _set_status(job_id, state="error", backend="dry_run", message=str(error))


def _run_legacy_job(job_id: str) -> None:
    lock = JOB_LOCKS.setdefault(job_id, threading.Lock())
    with lock:
        try:
            job_dir = _job_dir(job_id)
            manifest = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
            workflow = json.loads((job_dir / "workflow.json").read_text(encoding="utf-8"))
            _require_recorded_attestation(manifest, "ComfyUI")
            runner = ComfyLegacyRunner(SETTINGS.comfy_url)
            _set_status(job_id, state="uploading", message="Uploading source and references")

            source_upload = runner.upload(manifest["source"])
            ref1_upload = runner.upload(manifest["reference_1"])
            ref2_upload = runner.upload(manifest["reference_2"]) if manifest.get("reference_2") else None
            plan = json.loads(workflow["1189"]["inputs"]["plan"])
            plan["video"] = source_upload
            plan["global_ref"] = ref1_upload
            plan["global_ref2"] = ref2_upload or ""
            workflow["1189"]["inputs"]["plan"] = json.dumps(plan, separators=(",", ":"))

            _set_status(
                job_id,
                state="generating",
                message="MiniMax H3 job queued",
                prompt_id=None,
                uploads={"source": source_upload, "reference_1": ref1_upload, "reference_2": ref2_upload},
            )
            result = runner.run(workflow)
            mp4_items = [item for item in result.outputs if item.get("filename", "").endswith(".mp4")]
            if not mp4_items:
                raise RuntimeError("ComfyUI returned no MP4 output")

            _set_status(job_id, state="downloading", message="Downloading H3 output", prompt_id=result.prompt_id)
            generated = runner.download(mp4_items[0], job_dir / "generated.mp4")
            _complete_media_job(
                job_id,
                backend="legacy",
                generated=generated,
                source=Path(manifest["source"]),
                message="Generation complete",
                prompt_id=result.prompt_id,
            )
        except Exception as error:  # FastAPI background task boundary.
            _set_status(job_id, state="error", backend="legacy", message=str(error))


def _run_sdk_job(job_id: str) -> None:
    lock = JOB_LOCKS.setdefault(job_id, threading.Lock())
    with lock:
        try:
            job_dir = _job_dir(job_id)
            manifest = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
            workflow = json.loads((job_dir / "workflow.json").read_text(encoding="utf-8"))
            _require_recorded_attestation(manifest, "Hosted Comfy")
            submission = _sdk_submission_projection(job_dir)
            _set_status(
                job_id,
                state="generating",
                message="Submitting official Comfy SDK job",
                **submission,
            )
            runner = ComfySdkRunner(
                api_key=SETTINGS.comfy_api_key,
                base_url=SETTINGS.comfy_base_url,
            )
            saved = runner.run_workflow(
                workflow, job_dir / "sdk_outputs", source=manifest["source"],
                reference_1=manifest["reference_1"], reference_2=manifest.get("reference_2"),
            )
            mp4s = [path for path in saved if path.suffix.lower() == ".mp4"]
            if not mp4s:
                raise RuntimeError("Comfy SDK returned no MP4 output")
            generated = job_dir / "generated.mp4"
            if mp4s[0] != generated:
                mp4s[0].replace(generated)
            submission = _sdk_submission_projection(job_dir)
            _complete_media_job(
                job_id,
                backend="sdk",
                generated=generated,
                source=Path(manifest["source"]),
                message="Official Comfy SDK generation complete",
                **submission,
            )
        except ComfySdkConfigurationError as error:
            submission = _sdk_submission_projection(job_dir)
            _set_status(
                job_id,
                state="error",
                backend="sdk",
                message=error.message,
                error=error.as_dict(),
                **submission,
            )
        except RuntimeError as error:
            submission = _sdk_submission_projection(job_dir)
            _set_status(job_id, state="error", backend="sdk", message=str(error), **submission)
        except Exception as error:
            submission = _sdk_submission_projection(job_dir)
            message = (
                "SDK outcome is unknown; manual reconciliation is required. Do not start a new submission."
                if submission["retry"] == "blocked"
                else "SDK operation failed. Check local submission state before retrying."
            )
            _set_status(job_id, state="error", backend="sdk",
                        message=message, **submission)


@app.post("/api/jobs/{job_id}/run")
def run_job(job_id: str, background_tasks: BackgroundTasks, request: Request) -> JSONResponse:
    managed = _managed_projection(job_id)
    if managed is not None:
        raise HTTPException(status_code=409, detail={
            "code": "MANAGED_ATTEMPT_REQUIRES_EXPLICIT_AUTHORIZATION",
            "attempts_url": managed["attempts_url"],
        })
    _job_dir(job_id)
    current = JOB_STATUS.get(job_id, {}).get("state")
    if current in {"uploading", "generating", "downloading"}:
        raise HTTPException(status_code=409, detail=f"Job is already {current}")
    if SETTINGS.backend == "legacy":
        renderer = renderer_readiness(SETTINGS.backend, SETTINGS.comfy_url)
        if not renderer.ready:
            raise HTTPException(
                status_code=503,
                detail={"code": renderer.code, "message": renderer.message},
            )
    if SETTINGS.backend == "sdk":
        submission = _sdk_submission_projection(SETTINGS.data_dir / "jobs" / job_id)
        if submission["retry"] == "blocked":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "SDK_SUBMISSION_OUTCOME_UNKNOWN",
                    "message": "The prior SDK submission outcome is unknown; reconcile it before starting another run.",
                    **submission,
                },
            )
        configuration = check_sdk_configuration(
            SETTINGS.comfy_api_key,
            SETTINGS.comfy_base_url,
            os.environ.get("COMFY_SDK_ASSET_BRIDGE"),
        )
        if not configuration.ready:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "code": configuration.code,
                        "message": configuration.message,
                        "environment_variable": configuration.environment_variable,
                    }
                },
            )
    _set_status(job_id, state="queued", message="Queued")
    runners = {
        "legacy": _run_legacy_job,
        "sdk": _run_sdk_job,
        "dry_run": _run_dry_run_job,
    }
    background_tasks.add_task(runners[SETTINGS.backend], job_id)
    return JSONResponse({"job_id": job_id, "state": "queued"})


@app.get("/api/jobs/{job_id}/status")
def job_status(job_id: str) -> dict:
    managed = _managed_projection(job_id)
    if managed is not None:
        return managed
    status_path = _job_path(job_id, "status.json")
    return json.loads(status_path.read_text(encoding="utf-8"))


@app.get("/api/jobs/{job_id}/artifacts/{artifact}")
def job_artifact(job_id: str, artifact: str) -> FileResponse:
    filenames = {
        "generated": "generated.mp4",
        "final": "final.mp4",
        "side_by_side": "source_vs_final.mp4",
    }
    if artifact not in filenames:
        raise HTTPException(status_code=404, detail="Unknown artifact")
    return FileResponse(_job_path(job_id, filenames[artifact]), media_type="video/mp4")


@app.get("/api/jobs/{job_id}/workflow")
def job_workflow(job_id: str) -> FileResponse:
    return FileResponse(_job_path(job_id, "workflow.json"), media_type="application/json")


@app.get("/api/jobs/{job_id}/prompt")
def job_prompt(job_id: str) -> FileResponse:
    return FileResponse(_job_path(job_id, "prompt.txt"), media_type="text/plain")


app.include_router(create_project_router(PROJECT_STORE))
app.include_router(create_m1_router(PROJECT_STORE, ffprobe=SETTINGS.ffprobe))
app.mount("/media", StaticFiles(directory=ROOT / "media"), name="media")
app.mount("/", StaticFiles(directory=ROOT / "app/web", html=True), name="web")
