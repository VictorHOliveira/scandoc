import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth_routes, payment_routes, plan_routes, routes, webhook_routes
from .core import config, db, firebase

logger = logging.getLogger("scandoc")

DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", ",".join(DEFAULT_ORIGINS)).split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        firebase.init_firebase()
        db.seed_plans(db.get_firestore())
    except firebase.FirebaseNotConfiguredError as exc:
        logger.warning("%s — os endpoints retornarão 503 até que o Firebase seja configurado.", exc)
    except firebase.FirebaseConfigurationError as exc:
        logger.warning("%s — os endpoints retornarão 503 até que a configuração seja corrigida.", exc)
    except Exception:
        logger.exception("Falha ao inicializar o Firebase — os endpoints retornarão 503.")
    yield


app = FastAPI(
    title="ScannerDocumento API",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs" if config.ENABLE_DOCS else None,
    redoc_url="/redoc" if config.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if config.ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response

app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(plan_routes.router, prefix="/api/plans", tags=["plans"])
app.include_router(payment_routes.router, prefix="/api", tags=["subscriptions"])
app.include_router(webhook_routes.router, prefix="/api", tags=["webhooks"])
app.include_router(routes.router, prefix="/api", tags=["scan"])


@app.get("/")
def root():
    return {"app": "ScannerDocumento API", "docs": "/docs"}
