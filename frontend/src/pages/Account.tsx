import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { cancelSubscription, getSubscription, type SubscriptionInfo } from "../api";

function parseIso(iso: string): Date {
  if (!/[zZ]$|[+-]\d\d:\d\d$/.test(iso)) iso += "Z";
  return new Date(iso);
}

function formatDate(iso: string): string {
  return parseIso(iso).toLocaleDateString("pt-BR");
}

export default function Account() {
  const { me, refresh } = useAuth();
  const [sub, setSub] = useState<SubscriptionInfo | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getSubscription().then(setSub).catch(() => setSub(null));
  }, [me?.plan.slug]);

  if (!me) return null;

  const { user, plan, quota } = me;
  const unlimited = quota.limit === null;

  const onCancel = async () => {
    if (!window.confirm("Tem certeza que deseja cancelar a assinatura? Você mantém o acesso até o fim do período pago.")) {
      return;
    }
    setCancelling(true);
    setMessage("");
    try {
      const updated = await cancelSubscription();
      setSub(updated);
      setMessage("Assinatura cancelada. Você mantém o acesso até o fim do período pago.");
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erro ao cancelar assinatura");
    } finally {
      setCancelling(false);
    }
  };

  const paidPlan = sub?.active && plan.slug !== "free";

  return (
    <div className="account-page">
      <h2>Minha conta</h2>
      <div className="card account-card">
        <p>
          <strong>Nome:</strong> {user.name}
        </p>
        <p>
          <strong>E-mail:</strong> {user.email}
        </p>
      </div>

      <h3>Plano atual</h3>
      <div className="card account-card">
        <div className="account-plan-row">
          <div>
            <p className="plan-name">
              {plan.name}
              {plan.slug === "free" && <span className="badge badge-soft">gratuito</span>}
            </p>
            {plan.description && <p className="muted">{plan.description}</p>}
            {paidPlan && sub?.period_end && (
              <p className="muted">
                {sub.status === "cancelled" ? (
                  <>Assinatura cancelada — ativa até {formatDate(sub.period_end)} (sem renovação).</>
                ) : (
                  <>Assinatura mensal ativa até {formatDate(sub.period_end)}.</>
                )}
              </p>
            )}
          </div>
          <Link to="/planos" className="btn btn-primary">
            Trocar de plano
          </Link>
        </div>
        {paidPlan && sub?.status !== "cancelled" && (
          <button
            className="btn btn-danger"
            disabled={cancelling}
            onClick={onCancel}
          >
            {cancelling ? "Cancelando..." : "Cancelar assinatura"}
          </button>
        )}
      </div>

      {message && <p className="success-box">{message}</p>}

      <h3>Cota de análises (janela de {quota.window_hours}h)</h3>
      <div className="card account-card">
        <div className="quota-row">
          <div className="quota-num">
            <span className="quota-used">{quota.used}</span>
            <span className="quota-sep">/</span>
            <span className="quota-limit">{unlimited ? "∞" : quota.limit}</span>
          </div>
          <div className="quota-bar">
            <div
              className="quota-fill"
              style={{
                width: unlimited
                  ? "0%"
                  : `${Math.min(100, (quota.used / Math.max(1, quota.limit!)) * 100)}%`,
              }}
            />
          </div>
        </div>
        {unlimited ? (
          <p className="muted">Plano ilimitado — analise quantos documentos quiser.</p>
        ) : (
          <p className="muted">
            {quota.remaining} análise(s) restante(s). Cota renova em {formatDate(quota.resets_at)}.
          </p>
        )}
      </div>
    </div>
  );
}
