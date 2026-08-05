import json
import os

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, firestore as firestore_admin

from .config import (
    FIREBASE_AUTH_EMULATOR_HOST,
    FIREBASE_CREDENTIALS,
    FIREBASE_EMULATOR_HOST,
    FIREBASE_PROJECT_ID,
)

_app = None
_emulator_client = None


class FirebaseNotConfiguredError(RuntimeError):
    pass


def _load_credentials():
    value = FIREBASE_CREDENTIALS
    if value is None:
        return None
    if value.lstrip().startswith("{"):
        return json.loads(value)
    return value


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
    decoded = firebase_auth.verify_id_token(token)
    return {
        "uid": decoded["uid"],
        "email": decoded.get("email") or "",
        "name": decoded.get("name") or decoded.get("email") or "",
    }
