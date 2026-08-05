from fastapi import APIRouter

from ..core import db
from ..schemas import PlanOut
from .deps import get_db

router = APIRouter()


@router.get("", response_model=list[PlanOut])
def list_plans():
    plans = db.list_plans(get_db())
    return [
        PlanOut(
            name=p["name"],
            slug=p["slug"],
            description=p.get("description"),
            daily_limit=p.get("daily_limit"),
            price_brl=p.get("price_brl", "0.00"),
            sort_order=p.get("sort_order", 0),
        )
        for p in plans
    ]
