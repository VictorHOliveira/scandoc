from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta

from ..core import db
from ..core.config import PAYMENT_PROVIDER, PLAN_CHANGE_LOCK_DAYS
from ..core.db import PLANS_BY_SLUG
from ..core.payments import PaymentsError, get_payments
from ..schemas import CheckoutOut, PlanOut, SubscribeRequest, SubscriptionOut
from .deps import get_current_user, get_db

router = APIRouter()

MOCK = PAYMENT_PROVIDER == "mock"


@router.post("/subscribe")
def subscribe(body: SubscribeRequest, user: dict = Depends(get_current_user)):
    plan = PLANS_BY_SLUG.get(body.plan_slug)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    if plan["slug"] == "free":
        raise HTTPException(status_code=400, detail="O plano gratuito não requer assinatura")

    if not MOCK:
        raise HTTPException(
            status_code=400,
            detail="Use POST /api/subscribe/checkout para assinar pelo provedor de pagamento",
        )

    db.subscribe(get_db(), user["uid"], plan["slug"])

    return {
        "subscription": {
            "status": "active",
            "plan_slug": plan["slug"],
            "started_at": db._now().isoformat(),
        },
        "plan": PlanOut(
            name=plan["name"],
            slug=plan["slug"],
            description=plan.get("description"),
            daily_limit=plan.get("daily_limit"),
            price_brl=plan.get("price_brl", "0.00"),
            sort_order=plan.get("sort_order", 0),
        ),
    }


@router.post("/subscribe/checkout", response_model=CheckoutOut)
def create_checkout(body: SubscribeRequest, user: dict = Depends(get_current_user)):
    plan = PLANS_BY_SLUG.get(body.plan_slug)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    if plan["slug"] == "free":
        raise HTTPException(status_code=400, detail="O plano gratuito não requer assinatura")

    db_ = get_db()
    payments = get_payments()

    if payments.name == "stripe":
        subscription = db.get_subscription(db_, user["uid"]) or {}
        is_stripe_active = (
            subscription.get("provider") == "stripe"
            and subscription.get("status") == "active"
            and bool(subscription.get("preapproval_id"))
        )
        if is_stripe_active:
            current_plan = db.get_active_plan(db_, user["uid"])
            if current_plan["slug"] == plan["slug"]:
                raise HTTPException(status_code=400, detail="Você já está neste plano.")
            if plan["sort_order"] < current_plan["sort_order"]:
                _ensure_downgrade_allowed(db_, user["uid"])
            try:
                modified = payments.switch_subscription(
                    subscription["preapproval_id"], user["uid"], plan
                )
            except PaymentsError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            period_end = _period_end_from_stripe(modified)
            db.activate_subscription_period(
                db_,
                user["uid"],
                plan,
                period_end,
                provider_subscription_id=subscription["preapproval_id"],
                provider="stripe",
            )
            return CheckoutOut(checkout_url=None, switched=True)

    try:
        url = payments.create_checkout(
            uid=user["uid"], email=user.get("email", ""), plan=plan
        )
    except PaymentsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if payments.name == "mock":
        db.activate_subscription(db_, user["uid"], plan, provider="mock")
        return CheckoutOut(checkout_url=url, mock=True)

    return CheckoutOut(checkout_url=url, mock=False)


@router.get("/subscription", response_model=SubscriptionOut)
def get_subscription(user: dict = Depends(get_current_user)):
    db_ = get_db()
    plan = db.get_active_plan(db_, user["uid"])
    if plan is None or plan["slug"] == "free":
        return SubscriptionOut(active=False, plan_slug="free", status="none")

    subscription = db.get_subscription(db_, user["uid"])
    expires_at = _plan_expires_at(db_, user["uid"])
    status = (subscription or {}).get("status", "active")
    return SubscriptionOut(
        active=True,
        plan_slug=plan["slug"],
        status=status,
        period_end=expires_at.isoformat() if expires_at is not None else None,
    )


@router.post("/subscribe/cancel", response_model=SubscriptionOut)
def cancel_subscription(user: dict = Depends(get_current_user)):
    db_ = get_db()
    subscription = db.get_subscription(db_, user["uid"]) or {}
    if subscription.get("status") in ("cancelled", "expired"):
        plan = db.get_active_plan(db_, user["uid"])
        return SubscriptionOut(
            active=bool(plan and plan["slug"] != "free"),
            plan_slug=(plan or {}).get("slug", "free"),
            status="cancelled",
            period_end=_period_end_iso(db_, user["uid"]),
        )

    payments = get_payments()
    preapproval_id = subscription.get("preapproval_id")
    try:
        if preapproval_id:
            payments.cancel_subscription(preapproval_id)
    except PaymentsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.cancel_subscription(db_, user["uid"], provider=payments.name)

    plan = db.get_active_plan(db_, user["uid"])
    return SubscriptionOut(
        active=bool(plan and plan["slug"] != "free"),
        plan_slug=(plan or {}).get("slug", "free"),
        status="cancelled",
        period_end=_period_end_iso(db_, user["uid"]),
    )


def _plan_expires_at(db_, uid: str):
    user = db.get_user(db_, uid) or {}
    return db._to_dt(user.get("plan_expires_at"))


def _period_end_from_stripe(subscription) -> datetime:
    raw = getattr(subscription, "current_period_end", None)
    if raw is None and isinstance(subscription, dict):
        raw = subscription.get("current_period_end")
    return datetime.utcfromtimestamp(int(raw)) if raw else db._now() + timedelta(days=db.SUBSCRIPTION_DAYS)


def _period_end_iso(db_, uid: str) -> str | None:
    dt = _plan_expires_at(db_, uid)
    return dt.isoformat() if dt is not None else None


def _ensure_downgrade_allowed(db_, uid: str) -> None:
    user = db.get_user(db_, uid) or {}
    changed_at = db._to_dt(user.get("plan_changed_at"))
    if changed_at is None:
        return
    locked_until = changed_at + timedelta(days=PLAN_CHANGE_LOCK_DAYS)
    if db._now() < locked_until:
        raise HTTPException(
            status_code=400,
            detail=(
                "Você trocou de plano em "
                f"{changed_at.strftime('%d/%m/%Y')}. Poderá reduzir o plano "
                f"a partir de {locked_until.strftime('%d/%m/%Y')}."
            ),
        )
