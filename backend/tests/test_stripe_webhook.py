import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.core.payments import StripePayments
from tests.fake_firestore import FakeFirestore

fake = FakeFirestore()
IDENTITY = {"uid": "uid-stripe", "email": "stripe@test.com", "name": "Stripe Test"}


@pytest.fixture(scope="module")
def client():
    patchers = [
        patch("app.core.firebase.verify_token", return_value=IDENTITY),
        patch("app.core.db.get_firestore", return_value=fake),
        patch("app.main.firebase.init_firebase", return_value=None),
        patch("app.api.webhook_routes.PAYMENT_PROVIDER", "stripe"),
        patch("app.api.webhook_routes.STRIPE_WEBHOOK_SECRET", "whsec_test"),
        patch("app.api.webhook_routes.STRIPE_SECRET_KEY", "sk_test"),
    ]
    for p in patchers:
        p.start()
    fake._store.clear()
    db.seed_plans(fake)

    from app.main import app

    with TestClient(app) as c:
        yield c

    for p in patchers:
        p.stop()


def _future_ts(days=35) -> int:
    return int(time.time()) + days * 86400


def _event(event_type: str, obj: dict) -> dict:
    return {"type": event_type, "data": {"object": obj}}


def _post(client, event):
    with patch("stripe.Webhook.construct_event", return_value=event):
        return client.post(
            "/api/webhooks/stripe",
            json=event,
            headers={"Stripe-Signature": "t=1,v1=whatever"},
        )


def _seed_user(uid: str = "uid-stripe", plan_slug: str = "free") -> None:
    fake._store[("users", uid)] = {
        "uid": uid,
        "email": "stripe@test.com",
        "name": "Stripe Test",
        "plan_slug": plan_slug,
        "plan_expires_at": None,
        "subscription_id": None,
    }


def test_stripe_webhook_ignored_when_provider_not_stripe(client):
    with patch("app.api.webhook_routes.PAYMENT_PROVIDER", "mock"):
        r = client.post(
            "/api/webhooks/stripe",
            json={"type": "x"},
            headers={"Stripe-Signature": "sig"},
        )
    assert r.status_code == 200
    assert r.json() == {"status": "ignored"}


def test_stripe_webhook_rejects_bad_signature(client):
    with patch(
        "stripe.Webhook.construct_event",
        side_effect=ValueError("bad signature"),
    ):
        r = client.post(
            "/api/webhooks/stripe",
            json={"type": "x"},
            headers={"Stripe-Signature": "t=1,v1=bad"},
        )
    assert r.status_code == 400


def test_checkout_session_completed_activates_subscription(client):
    _seed_user()
    session = {
        "mode": "subscription",
        "payment_status": "paid",
        "metadata": {"uid": "uid-stripe", "plan_slug": "profissional"},
        "subscription": None,
    }
    r = _post(client, _event("checkout.session.completed", session))
    assert r.status_code == 200, r.text
    assert r.json() == {"status": "ok"}

    user = fake._store[("users", "uid-stripe")]
    assert user["plan_slug"] == "profissional"
    assert user["plan_expires_at"] is not None

    sub = fake._store[("subscriptions", "uid-stripe")]
    assert sub["provider"] == "stripe"
    assert sub["status"] == "active"
    assert sub["plan_slug"] == "profissional"


def test_checkout_session_completed_ignored_when_unpaid(client):
    _seed_user()
    session = {
        "mode": "subscription",
        "payment_status": "unpaid",
        "metadata": {"uid": "uid-stripe", "plan_slug": "profissional"},
    }
    r = _post(client, _event("checkout.session.completed", session))
    assert r.status_code == 200
    user = fake._store[("users", "uid-stripe")]
    assert user["plan_slug"] == "free"


def test_invoice_paid_renews_period(client):
    _seed_user(plan_slug="avancado")
    future_ts = _future_ts(65)
    subscription_obj = {
        "metadata": {"uid": "uid-stripe", "plan_slug": "avancado"},
        "current_period_end": future_ts,
    }
    invoice = {"subscription": "sub_123"}
    with patch("stripe.Subscription.retrieve", return_value=subscription_obj):
        r = _post(client, _event("invoice.paid", invoice))
    assert r.status_code == 200

    user = fake._store[("users", "uid-stripe")]
    assert user["plan_slug"] == "avancado"
    assert user["plan_expires_at"] == datetime.utcfromtimestamp(future_ts)

    sub = fake._store[("subscriptions", "uid-stripe")]
    assert sub["status"] == "active"
    assert sub["preapproval_id"] == "sub_123"


def test_subscription_updated_cancel_at_period_end_marks_cancelled(client):
    _seed_user(plan_slug="basico")
    future_ts = _future_ts(20)
    subscription_obj = {
        "metadata": {"uid": "uid-stripe"},
        "status": "active",
        "cancel_at_period_end": True,
        "current_period_end": future_ts,
    }
    r = _post(client, _event("customer.subscription.updated", subscription_obj))
    assert r.status_code == 200

    user = fake._store[("users", "uid-stripe")]
    assert user["plan_slug"] == "basico"
    assert user["plan_expires_at"] == datetime.utcfromtimestamp(future_ts)

    sub = fake._store[("subscriptions", "uid-stripe")]
    assert sub["status"] == "cancelled"


def test_subscription_updated_switch_changes_plan(client):
    _seed_user(plan_slug="basico")
    future_ts = _future_ts(20)
    subscription_obj = {
        "metadata": {"uid": "uid-stripe", "plan_slug": "ilimitado"},
        "status": "active",
        "cancel_at_period_end": False,
        "current_period_end": future_ts,
        "id": "sub_1",
    }
    r = _post(client, _event("customer.subscription.updated", subscription_obj))
    assert r.status_code == 200

    user = fake._store[("users", "uid-stripe")]
    assert user["plan_slug"] == "ilimitado"
    assert user["plan_expires_at"] == datetime.utcfromtimestamp(future_ts)

    sub = fake._store[("subscriptions", "uid-stripe")]
    assert sub["status"] == "active"
    assert sub["preapproval_id"] == "sub_1"


class _FakeStripeItem:
    id = "si_1"


class _FakeStripeItems:
    data = [_FakeStripeItem()]


class _FakeStripeSubscription:
    items = _FakeStripeItems()


def test_stripe_switch_subscription_changes_price_and_metadata():
    plan = db.PLANS_BY_SLUG["avancado"]
    modified = {"id": "sub_1", "current_period_end": 12345}
    calls = {}

    def _retrieve(sid):
        return _FakeStripeSubscription()

    def _modify(sid, **kwargs):
        calls.update(kwargs)
        return modified

    fake_prices = {
        "basico": "price_basico",
        "profissional": "price_prof",
        "avancado": "price_avancado",
        "ilimitado": "price_ilimitado",
    }
    with patch("stripe.Subscription.retrieve", side_effect=_retrieve), patch(
        "stripe.Subscription.modify", side_effect=_modify
    ), patch("app.core.payments.STRIPE_PRICES", fake_prices):
        payments = StripePayments("sk_test_xyz")
        result = payments.switch_subscription("sub_1", "uid-a", plan)

    assert result == modified
    assert calls["items"] == [{"id": "si_1", "price": "price_avancado"}]
    assert calls["metadata"] == {"uid": "uid-a", "plan_slug": "avancado"}
    assert calls["cancel_at_period_end"] is False


class _FakeSwitchPayments:
    name = "stripe"
    switch_calls = None
    switch_result = None

    def switch_subscription(self, subscription_id, uid, plan):
        self.switch_calls = (subscription_id, uid, plan)
        return self.switch_result


def test_checkout_switches_existing_subscription(client):
    fake._store[("users", "uid-stripe")] = {
        "uid": "uid-stripe",
        "email": "stripe@test.com",
        "name": "Stripe Test",
        "plan_slug": "basico",
        "plan_expires_at": None,
        "subscription_id": "sub_1",
    }
    fake._store[("subscriptions", "uid-stripe")] = {
        "uid": "uid-stripe",
        "provider": "stripe",
        "status": "active",
        "preapproval_id": "sub_1",
        "plan_slug": "basico",
        "period_end": None,
        "updated_at": None,
    }

    future_ts = _future_ts(40)
    payments = _FakeSwitchPayments()
    payments.switch_result = {"current_period_end": future_ts}

    with patch("app.api.payment_routes.get_payments", return_value=payments):
        r = client.post(
            "/api/subscribe/checkout",
            headers={"Authorization": "Bearer fake-token"},
            json={"plan_slug": "ilimitado"},
        )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["switched"] is True
    assert payments.switch_calls == (
        "sub_1",
        "uid-stripe",
        db.PLANS_BY_SLUG["ilimitado"],
    )

    user = fake._store[("users", "uid-stripe")]
    assert user["plan_slug"] == "ilimitado"
    assert user["plan_expires_at"] == datetime.utcfromtimestamp(future_ts)

    sub = fake._store[("subscriptions", "uid-stripe")]
    assert sub["status"] == "active"
    assert sub["preapproval_id"] == "sub_1"


def test_checkout_switch_rejects_same_plan(client):
    fake._store[("users", "uid-stripe")] = {
        "uid": "uid-stripe",
        "email": "stripe@test.com",
        "name": "Stripe Test",
        "plan_slug": "basico",
        "plan_expires_at": datetime.utcnow() + timedelta(days=40),
        "subscription_id": "sub_1",
    }
    fake._store[("subscriptions", "uid-stripe")] = {
        "uid": "uid-stripe",
        "provider": "stripe",
        "status": "active",
        "preapproval_id": "sub_1",
        "plan_slug": "basico",
        "period_end": None,
        "updated_at": None,
    }

    payments = _FakeSwitchPayments()
    with patch("app.api.payment_routes.get_payments", return_value=payments):
        r = client.post(
            "/api/subscribe/checkout",
            headers={"Authorization": "Bearer fake-token"},
            json={"plan_slug": "basico"},
        )

    assert r.status_code == 400
    assert payments.switch_calls is None


def test_subscription_deleted_marks_cancelled(client):
    _seed_user(plan_slug="ilimitado")
    future_ts = _future_ts(10)
    subscription_obj = {
        "metadata": {"uid": "uid-stripe"},
        "current_period_end": future_ts,
    }
    r = _post(client, _event("customer.subscription.deleted", subscription_obj))
    assert r.status_code == 200

    sub = fake._store[("subscriptions", "uid-stripe")]
    assert sub["status"] == "cancelled"


def test_unknown_event_ignored(client):
    r = _post(client, _event("charge.succeeded", {"id": "ch_1"}))
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


class _FakeSession:
    def __init__(self, url):
        self._url = url

    def to_dict(self):
        return {"url": self._url}


def test_stripe_checkout_creates_session():
    plan = db.PLANS_BY_SLUG["profissional"]
    captured = {}

    def _create(**kwargs):
        captured.update(kwargs)
        return _FakeSession("https://checkout.stripe.com/c/pay/test")

    fake_prices = {
        "basico": "price_basico",
        "profissional": "price_prof",
        "avancado": "price_avancado",
        "ilimitado": "price_ilimitado",
    }
    with patch("stripe.checkout.Session.create", side_effect=_create), patch(
        "app.core.payments.STRIPE_PRICES", fake_prices
    ):
        payments = StripePayments("sk_test_xyz")
        url = payments.create_checkout(uid="uid-a", email="a@b.com", plan=plan)

    assert url == "https://checkout.stripe.com/c/pay/test"
    assert captured["mode"] == "subscription"
    assert captured["client_reference_id"] == "uid-a"
    assert captured["customer_email"] == "a@b.com"
    assert captured["line_items"] == [{"price": "price_prof", "quantity": 1}]
    assert captured["metadata"] == {"uid": "uid-a", "plan_slug": "profissional"}
    assert captured["subscription_data"]["metadata"] == {
        "uid": "uid-a",
        "plan_slug": "profissional",
    }
    assert captured["managed_payments"] == {"enabled": False}
    assert captured["success_url"].endswith("/planos?payment=success")
