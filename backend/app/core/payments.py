import logging

from .config import (
    APP_BASE_URL,
    MERCADOPAGO_ACCESS_TOKEN,
    MERCADOPAGO_WEBHOOK_URL,
    PAYMENT_PROVIDER,
)

logger = logging.getLogger("scandoc.payments")


class PaymentsError(RuntimeError):
    pass


class MockPayments:
    name = "mock"

    def create_checkout(self, *, uid: str, email: str, plan: dict) -> str:
        return f"{APP_BASE_URL}/planos?payment=mock-success"

    def resolve_webhook(self, event_type: str, resource_id: str) -> dict | None:
        return None

    def cancel_subscription(self, preapproval_id: str) -> None:
        return None


class MercadoPagoPayments:
    name = "mercadopago"

    def __init__(self, access_token: str):
        if not access_token:
            raise PaymentsError(
                "MERCADOPAGO_ACCESS_TOKEN não configurado (set PAYMENT_PROVIDER=mock para simular)"
            )
        try:
            import mercadopago
        except ImportError as exc:
            raise PaymentsError("Pacote 'mercadopago' não instalado") from exc
        self._sdk = mercadopago.SDK(access_token)

    def create_checkout(self, *, uid: str, email: str, plan: dict) -> str:
        body = {
            "reason": f"ScanDoc - {plan['name']}",
            "external_reference": f"{uid}:{plan['slug']}",
            "payer_email": email,
            "auto_recurring": {
                "frequency": 1,
                "frequency_type": "months",
                "transaction_amount": float(plan["price_brl"]),
                "currency_id": "BRL",
            },
            "back_url": f"{APP_BASE_URL}/conta",
            "return_url": f"{APP_BASE_URL}/planos?payment=success",
            "pending_url": f"{APP_BASE_URL}/planos?payment=pending",
        }
        if MERCADOPAGO_WEBHOOK_URL:
            body["notification_url"] = MERCADOPAGO_WEBHOOK_URL
        try:
            resp = self._sdk.preapproval().create(body)
        except Exception as exc:
            logger.error("Erro ao criar preapproval no Mercado Pago: %r", exc)
            raise PaymentsError("Não foi possível criar a assinatura no Mercado Pago") from exc
        if resp.get("status") not in (200, 201):
            logger.error("Mercado Pago rejeitou preapproval: %r", resp)
            raise PaymentsError("O Mercado Pago rejeitou a assinatura")
        response = resp.get("response") or {}
        init_point = response.get("init_point")
        if not init_point:
            raise PaymentsError("O Mercado Pago não retornou o link de pagamento")
        return init_point

    def resolve_webhook(self, event_type: str, resource_id: str) -> dict | None:
        try:
            if event_type == "payment":
                resp = self._sdk.payment().get(resource_id)
                data = resp.get("response") or {}
                uid_plan = str(data.get("external_reference") or "")
                return {
                    "uid": uid_plan.split(":", 1)[0],
                    "plan_slug": uid_plan.split(":", 1)[1] if ":" in uid_plan else None,
                    "status": data.get("status"),
                    "preapproval_id": data.get("preapproval_id"),
                }
            if event_type in ("subscription_preapproval", "preapproval"):
                resp = self._sdk.preapproval().get(resource_id)
                data = resp.get("response") or {}
                uid_plan = str(data.get("external_reference") or "")
                return {
                    "uid": uid_plan.split(":", 1)[0],
                    "plan_slug": uid_plan.split(":", 1)[1] if ":" in uid_plan else None,
                    "status": data.get("status"),
                    "preapproval_id": resource_id,
                }
        except Exception as exc:
            logger.error("Erro ao consultar recurso do Mercado Pago: %r", exc)
        return None

    def cancel_subscription(self, preapproval_id: str) -> None:
        if not preapproval_id:
            return
        try:
            self._sdk.preapproval().update(preapproval_id, {"status": "cancelled"})
        except Exception as exc:
            logger.error("Erro ao cancelar assinatura %s no Mercado Pago: %r", preapproval_id, exc)
            raise PaymentsError("Não foi possível cancelar a assinatura no Mercado Pago") from exc


def get_payments():
    if PAYMENT_PROVIDER != "mercadopago":
        return MockPayments()
    return MercadoPagoPayments(MERCADOPAGO_ACCESS_TOKEN)
