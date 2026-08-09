from fastapi import Header, HTTPException

from ..core import db, firebase
from ..core.firebase import FirebaseNotConfiguredError


def get_db():
    try:
        return db.get_firestore()
    except FirebaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    token = authorization.split(" ", 1)[1]
    try:
        identity = firebase.verify_token(token)
    except FirebaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    fdb = get_db()
    return db.get_or_create_user(
        fdb, identity["uid"], identity.get("email") or "", identity.get("name") or ""
    )
