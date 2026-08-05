from fastapi import APIRouter, Depends

from ..core import db
from ..schemas import MeOut, PlanOut, QuotaOut, UserOut
from .deps import get_current_user, get_db

router = APIRouter()


@router.get("/me", response_model=MeOut)
def me(user: dict = Depends(get_current_user)):
    fdb = get_db()
    plan = db.get_active_plan(fdb, user["uid"])
    return MeOut(
        user=UserOut(id=user["uid"], name=user.get("name") or "", email=user.get("email") or ""),
        plan=PlanOut(
            name=plan["name"],
            slug=plan["slug"],
            description=plan.get("description"),
            daily_limit=plan.get("daily_limit"),
            price_brl=plan.get("price_brl", "0.00"),
            sort_order=plan.get("sort_order", 0),
        ),
        quota=QuotaOut(**db.quota_status(fdb, user["uid"])),
    )
