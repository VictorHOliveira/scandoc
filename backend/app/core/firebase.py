import json
import logging
import os
import time

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, firestore as firestore_admin

from .config import (
    FIREBASE_AUTH_EMULATOR_HOST,
    FIREBASE_CREDENTIALS,
    FIREBASE_EMULATOR_HOST,
    FIREBASE_PROJECT_ID,
)

logger = logging.getLogger("scandoc.firebase")

_app = None
_emulator_client = None


class FirebaseNotConfiguredError(RuntimeError):
    pass


class FirebaseConfigurationError(RuntimeError):
    pass


def _load_credentials():
    value = FIREBASE_CREDENTIALS
    if value is None:
        return None
    if value.lstrip().startswith("{"):
        try:
            creds = json.loads(value)
        except json.JSONDecodeError as exc:
            raise FirebaseConfigurationError(
                "FIREBASE_SERVICE_ACCOUNT parece ser JSON, mas não é um JSON válido. "
                "Cole o conteúdo completo do arquivo do service account."
            ) from exc
        required = {"type", "project_id", "client_email", "private_key"}
        missing = required - set(creds)
        if missing:
            raise FirebaseConfigurationError(
                "FIREBASE_SERVICE_ACCOUNT não contém os campos necessários "
                f"({', '.join(sorted(missing))}). Use o JSON completo do service account."
            )
        return creds
    if os.path.isfile(value):
        return value
    raise FirebaseConfigurationError(
        "FIREBASE_SERVICE_ACCOUNT não é um JSON válido nem um caminho de arquivo existente. "
        "Cole o JSON completo do service account ou informe um caminho válido."
    )


def init_firebase() -> None:
    global _app
    if _app is not None:
        return

    if FIREBASE_AUTH_EMULATOR_HOST:
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = FIREBASE_AUTH_EMULATOR_HOST
    if FIREBASE_EMULATOR_HOST:
        os.environ["FIRESTORE_EMULATOR_HOST"] = FIREBASE_EMULATOR_HOST

    project_id = FIREBASE_PROJECT_ID or ("demo-scandoc" if (FIREBASE_EMULATOR_HOST or FIREBASE_AUTH_EMULATOR_HOST) else None)

    if FIREBASE_CREDENTIALS:
        _app = firebase_admin.initialize_app(
            credentials.Certificate(_load_credentials()),
            {"projectId": project_id} if project_id else {},
        )
    elif FIREBASE_EMULATOR_HOST or FIREBASE_AUTH_EMULATOR_HOST:
        _app = firebase_admin.initialize_app(options={"projectId": project_id})
    else:
        raise FirebaseNotConfiguredError(
            "Firebase não configurado. Defina GOOGLE_APPLICATION_CREDENTIALS "
            "apontando para o service account JSON do seu projeto Firebase "
            "(ou FIRESTORE_EMULATOR_HOST/FIREBASE_AUTH_EMULATOR_HOST para usar emuladores)."
        )


def get_firestore():
    global _emulator_client
    if _app is None:
        init_firebase()
    if FIREBASE_EMULATOR_HOST:
        if _emulator_client is None:
            from google.auth.credentials import AnonymousCredentials
            from google.cloud import firestore as gcloud_firestore

            _emulator_client = gcloud_firestore.Client(
                project=FIREBASE_PROJECT_ID or "demo-scandoc",
                credentials=AnonymousCredentials(),
            )
        return _emulator_client
    return firestore_admin.client()


def verify_token(token: str) -> dict:
    if _app is None:
        init_firebase()
    for attempt in range(3):
        try:
            decoded = firebase_auth.verify_id_token(token)
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email") or "",
                "name": decoded.get("name") or decoded.get("email") or "",
            }
        except ValueError:
            raise
        except Exception as exc:
            if attempt == 2:
                logger.error("Falha ao verificar token após retries: %r", exc)
                raise
            logger.warning("Falha transiente ao verificar token (tentativa %d): %r", attempt + 1, exc)
            time.sleep(0.5 * (attempt + 1))
