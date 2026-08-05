from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..core import db
from ..core.config import MAX_UPLOAD_MB
from ..schemas import ScanResult
from ..scanners.common import compute_score
from ..scanners.runner import run_scan
from .deps import get_current_user, get_db

router = APIRouter()


@router.post("/scan", response_model=ScanResult)
async def scan(
    file: UploadFile,
    user: dict = Depends(get_current_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Arquivo maior que {MAX_UPLOAD_MB}MB")

    filename = file.filename or "documento"
    try:
        raw = run_scan(filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    fdb = get_db()
    allowed, quota = db.consume_quota(fdb, user["uid"])
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"message": "Limite diário de análises atingido", "quota": quota},
        )

    score = compute_score(raw["findings"])
    db.log_scan(fdb, user["uid"], filename, raw["format"], score)

    return ScanResult(
        filename=filename,
        format=raw["format"],
        score=score,
        findings=raw["findings"],
        hidden_text=raw["hidden_text"],
        annotated_image=raw["annotated_image"],
        injection_matches=raw["injection_matches"],
        summary=raw["summary"],
    )
