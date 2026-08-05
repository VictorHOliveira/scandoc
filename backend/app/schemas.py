from typing import Literal

from pydantic import BaseModel

Severity = Literal["info", "low", "medium", "high", "critical"]


class Finding(BaseModel):
    severity: Severity
    kind: str
    title: str
    description: str
    location: str | None = None
    snippet: str | None = None
    bbox: list[float] | None = None


class ScanResult(BaseModel):
    filename: str
    format: str
    score: int
    findings: list[Finding]
    hidden_text: str
    annotated_image: str | None = None
    injection_matches: list[str]
    summary: dict


class UserOut(BaseModel):
    id: str
    name: str
    email: str


class PlanOut(BaseModel):
    name: str
    slug: str
    description: str | None = None
    daily_limit: int | None = None
    price_brl: str
    sort_order: int = 0


class QuotaOut(BaseModel):
    used: int
    limit: int | None = None
    remaining: int | None = None
    window_hours: int
    resets_at: str


class MeOut(BaseModel):
    user: UserOut
    plan: PlanOut
    quota: QuotaOut


class SubscribeRequest(BaseModel):
    plan_slug: str
