import logging

from .config import (
    APP_BASE_URL,
    STRIPE_PRICE_AVANCADO,
    STRIPE_PRICE_BASICO,
    STRIPE_PRICE_ILIMITADO,
    STRIPE_PRICE_PROFISSIONAL,
    STRIPE_SECRET_KEY,
    PAYMENT_PROVIDER,
)

logger = logging.getLogger("scandoc.payments")


class PaymentsError(RuntimeError):
    pass


STRIPE_PRICES = {
    "basico": STRIPE_PRICE_BASICO,
    "profissional": STRIPE_PRICE_PROFISSIONAL,
    "avancado": STRIPE_PRICE_AVANCADO,
    "ilimitado": STRIPE_PRICE_ILIMITADO,
}


class MockPayments:
    name = "mock"

    def create_checkout(self, *, uid: str, email: str, plan: dict) -> str:
        return f"{APP_BASE_URL}/planos?payment=mock-success"

    def cancel_subscription(self, subscription_id: str) -> None:
        return None


class StripePayments:
    name = "stripe"

    def __init__(self, api_key: str):
        if not api_key:
            raise PaymentsError(
                "STRIPE_SECRET_KEY não configurado (set PAYMENT_PROVIDER=mock para simular)"
            )
        try:
            import stripe
        except ImportError as exc:
            raise PaymentsError("Pacote 'stripe' não instalado") from exc
        self._stripe = stripe
        self._stripe.api_key = api_key

    def _price_id(self, plan_slug: str) -> str:
        price_id = STRIPE_PRICES.get(plan_slug)
        if not price_id:
            raise PaymentsError(f"Preço Stripe não configurado para o plano '{plan_slug}'")
        return price_id

    def create_checkout(self, *, uid: str, email: str, plan: dict) -> str:
        try:
            session = self._stripe.checkout.Session.create(
                mode="subscription",
                client_reference_id=uid,
                customer_email=email,
                line_items=[{"price": self._price_id(plan["slug"]), "quantity": 1}],
                metadata={"uid": uid, "plan_slug": plan["slug"]},
                subscription_data={
                    "metadata": {"uid": uid, "plan_slug": plan["slug"]}
                },
                managed_payments={"enabled": False},
                success_url=f"{APP_BASE_URL}/planos?payment=success",
                cancel_url=f"{APP_BASE_URL}/planos",
            )
        except PaymentsError:
            raise
        except Exception as exc:
            logger.error("Erro ao criar Checkout Session no Stripe: %r", exc)
            raise PaymentsError("Não foi possível iniciar o pagamento no Stripe") from exc
        session = session.to_dict()
        if not session.get("url"):
            raise PaymentsError("O Stripe não retornou o link de checkout")
        return session["url"]

    def cancel_subscription(self, subscription_id: str) -> None:
        if not subscription_id:
            return
        try:
            self._stripe.Subscription.modify(
                subscription_id, cancel_at_period_end=True
            )
        except Exception as exc:
            logger.error(
                "Erro ao cancelar assinatura %s no Stripe: %r", subscription_id, exc
            )
            raise PaymentsError("Não foi possível cancelar a assinatura no Stripe") from exc

    def switch_subscription(self, subscription_id: str, uid: str, plan: dict):
        if not subscription_id:
            raise PaymentsError("Assinatura Stripe não encontrada para a troca de plano")
        try:
            current = self._stripe.Subscription.retrieve(subscription_id)
            items = (current.get("items") or {}).get("data") or []
            if not items:
                raise PaymentsError(
                    "Assinatura sem itens; cancele e assine novamente o plano desejado"
                )
            return self._stripe.Subscription.modify(
                subscription_id,
                items=[{"id": items[0]["id"], "price": self._price_id(plan["slug"])}],
                metadata={"uid": uid, "plan_slug": plan["slug"]},
                cancel_at_period_end=False,
            )
        except PaymentsError:
            raise
        except Exception as exc:
            logger.error(
                "Erro ao trocar de plano na assinatura %s: %r", subscription_id, exc
            )
            raise PaymentsError("Não foi possível trocar de plano no Stripe") from exc


def get_payments():
    if PAYMENT_PROVIDER != "stripe":
        return MockPayments()
    return StripePayments(STRIPE_SECRET_KEY)
