import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..core import db
from ..core.config import PAYMENT_PROVIDER
from ..core.db import PLANS_BY_SLUG
from ..core.payments import get_payments
from .deps import get_db

logger = logging.getLogger("scandoc.webhook")

router = APIRouter()


class MercadoPagoEvent(BaseModel):
    type: str | None = None
    action: str | None = None
    data: dict | None = None


@router.post("/webhooks/mercadopago")
async def mercadopago_webhook(request: Request, event: MercadoPagoEvent, db_: Depends = get_db):
    if PAYMENT_PROVIDER != "mercadopago":
        return {"status": "ignored"}

    event_type = event.type or event.action
    data = event.data or {}
    resource_id = data.get("id") or data.get("preapproval_id") or data.get("subscription_id")
    if not event_type or not resource_id:
        return {"status": "invalid"}

    payments = get_payments()
    resolved = payments.resolve_webhook(event_type, str(resource_id))
    if not resolved:
        return {"status": "unresolved"}

    if resolved["status"] != "approved":
        logger.info(
            "Webhook %s ignorado (status=%s, resource=%s)",
            event_type,
            resolved["status"],
            resource_id,
        )
        return {"status": "not_approved"}

    plan = PLANS_BY_SLUG.get(resolved["plan_slug"])
    if plan is None or resolved["uid"] is None:
        return {"status": "invalid_plan"}

    db.activate_subscription(
        db_,
        resolved["uid"],
        plan,
        provider_subscription_id=resolved.get("preapproval_id"),
        provider="mercadopago",
    )
    logger.info("Assinatura ativada para %s (plano %s)", resolved["uid"], plan["slug"])
    return {"status": "activated"}
