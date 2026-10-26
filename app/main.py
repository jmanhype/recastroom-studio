# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import threading
import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from openjutsu.comfy_legacy import ComfyLegacyRunner
from openjutsu.comfy_sdk_runner import ComfySdkConfigurationError, ComfySdkRunner
from openjutsu.archive import ArchiveSearchError, search_public_video_sources
from openjutsu.config import load_settings
from openjutsu.media import make_side_by_side, restore_source_audio
from openjutsu.pipeline import prepare_workflow
from openjutsu.readiness import renderer_readiness
from openjutsu.scene import analyze_scene
from openjutsu.studio_catalog import catalog


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = load_settings()
SETTINGS.data_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="RecastRoom Studio", version="0.1.1")
JOB_STATUS: dict[str, dict] = {}
JOB_LOCKS: dict[str, threading.Lock] = {}
STATUS_LOCK = threading.Lock()


@app.get("/api/health")
def health() -> dict:
    renderer = renderer_readiness(SETTINGS.backend, SETTINGS.comfy_url).as_dict()
    return {
        "ok": True,
        "workflow": SETTINGS.workflow.name,
        "workflow_exists": SETTINGS.workflow.is_file(),
        "backend": SETTINGS.backend,
        "renderer_ready": renderer["ready"],
        "renderer": renderer,
    }


@app.get("/api/workflows")
def workflows() -> dict:
    return catalog()


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


@app.post("/api/prepare")
async def prepare(
    background_tasks: BackgroundTasks,
    source: UploadFile = File(...),
    reference_1: UploadFile = File(...),
    reference_2: UploadFile | None = File(None),
    words: UploadFile | None = File(None),
    workflow: UploadFile | None = File(None),
    identity: str = Form(""),
    rights_attested: bool = Form(False),
    seed: int = Form(49),
) -> JSONResponse:
    if not rights_attested:
        raise HTTPException(status_code=422, detail="Operator attestation is required.")

    job_id = uuid.uuid4().hex[:12]
    upload_dir = SETTINGS.data_dir / "uploads" / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved: dict[str, Path] = {}
    for key, upload in {
        "source": source,
        "reference_1": reference_1,
        "reference_2": reference_2 if reference_2 and reference_2.filename else None,
        "words": words if words and words.filename else None,
        "workflow": workflow if workflow and workflow.filename else None,
    }.items():
        if upload is None:
            continue
        destination = upload_dir / Path(upload.filename or key).name
        with destination.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        saved[key] = destination

    try:
        report = analyze_scene(saved["source"], SETTINGS.ffprobe)
        job, workflow = prepare_workflow(
            SETTINGS,
            job_id=job_id,
            source=saved["source"],
            reference_1=saved["reference_1"],
            reference_2=saved.get("reference_2"),
            words_path=saved.get("words"),
            workflow_template=saved.get("workflow"),
            rights_attested=True,
            identity_description=identity or None,
            seed=seed,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    background_tasks.add_task(lambda: None)
    return JSONResponse(
        {
            "job_id": job_id,
            "scene": _public_scene(report),
            "manifest": _public_manifest(job),
            "workflow_url": f"/api/jobs/{job_id}/workflow",
            "prompt_url": f"/api/jobs/{job_id}/prompt",
        }
    )


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


def _require_recorded_attestation(manifest: dict, backend: str) -> None:
    if not manifest.get("rights_attested"):
        raise RuntimeError(f"{backend} execution requires a recorded operator attestation")


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
            _require_recorded_attestation(manifest, "Dry-run")

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
                message="Deterministic dry-run generation",
                prompt_id=prompt_id,
            )
            _set_status(
                job_id,
                state="downloading",
                backend="dry_run",
                message="Copying deterministic fixture output",
                prompt_id=prompt_id,
            )
            generated = job_dir / "generated.mp4"
            shutil.copyfile(source, generated)
            _complete_media_job(
                job_id,
                backend="dry_run",
                generated=generated,
                source=source,
                message="Deterministic dry-run generation complete",
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
            _require_recorded_attestation(manifest, "Legacy ComfyUI")
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
            _require_recorded_attestation(manifest, "Official Comfy SDK")
            _set_status(job_id, state="generating", message="Submitting official Comfy SDK job")
            runner = ComfySdkRunner(api_key=SETTINGS.comfy_api_key)
            saved = runner.run_workflow(
                workflow, job_dir / "sdk_outputs", source=manifest["source"],
                reference_1=manifest["reference_1"], reference_2=manifest.get("reference_2"),
            )
            mp4s = [path for path in saved if path.suffix.lower() == ".mp4"]
            if not mp4s:
                raise RuntimeError("Comfy SDK returned no MP4 output")
            _complete_media_job(
                job_id,
                backend="sdk",
                generated=mp4s[0],
                source=Path(manifest["source"]),
                message="Official Comfy SDK generation complete",
            )
        except ComfySdkConfigurationError as error:
            _set_status(
                job_id,
                state="error",
                backend="sdk",
                message=error.message,
                error=error.as_dict(),
            )
        except RuntimeError as error:
            _set_status(job_id, state="error", backend="sdk", message=str(error))
        except Exception as error:
            _set_status(job_id, state="error", backend="sdk",
                        message="SDK operation failed. Check local submission state before retrying.")


@app.post("/api/jobs/{job_id}/run")
def run_job(job_id: str, background_tasks: BackgroundTasks) -> JSONResponse:
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


app.mount("/", StaticFiles(directory=ROOT / "app/web", html=True), name="web")
