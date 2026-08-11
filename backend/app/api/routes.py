import threading
import uuid
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request, UploadFile

from ..core import config, db
from ..core.config import MAX_UPLOAD_MB, SHARE_TTL_DAYS
from ..core.jobs import jobs
from ..core.ratelimit import scan_rate_limiter
from ..scanners.common import compute_score
from ..scanners.runner import run_scan
from .deps import get_current_user, get_db

router = APIRouter()


def _to_result(filename: str, raw: dict) -> dict:
    return {
        "filename": filename,
        "format": raw["format"],
        "score": compute_score(raw["findings"]),
        "findings": raw["findings"],
        "hidden_text": raw["hidden_text"],
        "annotated_image": raw["annotated_image"],
        "injection_matches": raw["injection_matches"],
        "summary": raw["summary"],
    }


def _run_in_background(job, filename: str, data: bytes) -> None:
    def set_progress(percent: int, stage: str) -> None:
        jobs.update(job.id, progress={"percent": percent, "stage": stage})

    try:
        raw = run_scan(filename, data, on_progress=set_progress)
    except ValueError as exc:
        jobs.update(job.id, status="error", error=str(exc))
        return
    except Exception:
        jobs.update(job.id, status="error", error="Erro interno ao analisar o arquivo")
        return

    try:
        fdb = db.get_firestore()
        score = compute_score(raw["findings"])
        db.log_scan(fdb, job.uid, filename, raw["format"], score)
    except Exception:
        pass

    jobs.update(job.id, status="done", result=_to_result(filename, raw))


@router.post("/scan")
async def scan(
    file: UploadFile,
    request: Request,
    user: dict = Depends(get_current_user),
):
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    if not scan_rate_limiter.allow(f"{user['uid']}:{ip}"):
        raise HTTPException(
            status_code=429,
            detail="Muitas requisições em pouco tempo. Aguarde um instante e tente novamente.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Arquivo maior que {MAX_UPLOAD_MB}MB")

    fdb = get_db()
    allowed, quota = db.consume_quota(fdb, user["uid"])
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"message": "Limite diário de análises atingido", "quota": quota},
        )

    filename = file.filename or "documento"
    job = jobs.create(user["uid"])
    thread = threading.Thread(
        target=_run_in_background,
        args=(job, filename, data),
        daemon=True,
    )
    thread.start()
    return {"job_id": job.id, "status": job.status}


@router.get("/scan/{job_id}")
def scan_status(
    job_id: str,
    user: dict = Depends(get_current_user),
):
    job = jobs.get(job_id, user["uid"])
    if job is None:
        raise HTTPException(status_code=404, detail="Trabalho de análise não encontrado")
    payload = {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
    }
    if job.status == "done":
        payload["result"] = job.result
    elif job.status == "error":
        payload["error"] = job.error
    return payload


MAX_SHARED_HIDDEN_TEXT = 2000


def _sanitize_shared_result(result: dict) -> dict:
    clean = dict(result)
    hidden = clean.get("hidden_text") or ""
    clean["hidden_text"] = hidden[:MAX_SHARED_HIDDEN_TEXT]
    return clean


@router.post("/shares")
async def create_share(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    job_id = payload.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id é obrigatório")
    job = jobs.get(job_id, user["uid"])
    if job is None or job.status != "done" or job.result is None:
        raise HTTPException(status_code=404, detail="Análise concluída não encontrada")

    share_id = uuid.uuid4().hex[:16]
    fdb = get_db()
    db.save_share(
        fdb,
        share_id,
        user["uid"],
        _sanitize_shared_result(job.result),
        db.now() + timedelta(days=SHARE_TTL_DAYS),
    )
    return {"share_id": share_id}


@router.get("/shares/{share_id}")
def get_share(
    share_id: str,
    fdb=Depends(get_db),
):
    share = db.fetch_share(fdb, share_id)
    if share is None:
        raise HTTPException(status_code=404, detail="Relatório compartilhado não encontrado")
    expires = db.to_dt(share.get("expires_at"))
    if expires is None or expires < db.now():
        raise HTTPException(status_code=404, detail="Relatório compartilhado expirado")
    return {
        "share_id": share_id,
        "created_at": share.get("created_at"),
        "result": share.get("result"),
    }
