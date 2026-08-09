from datetime import datetime, timedelta

from google.cloud.firestore import Client as FirestoreClient
from google.cloud.firestore_v1.transaction import transactional

from .config import FREE_PLAN_SLUG, QUOTA_WINDOW_HOURS, SUBSCRIPTION_DAYS
from .firebase import get_firestore

PLANS = [
    {
        "slug": "free",
        "name": "Gratuito",
        "description": "1 análise por dia, para testar.",
        "daily_limit": 1,
        "price_brl": "0.00",
        "sort_order": 0,
    },
    {
        "slug": "basico",
        "name": "Básico",
        "description": "5 análises por dia.",
        "daily_limit": 5,
        "price_brl": "19.90",
        "sort_order": 1,
    },
    {
        "slug": "profissional",
        "name": "Profissional",
        "description": "10 análises por dia.",
        "daily_limit": 10,
        "price_brl": "34.90",
        "sort_order": 2,
    },
    {
        "slug": "avancado",
        "name": "Avançado",
        "description": "20 análises por dia.",
        "daily_limit": 20,
        "price_brl": "49.90",
        "sort_order": 3,
    },
    {
        "slug": "ilimitado",
        "name": "Ilimitado",
        "description": "Análises ilimitadas.",
        "daily_limit": None,
        "price_brl": "79.90",
        "sort_order": 4,
    },
]

PLANS_BY_SLUG = {p["slug"]: p for p in PLANS}


def _now() -> datetime:
    return datetime.utcnow()


def _to_dt(value) -> datetime | None:
    if value is None:
        return None
    if hasattr(value, "timestamp"):
        return datetime.utcfromtimestamp(value.timestamp())
    return value


def seed_plans(db: FirestoreClient) -> None:
    for plan in PLANS:
        db.collection("plans").document(plan["slug"]).set(plan, merge=True)


def list_plans(db: FirestoreClient) -> list[dict]:
    docs = db.collection("plans").stream()
    return sorted(
        [d.to_dict() for d in docs],
        key=lambda p: p.get("sort_order", 99),
    )


def get_plan(db: FirestoreClient, slug: str) -> dict | None:
    snap = db.collection("plans").document(slug).get()
    return snap.to_dict() if snap.exists else PLANS_BY_SLUG.get(slug)


def _user_ref(db: FirestoreClient, uid: str):
    return db.collection("users").document(uid)


def get_user(db: FirestoreClient, uid: str) -> dict | None:
    snap = _user_ref(db, uid).get()
    return snap.to_dict() if snap.exists else None


def get_or_create_user(db: FirestoreClient, uid: str, email: str, name: str) -> dict:
    ref = _user_ref(db, uid)
    snap = ref.get()
    if snap.exists:
        data = snap.to_dict()
        updates = {}
        if email and data.get("email") != email:
            updates["email"] = email
        if name and data.get("name") != name:
            updates["name"] = name
        if updates:
            ref.update(updates)
        return {**data, **updates}
    data = {
        "uid": uid,
        "email": email,
        "name": name or email.split("@")[0],
        "created_at": _now(),
        "plan_slug": FREE_PLAN_SLUG,
        "plan_expires_at": None,
        "quota_used": 0,
        "quota_window_start": _now(),
    }
    ref.set(data)
    return data


def get_active_plan(db: FirestoreClient, uid: str) -> dict:
    user = get_user(db, uid) or {}
    slug = user.get("plan_slug") or FREE_PLAN_SLUG
    expires = _to_dt(user.get("plan_expires_at"))
    if expires is not None and expires < _now():
        slug = FREE_PLAN_SLUG
    return get_plan(db, slug) or PLANS_BY_SLUG[FREE_PLAN_SLUG]


def subscribe(db: FirestoreClient, uid: str, plan_slug: str) -> None:
    ref = _user_ref(db, uid)
    data = {
        "plan_slug": plan_slug,
        "plan_started_at": _now(),
        "plan_expires_at": None,
    }
    ref.set(data, merge=True)


def activate_subscription(
    db: FirestoreClient,
    uid: str,
    plan: dict,
    provider_subscription_id: str | None = None,
    provider: str = "mock",
) -> None:
    ref = _user_ref(db, uid)
    now = _now()
    existing = ref.get().to_dict() or {}
    existing_expires = _to_dt(existing.get("plan_expires_at"))
    base = existing_expires if existing_expires is not None and existing_expires > now else now
    new_expires = base + timedelta(days=SUBSCRIPTION_DAYS)

    ref.set(
        {
            "plan_slug": plan["slug"],
            "plan_started_at": now,
            "plan_expires_at": new_expires,
            "subscription_id": provider_subscription_id,
        },
        merge=True,
    )

    db.collection("subscriptions").document(uid).set(
        {
            "uid": uid,
            "provider": provider,
            "preapproval_id": provider_subscription_id,
            "plan_slug": plan["slug"],
            "status": "active",
            "period_start": now,
            "period_end": new_expires,
            "updated_at": now,
        },
        merge=True,
    )


def cancel_subscription(db: FirestoreClient, uid: str, provider: str = "mock") -> None:
    ref = _user_ref(db, uid)
    user = ref.get().to_dict() or {}
    now = _now()
    sub_ref = db.collection("subscriptions").document(uid)
    sub_ref.set(
        {
            "uid": uid,
            "provider": provider,
            "preapproval_id": user.get("subscription_id"),
            "plan_slug": user.get("plan_slug"),
            "status": "cancelled",
            "period_end": user.get("plan_expires_at"),
            "updated_at": now,
        },
        merge=True,
    )


def get_subscription(db: FirestoreClient, uid: str) -> dict | None:
    snap = db.collection("subscriptions").document(uid).get()
    return snap.to_dict() if snap.exists else None


def quota_status(db: FirestoreClient, uid: str) -> dict:
    user = get_user(db, uid) or {}
    plan = get_active_plan(db, uid)
    used = int(user.get("quota_used", 0))
    window_start = _to_dt(user.get("quota_window_start")) or _now()
    if (_now() - window_start) > timedelta(hours=QUOTA_WINDOW_HOURS):
        used = 0
    limit = plan.get("daily_limit")
    remaining = None if limit is None else max(0, limit - used)
    resets_at = window_start + timedelta(hours=QUOTA_WINDOW_HOURS)
    return {
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "window_hours": QUOTA_WINDOW_HOURS,
        "resets_at": resets_at.isoformat(),
    }


def consume_quota(db: FirestoreClient, uid: str) -> tuple[bool, dict]:
    ref = _user_ref(db, uid)
    outcome: dict = {}

    @transactional
    def _tx(transaction):
        raw = transaction.get(ref)
        try:
            snap = next(iter(raw), None)
        except TypeError:
            snap = raw
        user = snap.to_dict() if snap is not None and snap.exists else {}
        now = _now()
        used = int(user.get("quota_used", 0))
        window_start = _to_dt(user.get("quota_window_start"))
        if window_start is None or (now - window_start) > timedelta(hours=QUOTA_WINDOW_HOURS):
            used = 0
            window_start = now

        slug = user.get("plan_slug") or FREE_PLAN_SLUG
        expires = _to_dt(user.get("plan_expires_at"))
        if expires is not None and expires < now:
            slug = FREE_PLAN_SLUG
        limit = (get_plan(db, slug) or PLANS_BY_SLUG[FREE_PLAN_SLUG]).get("daily_limit")

        base_quota = {
            "used": used,
            "limit": limit,
            "remaining": None if limit is None else max(0, limit - used),
            "window_hours": QUOTA_WINDOW_HOURS,
            "resets_at": (window_start + timedelta(hours=QUOTA_WINDOW_HOURS)).isoformat(),
        }

        if limit is not None and used >= limit:
            outcome["allowed"] = False
            outcome["quota"] = {**base_quota, "remaining": 0}
            return

        transaction.update(
            ref,
            {"quota_used": used + 1, "quota_window_start": window_start},
        )
        outcome["allowed"] = True
        outcome["quota"] = {
            **base_quota,
            "used": used + 1,
            "remaining": None if limit is None else limit - used - 1,
        }

    _tx(db.transaction())
    return outcome["allowed"], outcome["quota"]


def log_scan(db: FirestoreClient, uid: str, filename: str, format: str, score: int) -> None:
    db.collection("scan_events").add(
        {
            "uid": uid,
            "created_at": _now(),
            "filename": filename,
            "format": format,
            "score": score,
        }
    )
