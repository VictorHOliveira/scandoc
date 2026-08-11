import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request

from ..core import db
from ..core.config import PAYMENT_PROVIDER, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from ..core.db import PLANS_BY_SLUG
from .deps import get_db

logger = logging.getLogger("scandoc.webhook")

router = APIRouter()


def _to_dt(unix: int) -> datetime | None:
    if not unix:
        return None
    return datetime.utcfromtimestamp(int(unix))


def _to_dict(obj):
    return obj.to_dict() if hasattr(obj, "to_dict") else obj


def _resolve_period_end(stripe, subscription_id: str, fallback) -> datetime:
    if subscription_id:
        try:
            subscription = _to_dict(stripe.Subscription.retrieve(subscription_id))
            period_end = _to_dt(subscription.get("current_period_end"))
            if period_end:
                return period_end
        except Exception:
            logger.warning("Falha ao buscar subscription %s", subscription_id)
    return fallback


def _metadata(obj: dict) -> dict:
    return obj.get("metadata") or {}


def _user_from_metadata(metadata: dict):
    uid = metadata.get("uid")
    plan = PLANS_BY_SLUG.get(metadata.get("plan_slug"))
    return uid, plan


def _on_checkout_completed(db_, stripe, session) -> None:
    if session.get("mode") != "subscription":
        return
    if session.get("payment_status") not in ("paid", "no_payment_required"):
        return
    uid, plan = _user_from_metadata(_metadata(session))
    if not uid or plan is None:
        return
    subscription_id = session.get("subscription")
    period_end = _resolve_period_end(
        stripe,
        subscription_id,
        db._now() + timedelta(days=db.SUBSCRIPTION_DAYS),
    )
    db.activate_subscription_period(
        db_,
        uid,
        plan,
        period_end,
        provider_subscription_id=subscription_id,
        provider="stripe",
    )


def _on_invoice_paid(db_, stripe, invoice) -> None:
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return
    try:
        subscription = _to_dict(stripe.Subscription.retrieve(subscription_id))
    except Exception as exc:
        logger.error("Falha ao buscar subscription %s: %r", subscription_id, exc)
        return
    uid, plan = _user_from_metadata(_metadata(subscription))
    if not uid or plan is None:
        return
    period_end = _to_dt(subscription.get("current_period_end"))
    if period_end is None:
        return
    db.activate_subscription_period(
        db_,
        uid,
        plan,
        period_end,
        provider_subscription_id=subscription_id,
        provider="stripe",
    )


def _on_subscription_updated(db_, stripe, subscription) -> None:
    uid, plan = _user_from_metadata(_metadata(subscription))
    if not uid:
        return
    period_end = _to_dt(subscription.get("current_period_end"))
    status = subscription.get("status")
    cancel_at_period_end = bool(subscription.get("cancel_at_period_end"))
    if status == "canceled" or cancel_at_period_end:
        db.update_subscription_status(db_, uid, "cancelled", period_end=period_end)
    elif status == "active" and plan is not None and period_end is not None:
        db.activate_subscription_period(
            db_,
            uid,
            plan,
            period_end,
            provider_subscription_id=subscription.get("id"),
            provider="stripe",
        )
    else:
        db.update_subscription_status(db_, uid, status, period_end=period_end)


def _on_subscription_deleted(db_, stripe, subscription) -> None:
    uid, _ = _user_from_metadata(_metadata(subscription))
    if not uid:
        return
    period_end = _to_dt(subscription.get("current_period_end"))
    db.update_subscription_status(db_, uid, "cancelled", period_end=period_end)


_HANDLERS = {
    "checkout.session.completed": _on_checkout_completed,
    "invoice.paid": _on_invoice_paid,
    "customer.subscription.updated": _on_subscription_updated,
    "customer.subscription.deleted": _on_subscription_deleted,
}


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    if PAYMENT_PROVIDER != "stripe":
        return {"status": "ignored"}

    import stripe

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Header Stripe-Signature ausente")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Assinatura do webhook inválida")

    event = _to_dict(event)
    event_type = event.get("type")
    handler = _HANDLERS.get(event_type)
    if handler is None:
        return {"status": "ignored", "type": event_type}

    stripe.api_key = STRIPE_SECRET_KEY
    data = event.get("data", {}).get("object", {})
    handler(get_db(), stripe, data)
    logger.info("Webhook %s processado", event_type)
    return {"status": "ok"}
