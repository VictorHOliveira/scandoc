import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parents[2]
QUOTA_WINDOW_HOURS = int(os.getenv("QUOTA_WINDOW_HOURS", "24"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
FREE_PLAN_SLUG = "free"
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "0") == "1"

PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "mock").strip().lower()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_BASICO = os.getenv("STRIPE_PRICE_BASICO", "")
STRIPE_PRICE_PROFISSIONAL = os.getenv("STRIPE_PRICE_PROFISSIONAL", "")
STRIPE_PRICE_AVANCADO = os.getenv("STRIPE_PRICE_AVANCADO", "")
STRIPE_PRICE_ILIMITADO = os.getenv("STRIPE_PRICE_ILIMITADO", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5173")
SUBSCRIPTION_DAYS = int(os.getenv("SUBSCRIPTION_DAYS", "30"))

FIREBASE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
    "FIREBASE_SERVICE_ACCOUNT"
)
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")
FIREBASE_AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
