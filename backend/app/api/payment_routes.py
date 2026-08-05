from fastapi import APIRouter, Depends, HTTPException

from ..core import db
from ..core.db import PLANS_BY_SLUG
from ..schemas import PlanOut, SubscribeRequest
from .deps import get_current_user, get_db

router = APIRouter()


@router.post("/subscribe")
def subscribe(body: SubscribeRequest, user: dict = Depends(get_current_user)):
    plan = PLANS_BY_SLUG.get(body.plan_slug)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    if plan["slug"] == "free":
        raise HTTPException(status_code=400, detail="O plano gratuito não requer assinatura")

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
